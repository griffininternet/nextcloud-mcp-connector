# Pitfalls Research

**Domain:** Eine zweite, fremde Host-Identität (OpenProject in openDesk) und ein Audit-Log über jeden Tool-Aufruf an eine ausgelieferte MCP-only-ExApp anbauen (v1.5 "Vorlauf openDesk")
**Researched:** 2026-08-28
**Confidence:** HIGH für die OpenProject-API-Form und die Nextcloud-Logging-Defaults (offizielle Doku, Context7 über /websites/openproject), HIGH für die openDesk-Versionsmatrix (releases.opendesk.eu, v1.18.0 vom 19.08.2026), HIGH für den Code-Stand dieses Repos (direkt gelesen), MEDIUM für die Workspaces-Abkündigung und die pageSize-Obergrenze (Doku-Seiten, nicht gegen eine Instanz gemessen), MEDIUM für alles, was den ZenDiS-Aufnahmeprozess betrifft (öffentlich nicht dokumentiert, das ist selbst der Befund), MEDIUM für die rechtlichen Einordnungen (Recherche, keine Rechtsberatung)

Diese Datei ersetzt die v1.2-Pitfall-Recherche. Sie ist gegen den Code nach Release 0.1.10 geschrieben:
`oauth/store.py`, `config.py` (`persistent_storage`), `exapp/purge.py`, `exapp/occ.py`,
`exapp/config_values.py`, `scripts/check_tool_budget.py` (`BUDGET_BYTES = 18_000`),
`docs/privacy.md` und der Enterprise-Absatz in `README.md:512` sowie in `appinfo/info.xml` (EN
Zeile 77, DE 122, FR 169). Jedes "Wie vermeiden" nennt die Stelle, an die die Änderung gehört,
weil ein Pitfall ohne Adresse eine Warnung ist und kein Plan.

## Die Ein-Absatz-Fassung

OpenProject ist nicht die zehnte Nextcloud-App, sondern der erste Host, dem unser Nutzer fremd
ist. Das Kernversprechen dieses Projekts, "der Assistent sieht nie mehr als der angemeldete
Nutzer", ist heute dadurch gedeckt, dass jeder Aufruf mit einem Nextcloud-App-Passwort genau
dieses Nutzers läuft. Gegen OpenProject gibt es dieses Passwort nicht, und der einzige
Maschinen-zu-Maschine-Weg, den OpenProject anbietet, ist Client Credentials mit einem fest
konfigurierten Impersonationsnutzer: also genau der Durchgriff, den wir ausgeschlossen haben.
Der saubere Weg (OIDC-Token-Exchange über Keycloak) hängt an einem Nextcloud-Feature, das
`user_oidc#925` bis heute als offene Anfrage führt. Parallel dazu: openDesk ist eine Kubernetes-
Distribution mit gepinnten Komponenten (v1.18.0: Nextcloud 33.0.7, OpenProject 17.7.2, Nubus
Keycloak 26.7.0), und unsere Ein-Klick-Story ist auf Nextcloud 34.0.3 gemessen. Die Frage, ob
eine ExApp dort überhaupt installierbar ist, entscheidet vor jeder API-Frage. Das Audit-Log
wiederum ist der Baustein, der leicht aussieht und in der Praxis an fünf Stellen kippt: es wird
zur zweiten Kopie genau der Daten, die es überwachen soll, es füllt dasselbe Volume, auf dem der
OAuth-Store liegt, es ist einer Person nicht zurechenbar, der Administrator bekommt es nie zu
Gesicht (Nextcloud verschluckt INFO-Meldungen per Default, siehe `admin_audit`), und in dem
Moment, in dem etwas Halbfertiges "Audit-Log" heißt, wird ein heute wahrer Satz in drei Sprachen
im Store falsch.

## Critical Pitfalls

### Pitfall 1: OpenProject kennt unseren Nutzer nicht, und die naheliegende Abhilfe bricht das Kernversprechen

**What goes wrong:**
Heute funktioniert der Berechtigungsdurchgriff strukturell: AppAPI nennt uns die Nutzer-Id, wir
holen aus dem SQLite-Store das verschlüsselte App-Passwort dieser Autorisierung, und Nextcloud
selbst entscheidet, was der Nutzer sehen darf. Wir müssen nichts filtern, weil wir nichts
filtern können. Gegen OpenProject existiert dieser Mechanismus nicht. Was OpenProject anbietet:

| Weg | Wie er sich anfühlt | Was er wirklich tut |
|-----|---------------------|---------------------|
| API-Key als Bearer (`opapi-...`) oder Basic `apikey:KEY` | schnell, im Spike in fünf Minuten grün | ein persönlicher Schlüssel pro Nutzer, den jeder Nutzer selbst erzeugen und uns geben müsste: ein zweites App-Passwort-Gebastel, also genau das, wogegen dieses Projekt in der Store-Beschreibung antritt |
| OAuth 2.0 Authorization Code (mit PKCE) | spec-konform, passt zu unserem Selbstbild | erfordert einen zweiten Consent-Durchlauf pro Nutzer gegen einen zweiten Host, eine zweite Client-Registrierung, einen zweiten Refresh-Zyklus und ein zweites Widerrufskonzept im Store und in der `/connections`-Seite |
| OAuth 2.0 Client Credentials | "der Server holt sich einen Token, fertig" | OpenProject bindet Client Credentials an einen konfigurierten "Client credentials user". Jede Anfrage läuft im Namen dieses einen Nutzers, unabhängig davon, wer gefragt hat |
| OIDC-Token-Exchange über Keycloak (RFC 8693) | in openDesk architektonisch richtig | setzt voraus, dass Nextcloud der ExApp ein Nutzer-Token des IdP aushändigt. `nextcloud/user_oidc#925` ist genau diese Anfrage und steht offen |

Die dritte Zeile ist die Falle. Sie ist der einzige Weg, der im Spike sofort funktioniert, und
sie ist zugleich der einzige Weg, der den Satz "der Assistent sieht niemals mehr als der
angemeldete Nutzer" unwahr macht: mit einem Impersonationsnutzer, der in mehreren Projekten
Mitglied ist, sieht jeder Anfragende dessen Sicht. In einer Behörde ist das kein Schönheitsfehler,
sondern der Grund, warum das Produkt abgelehnt wird.

Erschwerend: OpenProject rendert Berechtigungen als **Anwesenheit von Links** in der HAL-Antwort
(siehe Pitfall 4). Ein Impersonationsnutzer mit vielen Rechten liefert also nicht nur mehr Daten,
sondern auch mehr Handlungsangebote, und ein Modell, das `_links` liest, sieht Aktionen, die der
echte Fragende nie hätte.

**Why it happens:**
Der Spike ist zeitboxiert, Client Credentials sind zwei curl-Zeilen, und die Antwort sieht
richtig aus. Der Unterschied zwischen "die API antwortet" und "die API antwortet als der
richtige Mensch" ist in einer Einzelnutzer-Testinstanz unsichtbar, exakt wie bei den Talk-Read-
Markern in v1.2.

**How to avoid:**
Die Identitätsfrage ist das **Ergebnis** des Spikes, nicht sein Nebenprodukt. Konkret:

1. Der Spike beantwortet zuerst schriftlich: Woher kommt das Nutzer-Token für OpenProject, und
   wie widerruft es der Nutzer? Erst danach wird eine Zeile Client-Code geschrieben.
2. Client Credentials wird als Weg **ausgeschlossen und die Ausschlussbegründung in PROJECT.md
   unter Key Decisions notiert**, bevor jemand versucht ist, damit eine Demo zu bauen. Wenn er
   für einen Machbarkeitsbeweis benutzt wird, dann in einem wegwerfbaren Skript unter
   `scripts/`, nie in `src/`, und der Spike-Report sagt in seinem ersten Absatz, dass die Messung
   nicht als der Fragende lief.
3. Der Token-Exchange-Pfad wird als **Frage an den ISV-Call** formuliert, nicht als Annahme:
   "Stellt openDesk beziehungsweise Nubus einen Weg bereit, mit dem eine Nextcloud-ExApp ein
   auf `api_v3` beschränktes Token für OpenProject im Namen des angemeldeten Nutzers erhält?"
   Diese eine Frage ist mehr wert als der halbe Rest der Fragenliste, weil sie entscheidet, ob
   v2.0 überhaupt gebaut werden kann.
4. Falls die Antwort "nein" lautet, ist der zweite Consent-Durchlauf (Authorization Code gegen
   OpenProject, PKCE, eigener Widerruf auf `/connections`) der einzig vertretbare Fallback, und
   sein Aufwand gehört in die v2.0-Schätzung, nicht in v1.5.

**Warning signs:**
Ein `OPENPROJECT_API_KEY` oder `client_secret` in einer `.env`, einer Compose-Datei oder einem
Test. Ein Spike-Ergebnis, das die Frage "als wem?" nicht in einem Satz beantwortet. Eine Notiz,
die "funktioniert" sagt, ohne den Nutzernamen zu nennen, unter dem gemessen wurde.

**Phase to address:**
openDesk-Spike, als erste und wichtigste Erfolgsbedingung. Formuliert als Messung: "Der Spike-
Report benennt genau einen tragfähigen Weg zur Nutzeridentität gegen OpenProject, oder er
benennt begründet keinen."

---

### Pitfall 2: Die K.-o.-Frage ist nicht die API, sondern ob eine ExApp in openDesk überhaupt installierbar ist

**What goes wrong:**
Der ganze Meilenstein zielt auf die API-Machbarkeit und übersieht die Ebene darunter. openDesk
ist laut eigener Architekturdokumentation "designed as a Kubernetes deployment", ein Satz Helm-
Charts, orchestriert per Helmfile. Unsere ExApp braucht einen AppAPI-Deploy-Daemon. Für
Produktion unterstützt AppAPI im Kern den Docker-Weg (`docker-install`, per Docker Socket Proxy
oder HaRP); `manual-install` ist laut Nextcloud-Doku ausdrücklich für Entwicklung oder
Spezialfälle. In einem Kubernetes-Cluster, in dem der Betreiber neun Anwendungen betreibt und der
Nextcloud-Container aus einem gepinnten Chart kommt, ist "installiere per Klick aus dem App
Store" nicht die Nutzererfahrung, es sei denn, der Betreiber hat vorher einen Deploy-Daemon
bereitgestellt und die openDesk-Werte dafür geöffnet.

Wenn das nicht geht oder nur mit Betreiberaufwand geht, ist der Kern-Differenzierer dieses
Projekts (Zugänglichkeit, ein Klick) in genau der Zielumgebung wertlos, und zwar unabhängig
davon, wie sauber der OpenProject-Client wird. Ein Spike, der das nicht klärt, hat die teure
Frage nicht angefasst.

**Why it happens:**
"openDesk enthält Nextcloud" liest sich wie "unsere App läuft dort". Die Distribution bestimmt
aber, welche Nextcloud-Apps aktiv sind und wie der Container aussieht, und die Store-Installation
ist ein Vorgang, den ein Betreiber in einer gehärteten Verwaltungsumgebung nicht beiläufig
zulässt.

**How to avoid:**
Der Spike stellt diese Frage **vor** der API-Frage und beantwortet sie aus zwei Quellen: dem
openDesk-Deployment-Repository auf openCode (`bmi/opendesk/deployment/opendesk`, dort die
Nextcloud-Werte und die App-Liste) und dem ISV-Call. Formuliere sie so, dass sie mit Ja oder Nein
beantwortbar ist:

- Läuft in openDesk ein AppAPI-Deploy-Daemon, und wenn ja, welcher Typ?
- Gibt es eine Allowlist für Nextcloud-Apps in den Helm-Werten, und wer entscheidet über
  Aufnahme?
- Wenn nein: Ist eine ExApp als eigenes Deployment neben der Suite (HaRP, entfernter Host) ein
  akzeptierter Betriebsweg, oder ist das für einen Betreiber ein Ausschlusskriterium?

Der Spike-Report führt diese drei Antworten ganz oben, weil sie die Reihenfolge von v2.0
bestimmen. Wenn die Antwort "nur als Teil der Distribution" lautet, dann ist der ZenDiS-Kanal
kein Vertriebsweg, sondern die einzige Tür, und der Meilenstein danach heißt nicht "OpenProject-
Werkzeuge", sondern "Aufnahmefähigkeit herstellen".

**Warning signs:**
Ein Spike-Report, der nur über `api/v3` spricht. Eine Roadmap-Phase "OpenProject-Tools", der
keine Phase "Installierbarkeit" vorausgeht. Die Annahme, der Store-Knopf sei überall derselbe
Knopf.

**Phase to address:**
openDesk-Spike, Teil 1, vor jeder API-Untersuchung. Erfolgsbedingung: drei Ja-Nein-Antworten,
jede mit Quelle oder mit dem Vermerk "offen, im ISV-Call zu klären".

---

### Pitfall 3: Der Spike gegen eine Instanz, die man nicht hat, misst das Falsche oder gar nichts

**What goes wrong:**
Zwei entgegengesetzte Fehler, beide teuer.

*Der erste:* gar nicht spiken, sondern lesen, und den Doku-Auszug als Machbarkeitsbeweis buchen.
Genau diese Lehre steht bereits in der Projektakte: "ein als behoben gebuchter Review-Befund ohne
nachgefahrenen Beleg ist schlimmer als ein offener." Für OpenProject gibt es dafür keine
Entschuldigung: eine vollständige Instanz mit Seed-Daten steht mit einem Docker-Compose-Stack in
Minuten, und `OPENPROJECT_HTTPS=false` ist die einzige Klippe beim ersten Start.

*Der zweite, gefährlichere:* gegen eine frische Vanilla-OpenProject-Instanz spiken und das
Ergebnis für openDesk halten. Was eine lokale Instanz **nicht** reproduziert:

- Keycloak als Identitätsanbieter und damit die gesamte Identitätsfrage aus Pitfall 1. Lokal
  gibt es einen Admin mit API-Key, und alles ist grün.
- Die Pflicht, dass ein JWT eines OIDC-Providers einen Scope trägt: das kam als
  ausdrücklicher Breaking Change mit OpenProject 16.0.0 und ist im lokalen API-Key-Modus
  unsichtbar.
- Die gepinnte Version. openDesk v1.18.0 (19.08.2026) fährt OpenProject 17.7.2; wer lokal
  `openproject/openproject:latest` zieht, misst potenziell eine andere Generation, und in
  OpenProject 17 sind projektbezogene Endpunkte zugunsten von Workspaces abgekündigt (Pitfall 4).
- Die Datenlage. Seed-Daten haben ein Projekt, fünf Arbeitspakete und keine Rechteverteilung.
  Alle Berechtigungs- und Paginierungsfallen sind dort unsichtbar, exakt wie die Talk-Read-Marker
  auf einer Einnutzer-Instanz unsichtbar waren.
- Die vorkonfigurierte Nextcloud-OpenProject-Kopplung. In openDesk existiert `integration_openproject`
  bereits mit eigenem Zwei-Wege-OAuth2 zwischen den beiden Hosts. Ein Spike, der davon nichts
  weiß, erfindet einen Weg, den die Distribution schon hat, oder kollidiert mit ihm.

**Why it happens:**
Ein Spike ohne Instanz fühlt sich unseriös an, also baut man schnell eine, und dann gilt
stillschweigend, was diese Instanz zeigt. Der Unterschied zwischen "OpenProject" und "OpenProject
in openDesk" ist eine Umgebungsfrage und wird deshalb nicht als technische Frage wahrgenommen.

**How to avoid:**
Den Spike von vornherein in zwei getrennte Ergebnisspalten schreiben, und die Trennung im Bericht
sichtbar halten:

| Spalte | Wie belegt | Beispiele |
|--------|-----------|-----------|
| Lokal gemessen | Docker-Compose-Instanz, Version notiert | HAL-Form, Filter-Syntax, Paginierung, Fehlercodes, Antwortgrößen, Feldprojektion |
| Nur im Ziel prüfbar | Frage an den ISV-Call, ausdrücklich als offen markiert | Identität und Token-Herkunft, Scope-Pflicht, Deploy-Daemon, gepinnte Versionen, Zulassung |

Dazu drei Regeln: die lokale Instanz wird auf die openDesk-Version gepinnt (heute 17.7.x), nicht
auf `latest`. Es werden mindestens zwei Nutzer mit unterschiedlichen Projektrollen angelegt, weil
sonst die Berechtigungsfragen nicht gestellt werden können. Und die Zeitbox ist eine Zeitbox: der
Spike endet mit einem Bericht und einer Fragenliste, nicht mit einem Client-Modul. Was
Produktionscode werden soll, wird in v2.0 neu geschrieben, nachdem die Identitätsfrage beantwortet
ist.

**Warning signs:**
Ein Spike, der ohne Versionsangabe berichtet. `latest` in einer Compose-Datei. Ein Spike-Zweig,
der Dateien unter `src/mcp_connector/nextcloud/clients/` anlegt. Ein Bericht ohne Abschnitt
"nicht gemessen, weil keine openDesk-Instanz vorhanden".

**Phase to address:**
openDesk-Spike, als Rahmenregel der Phase. Erfolgsbedingung: der Bericht trennt Gemessenes von
Angenommenem und nennt für jedes Angenommene die Frage, die es klären würde.

---

### Pitfall 4: Die OpenProject-API hat vier Formfallen, und jede davon kostet einen Nachmittag

**What goes wrong:**
Die API ist gut dokumentiert und trotzdem ungewohnt, weil sie an vier Stellen anders funktioniert
als jede Nextcloud-API, gegen die dieses Projekt bisher gebaut hat.

1. **HAL+JSON statt Nutzdaten.** Antworten kommen als `application/hal+json`. Eine Sammlung ist
   `{_type: "Collection", count, offset, pageSize, total, _embedded: {elements: [...]}, _links: {...}}`.
   Die Nutzdaten liegen also zwei Ebenen tief, und jedes Element trägt einen `_links`-Block, der
   den Löwenanteil der Bytes ausmacht. Wer eine solche Antwort ungefiltert durch ein MCP-Tool
   reicht, verbrennt das Antwortbudget an Hyperlinks. Verwandte Objekte (Projekt, Bearbeiter,
   Status) stehen nur als `href` mit `title`; wer den `title` nicht nutzt, baut sich ein N+1-
   Problem pro Arbeitspaket.
2. **Filter sind URL-kodiertes JSON.** Ein Filter ist ein Array von Objekten der Form
   `[{"status":{"operator":"=","values":["5"]}}]`, das als ein einziger Query-Parameter
   übergeben wird. Zwei Konsequenzen: die Operatoren sind eigene Zeichen (`=`, `!`, `**`, `o`
   für offen, `~` und andere) und keine Vergleichsoperatoren im üblichen Sinn, und der
   Standardfilter der Arbeitspaket-Endpunkte ist bereits gesetzt
   (`[{"status_id":{"operator":"o","values":null}}]`, also nur offene). Wer keinen Filter mitgibt,
   bekommt nicht "alles", sondern "offene", und wundert sich, dass ein erledigtes Paket nicht
   auffindbar ist. Für lange Filter existiert zusätzlich `eprops` (komprimiert und kodiert), was
   die Fehlersuche im Log unmöglich macht, wenn man es benutzt.
3. **Berechtigungen sind kontextabhängig gerendert, und 404 heißt nicht "gibt es nicht".** Die
   Doku ist an dieser Stelle ausdrücklich: nur Aktionen, die der authentifizierte Nutzer ausführen
   darf, werden als Link gerendert, und ein Client ohne ausreichende Rechte "shall not be able to
   test for the existence of a project", also antwortet OpenProject mit 404 statt 403. Unsere
   heutige 404-Erklärung ("suche zuerst danach, die Id ist dieser Instanz unbekannt") ist damit
   in genau dem Fall falsch, der am häufigsten vorkommt: fehlende Projektmitgliedschaft. Das ist
   dieselbe Klasse wie das Mail-404 aus v1.2 ("not logged in"), und sie schickt das Modell in
   eine Suchschleife.
4. **Paginierung ist Offset-Paginierung mit Seitenzahlen.** `offset` ist die Seitennummer
   (Standard 1), `pageSize` die Seitengröße (Standard 20, dokumentierte Obergrenze 1000, von der
   Instanz über die Seitengrößen-Optionen beschränkbar). Unser `paging.py` gibt Handles heraus;
   eine Offset-Seite ist ohne stabile Sortierung nicht stabil, das heißt: ohne explizites `sortBy`
   (etwa `[["id","asc"]]`) kann dasselbe Objekt auf zwei Seiten oder auf keiner erscheinen, wenn
   sich zwischendurch etwas ändert.

Dazu zwei Versionsfallen, beide MEDIUM-Konfidenz aus den Release-Notes und Endpunktseiten: seit
OpenProject **16.0.0** müssen API-Anfragen mit einem JWT eines OIDC-Providers einen Scope tragen
(`api_v3`), und seit OpenProject **17** sind projektbezogene Endpunkte wie
`/api/v3/projects/{id}/work_packages` zugunsten von `/api/v3/workspaces/{id}/work_packages`
abgekündigt. Beides trifft genau die Version, die openDesk fährt.

**Why it happens:**
Jede dieser vier Formen ist für sich harmlos und in der Doku beschrieben. Zusammen ergeben sie
eine API, die sich nur dann korrekt anfühlt, wenn man sie einmal ganz gelesen hat, und die im
Happy Path einer Seed-Instanz vollständig funktioniert.

**How to avoid:**
Als Spike-Ergebnis, nicht als Code: ein Abschnitt im Bericht pro Punkt, mit einer gemessenen
Beispielantwort und ihrer Bytegröße vor und nach Projektion. Konkret zu notieren:

- die Feldliste, die ein `work_package` in einer MCP-Antwort tragen soll (Vorschlag: `id`,
  `subject`, `_links.status.title`, `_links.type.title`, `_links.assignee.title`,
  `_links.project.title`, `startDate`, `dueDate`, `updatedAt`, und sonst nichts), plus die
  gemessene Ersparnis. Das ist dieselbe Schema-Diät, die das Projekt schon zweimal gerettet hat.
- die Erkenntnis, dass ein 404 zwei Bedeutungen hat, mit dem Formulierungsvorschlag für den Hint.
- die Entscheidung, immer explizit zu filtern, immer explizit zu sortieren, immer explizit
  `pageSize` zu setzen (das ist wörtlich die Tables-Lehre aus v1.2), und `eprops` nicht zu
  benutzen.
- die Version, gegen die gemessen wurde, und die Frage, ob die Workspaces-Endpunkte in 17.7 schon
  die zu nutzenden sind.

Für v2.0 gilt dann die Regel aus `notes.py`: eine gepinnte API-Generation pro Client, hier
`api/v3`, plus ein Kompatibilitätsvermerk zur Workspaces-Umstellung.

**Warning signs:**
Eine Beispielantwort im Bericht, die `_links` vollständig enthält. Eine Anfrage ohne `pageSize`.
Ein Filterbeispiel, das nicht URL-kodiert ist (funktioniert per curl oft trotzdem und in Python
dann nicht). Ein Bericht, der 404 als "nicht gefunden" übersetzt.

**Phase to address:**
openDesk-Spike, Teil 2 (API-Form). Die daraus folgenden Client-Regeln gehören in v2.0, nicht in
diesen Meilenstein.

---

### Pitfall 5: Das Audit-Log wird zur zweiten Kopie genau der Daten, die es schützen sollte

**What goes wrong:**
"Audit-Log über jeden Tool-Aufruf" wird als "logge den Aufruf" gelesen, und ein Aufruf besteht
aus Argumenten und einer Antwort. Wer beides schreibt, hat mit einem Commit die sorgfältigste
Aussage dieses Projekts kassiert. `docs/privacy.md` sagt heute wörtlich:

> Die App speichert nicht den Inhalt Ihrer Dateien, Kalender, Notizen, Deck-Karten oder Kontakte.
> Sie liest sie pro Anfrage, unter der Identität des Nutzers, und gibt sie in der Werkzeugantwort
> zurück. Nichts davon wird in die Datenbank geschrieben.

Ein Audit-Log mit Argumenten enthält Suchbegriffe, Dateipfade, Konversationstoken, Mail-Ids und
Betreffzeilen. Ein Audit-Log mit Antworten enthält Mailtexte und Chatnachrichten. Damit entsteht
im Container ein persistenter, unverschlüsselter Bestand an genau den Daten, für die die Architektur
bisher garantiert, dass sie nur durchfließen. Nebeneffekte, alle real:

- Der Purge-Pfad (`occ mcp_connector:purge --force`) leert heute die OAuth-Tabellen. Ein Audit-Log
  im selben Store würde entweder mitgelöscht (dann ist es als Audit wertlos, siehe Pitfall 9)
  oder nicht (dann behauptet `privacy.md` Löschung, die nicht stattfindet). Beides ist falsch, und
  die Entscheidung muss bewusst getroffen und dokumentiert werden.
- Ein Auskunftsersuchen nach DSGVO Art. 15 bezieht sich dann auf Inhalte, nicht nur auf
  Verbindungsdaten. Das ist für einen Solo-Betreiber eine neue Klasse von Pflicht.
- Die Verschlüsselung des Stores schützt heute App-Passwörter, weil der Schlüssel in Nextclouds
  App-Konfiguration liegt. Audit-Zeilen im Klartext daneben zu legen, macht die Sorgfalt an der
  einen Stelle zur Kulisse.

**Why it happens:**
Weil "vollständig" wie das Qualitätskriterium eines Audit-Logs klingt und weil die Argumente beim
Schreiben des Loggers ohnehin in der Hand liegen. Der Unterschied zwischen "was wurde getan" und
"was wurde gesehen" ist genau die Grenze, die hier verläuft, und sie ist nicht offensichtlich.

**How to avoid:**
Eine Regel, ausnahmslos, im Logger und nicht in den Tool-Funktionen: **das Audit-Log speichert
Metadaten eines Aufrufs, niemals Nutzinhalte.** Konkret als Zeilenschema:

| Feld | Beispiel | Warum erlaubt |
|------|----------|---------------|
| Zeitpunkt (UTC, ISO 8601) | `2026-09-01T08:14:22Z` | Ereignisdatum |
| Nutzer-Id | `alice` | Zurechenbarkeit (Pitfall 7) |
| Client | `Claude.ai`, plus Client-Id-Hash | Zurechenbarkeit |
| Werkzeugname | `mail_read` | das "was" |
| Ergebnisklasse | `ok`, `denied`, `degraded`, `error` | das "mit welchem Ausgang" |
| Argument-**Namen**, nicht -Werte | `["account_id","message_id"]` | zeigt die Form ohne den Inhalt |
| Trefferanzahl und Antwortgröße in Bytes | `12`, `4831` | erlaubt Auffälligkeitserkennung ohne Inhalt |
| Korrelations-Id | ein Zufallswert pro Aufruf | verbindet mit dem Anwendungslog, wenn jemand debuggen muss |

Was ausdrücklich nicht hineingehört: Suchbegriffe, Pfade, Betreffzeilen, Nachrichtentexte,
Konversationstoken im Klartext, Mail-Adressen. Wo eine Kennung nötig ist, gehört ein über einen
instanzlokalen Schlüssel gebildeter HMAC hinein, kein Klartext: das erlaubt "derselbe Gegenstand
wie gestern", ohne den Gegenstand zu benennen.

Diese Regel wird wie das AST-Grep-Gate durchgesetzt und nicht durch Disziplin: ein Contract-Test,
der die Audit-Schreibstelle parst und fehlschlägt, sobald ein Wert aus dem Argument-Mapping oder
aus dem Antwortobjekt in die Zeile fließt. Dazu ein Vokabular-Gate-artiger Test über eine
Beispielzeile mit einer bekannten Kanarienzeichenkette in Argumenten und Antwort: die Zeichenkette
darf in der erzeugten Audit-Zeile nicht vorkommen.

**Warning signs:**
Ein Logger, der `**kwargs` oder das Antwortobjekt entgegennimmt. Ein Audit-Feld namens `query`,
`args`, `payload` oder `result`. Eine Diskussion, die mit "für die Fehlersuche wäre es hilfreich,
wenn" beginnt. Jede Änderung, die `privacy.md` Abschnitt "What the app stores" berührt.

**Phase to address:**
Audit-Log-Fundament, als erste Designentscheidung, vor der ersten Schreibstelle. Erfolgsbedingung:
Kanarientest grün, `privacy.md` in derselben Phase geändert.

---

### Pitfall 6: Unbegrenztes Wachstum im Container reißt den OAuth-Store mit

**What goes wrong:**
Das Audit-Log landet naheliegenderweise dort, wo schon Zustand liegt: im Volume unter
`APP_PERSISTENT_STORAGE` (`nc_app_mcp_connector_data`), also neben der SQLite-Datei, in der jede
Autorisierung, jedes verschlüsselte App-Passwort und jeder Token-Hash steht. Dieses Volume hat
keine Quote, keine Rotation und keinen Aufräumer. Ein Audit-Log ohne Grenze führt deshalb nicht zu
"das Log ist groß", sondern zu **"das Volume ist voll"**, und dann:

- SQLite kann im WAL-Modus nicht mehr schreiben. Jede Token-Rotation scheitert. Jede aktive
  Verbindung bricht ab.
- Der Healthcheck des Containers antwortet eventuell weiter mit 200, weil der Prozess lebt.
- Es gibt keinen Weg für den Nutzer, sich neu zu verbinden, weil das Schreiben der neuen
  Autorisierung dasselbe volle Volume trifft.
- Die Wiederherstellung erfordert einen Administrator mit Shell-Zugriff auf den Docker-Host,
  was in einer Kubernetes-Distribution wie openDesk nicht der Support-Weg ist, den ein Betreiber
  hören möchte.

Ein Aufruf pro Tool, ein Nutzer, ein Agentenlauf mit fünfzig Aufrufen: das sind schnell hunderte
Zeilen pro Nutzer und Tag. Bei fünfzig Nutzern und einer 300-Byte-Zeile sind das in der
Größenordnung von einem halben Gigabyte pro Jahr, und niemand hat je darüber nachgedacht.
Nextcloud selbst zeigt beide Enden des Problems: `log_rotate_size` steht per Default auf 100 MB,
und die Doku sagt ausdrücklich, dass eine bereits vorhandene rotierte Datei **überschrieben** wird.
Es gibt also genau eine Rotationsgeneration. Wer sein Audit dorthin schreibt, hat kein
Wachstumsproblem, aber ein Verlustproblem.

**Why it happens:**
Weil das Wachstum eines Logs bei der Entwicklung mit drei Testaufrufen unsichtbar ist und weil das
Volume, wenn es einmal angelegt ist, wie unendlicher Platz aussieht.

**How to avoid:**
Drei Entscheidungen, alle vor der ersten Zeile Code, alle in einer Phase:

1. **Obergrenze im Schema.** Wenn das Log in SQLite geht: eine Tabelle mit fester Zeilenobergrenze
   und einem Trigger oder einem Schreibpfad, der beim Einfügen die ältesten Zeilen über der
   Grenze löscht (Ringpuffer), plus eine Aufbewahrungsfrist in Tagen, die ein Admin setzen kann.
   Beide Grenzen greifen, die kleinere gewinnt. Der Default wird gemessen und begründet, in
   derselben Disziplin wie `BUDGET_BYTES = 18_000`.
2. **Eine Zahl im Betrieb sichtbar machen.** Der bestehende Status-Endpunkt der ExApp meldet die
   Zeilenzahl, die Dateigröße und das Alter der ältesten Zeile. Ohne diese drei Zahlen merkt es
   niemand, bis es zu spät ist.
3. **Der Weg nach draußen ist der Regelfall, der Weg im Volume die Ausnahme.** Wenn das Log
   ohnehin in den Nextcloud-Log geht (Pitfall 8), ist der lokale Bestand nur ein Puffer und darf
   klein sein.

Ein Ringpuffer widerspricht der Audit-Idee: genau deshalb muss das eine bewusst dokumentierte
Aussage sein ("die App hält die letzten N Ereignisse beziehungsweise die letzten D Tage; wer mehr
braucht, leitet weiter"), und nicht eine stille Eigenschaft, die ein Auditor entdeckt.

**Warning signs:**
Kein `DELETE`- oder `LIMIT`-Pfad im Audit-Code. Keine Größenangabe im Status. Eine Aufbewahrungs-
frage, die "später" beantwortet werden soll. Ein Test, der zehn Zeilen schreibt und aufhört.

**Phase to address:**
Audit-Log-Fundament, zusammen mit dem Schema. Erfolgsbedingung: ein Test schreibt über die Grenze
hinaus und beweist, dass die Datei nicht wächst und der OAuth-Store unberührt bleibt.

---

### Pitfall 7: Zeilen, die man keiner Person zuordnen kann, und die Zuordnung, die man nicht darf

**What goes wrong:**
Ein Audit-Log soll "wer hat was wann getan" beantworten. In dieser Architektur ist jeder Teil
davon zweideutig, wenn man nicht aufpasst:

- **Die Quell-IP ist wertlos.** Alle Anfragen der ExApp an Nextcloud kommen aus einem Container,
  also aus einer IP, für alle Nutzer der Installation. Das ist bereits als Brute-Force-Falle
  bekannt (v1.2, Pitfall 10) und gilt für die Zurechenbarkeit genauso.
- **"Der Nutzer" ist mehrdeutig.** Es gibt den Nextcloud-Nutzer, den OAuth-Client (Claude.ai,
  ChatGPT, Claude Code), die konkrete Autorisierung und, ab v2.0, eventuell eine zweite Identität
  auf dem fremden Host. Eine Zeile, die nur `alice` sagt, beantwortet nicht, ob Alice selbst
  getippt hat oder ihr Agent nachts eine Schleife lief.
- **Nutzer-Ids sind wiederverwendbar.** Ein gelöschter Nextcloud-Nutzer, dessen Id neu vergeben
  wird, macht alte Zeilen falsch zuordenbar.
- **Die Uhr im Container ist nicht die Uhr des Auditors.** Ohne UTC und ohne Zeitzonenangabe ist
  eine Korrelation mit dem Nextcloud-Log Handarbeit mit Fehlerpotenzial.
- **Und die Gegenrichtung:** eine Zeile, die zu genau zuordnet, wird zum Verhaltensprotokoll
  (siehe Pitfall 11). "Vollständig zurechenbar" und "datensparsam" ziehen gegeneinander, und die
  Auflösung ist eine Entscheidung, keine Technik.

**Why it happens:**
Weil der Logger dort geschrieben wird, wo die Nutzer-Id gerade zur Hand ist, und weil "eine Id ist
eine Id" wirkt, bis jemand eine Zeile erklären muss.

**How to avoid:**
Die Zeile trägt vier Identitätsfelder statt einem, und jedes hat eine benannte Bedeutung:

1. `nc_user`: die Nextcloud-Nutzer-Id, exakt der Wert, unter dem der Aufruf lief. Das ist die
   einzige Angabe, mit der ein Administrator in seinem eigenen System weiterarbeiten kann.
2. `authorization_id`: die Id der Autorisierung aus dem Store. Sie überlebt eine Umbenennung und
   trennt zwei Assistenten desselben Nutzers.
3. `client`: der registrierte Client-Name, plus Client-Id. Der Name ist selbstgewählt und deshalb
   nicht vertrauenswürdig, die Id ist es.
4. `mode`: `exapp`, `http_passthrough`, `stdio` oder `http_static_bearer`, weil in drei dieser
   vier Modi die Nutzeridentität aus einer anderen Quelle stammt und eine Zeile ohne diese Angabe
   nicht interpretierbar ist.

Dazu: Zeitstempel immer UTC in ISO 8601 mit `Z`, nie lokal. Eine monoton steigende laufende Nummer
pro Zeile, damit Lücken auffallen (das ist die billigste Form von Vollständigkeitsnachweis, siehe
Pitfall 9). Und ein ausdrücklicher Satz in der Doku, was das Log **nicht** beantwortet, zum
Beispiel: es unterscheidet nicht, ob der Mensch oder sein Agent den Aufruf ausgelöst hat, weil das
Protokoll diese Unterscheidung nicht trägt.

**Warning signs:**
Eine Audit-Zeile mit genau einem Identitätsfeld. Ein lokaler Zeitstempel. Ein Test, der die Zeile
prüft, ohne den Modus zu variieren. Ein Support-Fall, der mit "aber wer war das?" endet.

**Phase to address:**
Audit-Log-Fundament, im Zeilenschema. Erfolgsbedingung: für jeden der vier Credential-Modi
existiert ein Test, der zeigt, welche Identitätsangaben in der Zeile stehen und welche notwendig
leer sind.

---

### Pitfall 8: Ein Log, das der Administrator nie zu Gesicht bekommt

**What goes wrong:**
Ein Audit-Log in einem Docker-Volume eines Containers, den der Administrator über AppAPI gestartet
hat, ist praktisch unsichtbar. Der Weg dorthin lautet: Host finden, Volume finden, `docker exec`
oder Volume mounten, SQLite-Client installieren, SQL schreiben. Das tut niemand, und in einer
Kubernetes-Distribution kann es der Betreiber unter Umständen gar nicht.

Der offensichtliche Ausweg ist der AppAPI-Log-Endpunkt: eine ExApp kann per
`POST /ocs/v2.php/apps/app_api/api/v1/log` mit `{"level": <PSR-3 0..7>, "message": "..."}` in den
Nextcloud-Log schreiben, und der Eintrag wird automatisch mit der ExApp-Id versehen. Genau dort
liegt die nächste Falle, und Nextcloud liefert den Präzedenzfall gleich mit:

- Der System-Loglevel steht per Default auf **2 (Warning)**. Die eingebaute `admin_audit`-App
  schreibt auf **Info**, und die Nextcloud-Dokumentation sagt ausdrücklich, dass diese Meldungen
  deshalb unterdrückt werden, solange der Administrator den Level nicht senkt oder eine
  Ausnahme konfiguriert. Ein Audit-Log auf Info-Level ist auf einer Standardinstallation ein Log,
  das es nicht gibt.
- Auf Warning zu schreiben, um das zu umgehen, vergiftet den Log des Administrators: hunderte
  Warnungen täglich für Vorgänge, die keine sind, und im Ergebnis stellt er die App leiser oder
  ab. AppAPI protokolliert außerdem jede impersonierte Anfrage bereits auf Warning-Level nach
  `data/exapp_impersonation.log`, das Fan-out existiert also schon.
- Ein Eintrag ist eine **Zeichenkette**, kein strukturierter Datensatz. Wer ein SIEM füttern will,
  braucht JSON in dieser Zeichenkette und muss das ausdrücklich so bauen.
- Jeder Eintrag ist ein zusätzlicher OCS-Roundtrip zu Nextcloud, pro Werkzeugaufruf. Bei
  `prepare_context` mit vier Beinen ist das die Frage, ob ein Aufruf oder fünf protokolliert
  werden, und die Antwort entscheidet über Latenz und Logvolumen gleichermaßen.

**Why it happens:**
Weil "es wird geloggt" und "es ist lesbar" für dieselbe Aussage gehalten werden, und weil der
Default-Loglevel eine Eigenschaft der fremden Installation ist, die auf der eigenen Testinstanz
gerne auf Debug steht.

**How to avoid:**
Die Ausgabe ist ein eigenes Thema mit eigener Entscheidung, nicht ein Anhängsel des Schreibens:

1. **Zwei Ziele, ein Schema.** Der lokale Bestand (durchsuchbar, begrenzt, Pitfall 6) und der
   Nextcloud-Log (der Ort, an dem der Administrator ohnehin nachsieht) tragen dieselbe Zeile.
   Der Nextcloud-Weg ist das, was den Administrator erreicht; der lokale Weg ist das, was eine
   Abfrage erlaubt.
2. **Level als Admin-Einstellung, mit einem begründeten Default.** Der Schalter reiht sich in die
   bestehenden deklarativen Admin-Einstellungen ein, genau wie `NC_MCP_TALK_SEND` und der CIMD-
   Schalter. Drei Stellungen genügen: aus, Nextcloud-Log auf Notice/Info, Nextcloud-Log auf
   Warning. Der Hilfetext nennt die Loglevel-Falle in einem Satz, weil sonst jeder Support-Fall
   damit beginnt.
3. **Eine Zeile pro Werkzeugaufruf, nicht pro HTTP-Anfrage nach draußen.** `prepare_context` ist
   ein Aufruf. Die Beine erscheinen als Zählung in der Zeile, nicht als eigene Zeilen.
4. **Ein Abfrageweg, der ohne Shell auskommt.** Am billigsten: ein authentifizierter Endpunkt der
   ExApp, der die letzten N Zeilen als JSON liefert, hinter Administratorenprüfung, plus ein
   Export als NDJSON. Ohne diesen Weg ist der lokale Bestand Dekoration.
5. **Der Schreibweg darf nie den Werkzeugaufruf blockieren.** Ein Nextcloud-Log-Roundtrip, der
   hängt, darf nicht die Antwort verzögern: eigenes Zeitbudget, Fehler wird zu einer stillen
   Zählung, nicht zu einem Werkzeugfehler. Das ist dieselbe Regel, die `tools/context.py` für die
   Beine des Bundles bereits durchhält.

Achtung an einer Stelle: wenn der Schreibweg fehlschlagen darf, ist das Log nicht mehr
vollständig. Das ist vertretbar, muss aber gesagt werden (Pitfall 9), und die Anzahl verlorener
Zeilen gehört in den Status.

**Warning signs:**
Ein Audit-Feature ohne Leseweg. Eine Testanleitung, die mit `docker exec` beginnt. Ein Default,
der auf Info schreibt, ohne dass irgendwo der Satz über den Default-Loglevel steht. Eine Messung
der Werkzeuglatenz, die vor der Audit-Einführung und danach nicht verglichen wurde.

**Phase to address:**
Audit-Log-Ausgabe, als eigene Phase nach dem Fundament. Erfolgsbedingung: auf einer Instanz mit
unverändertem Default-Loglevel erscheint eine Audit-Zeile dort, wo der Administrator sie erwartet,
und der Beweis ist ein Auszug aus dem Nextcloud-Log, kein Screenshot der eigenen Datenbank.

---

### Pitfall 9: "Audit-Log" nennen, was ein Anwendungslog ist

**What goes wrong:**
Das Wort ist der Anspruch. Wer "Audit-Log" schreibt, verspricht einem Prüfer etwas, und der Prüfer
in dieser Zielgruppe arbeitet gegen BSI IT-Grundschutz OPS.1.1.5, gegen ISO 27001 und gegen die
Datenschutzaufsicht. Was dort erwartet wird und was ein Anwendungslog typischerweise nicht liefert:

| Erwartung | Woher | Was unser Erstwurf typischerweise tut |
|-----------|-------|----------------------------------------|
| Der Administrator darf Protokolldaten nicht ändern oder löschen können | OPS.1.1.5 | Der Administrator hat Shell auf dem Host und damit auf die SQLite-Datei. Trennung existiert nicht |
| Vollständigkeit ist nachweisbar, Lücken fallen auf | Prüfpraxis | Eine Zeile, die beim Schreibfehler verloren geht, hinterlässt keine Spur |
| Manipulation ist erkennbar | OPS.1.1.5 (Signatur), Stand der Technik (Hash-Kette) | Eine gewöhnliche Tabelle ohne Verkettung |
| Aufbewahrung und Löschfrist sind festgelegt und begründet | Datenschutzrecht | Unbegrenzt, oder ein Ringpuffer ohne Begründung |
| Der Zweck ist festgelegt und die Nutzung daran gebunden | Zweckbindung | Nicht dokumentiert |
| Der Nachweis ist ohne den Hersteller führbar | Prüfpraxis | Nur über ein Feature, das derselbe Hersteller geschrieben hat |

Die härteste Zeile ist die erste. In der Betriebsform dieses Produkts ist der Administrator
zugleich der, der das Log lesen soll, und der, der es löschen könnte. Ein Audit-Log, das die
Handlungen von Nutzern gegenüber diesem Administrator dokumentiert, ist dadurch nicht wertlos.
Ein Audit-Log, das Handlungen **des Administrators** dokumentieren soll, ist es sehr wohl, und
genau das versteht ein Prüfer meist unter dem Wort.

Die Folge, wenn das nicht sauber getrennt ist: Bei der ersten ernsthaften Prüfung wird das
Feature abgelehnt, und die Ablehnung fällt nicht nur auf das Feature zurück, sondern auf die
übrigen Aussagen des Produkts, die alle nachweislich belegt sind.

**Why it happens:**
Weil "Audit-Log" die geläufige Bezeichnung für "wir schreiben auf, wer was gemacht hat" ist und
weil in der Enterprise-Zeile des Store-Textes exakt dieses Wort steht.

**How to avoid:**
Zwei Wege, und eine bewusste Wahl zwischen ihnen. Meine Empfehlung ist der erste.

1. **Den Anspruch auf das senken, was gehalten wird, und die Grenze aussprechen.** Das Feature
   heißt dann etwa "Zugriffsprotokoll" beziehungsweise "access log for tool calls", die
   Dokumentation nennt in drei Sätzen, was es leistet (jeder Werkzeugaufruf, mit Nutzer, Client,
   Zeit, Ausgang), und was es nicht leistet (kein Manipulationsschutz gegenüber dem
   Instanzadministrator, keine Inhalte, begrenzte Aufbewahrung, Weiterleitung an ein SIEM ist der
   vorgesehene Weg zu Revisionssicherheit). Dieser ehrliche Zuschnitt ist verkäuflich: er sagt
   dem Betreiber genau, wo sein eigenes SIEM anschließt.
2. **Den Anspruch halten.** Dann braucht es mindestens: eine Hash-Kette über die Zeilen (jede
   Zeile trägt den Hash der vorigen), eine laufende Nummer, einen periodisch signierten oder
   nach außen weitergegebenen Kettenkopf, und einen Prüfbefehl, der die Kette verifiziert. Das
   ist machbar und in wenigen hundert Zeilen zu haben, aber es ist ein eigenes Vorhaben mit
   eigenen Tests, und es löst das Administratorproblem nur zusammen mit einer externen Ablage.

Was in beiden Fällen gilt: die laufende Nummer und die Zählung verworfener Zeilen kosten fast
nichts und sind der Unterschied zwischen "wir wissen nicht, ob etwas fehlt" und "wir sehen, dass
etwas fehlt". Die nehmen wir mit, egal welcher Weg gewählt wird.

**Warning signs:**
Das Wort "revisionssicher", "tamper-proof" oder "manipulationssicher" in irgendeinem Text, ohne
dass eine Kette existiert. Eine Feature-Beschreibung, die keinen "was es nicht leistet"-Absatz
hat. Die Erwartung, dass ein Prüfer das Wort so versteht, wie es gemeint war.

**Phase to address:**
Meilenstein-Design, vor dem Fundament: die Wahl zwischen Weg 1 und Weg 2 bestimmt Schema, Aufwand
und Text. Die Grenzbeschreibung selbst gehört in die Doku-Phase, dreisprachig.

---

### Pitfall 10: Ein halbfertiges Audit-Log macht drei wahre Sätze im Store falsch

**What goes wrong:**
Der Enterprise-Absatz steht heute wortgleich an vier Stellen: `README.md:512` sowie
`appinfo/info.xml` in EN (Zeile 77), DE (122) und FR (169). Er lautet sinngemäß: "Audit-Log,
Gruppen-Policies und SSO über Ihren Identitätsanbieter sind als kommerzielles Add-on für
Organisationen **geplant**." PROJECT.md hält dazu ausdrücklich fest, dass diese Dinge "heute in
keiner Form vorhanden" sind, und dass der Text mitziehen muss, sobald das Audit-Log existiert,
"sonst wird eine wahre Aussage falsch".

Vier Arten, wie das schiefgeht, und alle vier sind billig zu vermeiden und teuer zu reparieren:

1. **Der Text zieht nicht mit.** Das Audit-Log ist in der freien App, der Store sagt weiter
   "geplant". Ein Interessent, der wegen dieser Zeile schreibt, bekommt eine Antwort, die seiner
   eigenen Beobachtung widerspricht.
2. **Der Text zieht zu weit mit.** Aus "Zugriffsprotokoll über Werkzeugaufrufe" wird im Store
   "Audit-Log", und damit wird Pitfall 9 zur öffentlichen Zusage.
3. **Die Fake-Door wird von innen eingerissen.** Das Enterprise-Signal wird ab Oktober an genau
   diesen drei Nennungen gemessen. Wer eine der drei aus dem Angebot nimmt und in die freie App
   legt, verändert das Messinstrument mitten in der Messung, und die Auswertung wird
   uninterpretierbar. Das ist keine Marketingfrage, das ist die Frage, ob das Go-Kriterium noch
   trägt.
4. **AGPL macht die Entscheidung endgültig.** Was in dieses Repository kommt, ist unter AGPL-3.0
   veröffentlicht. Ein Audit-Log kann danach nicht mehr das kommerzielle Unterscheidungsmerkmal
   sein, gegenüber niemandem. Für den ISV-Call am 14.09. ist das eine Position, die vorher geklärt
   sein sollte, nicht eine, die man dort entdeckt.

Dazu die operative Nebenwirkung: der Store liest das Manifest ausschließlich beim Upload. Eine
Textänderung wird also erst mit einem Release sichtbar, das heißt, sie hängt am Owner-Tag-Gate und
an der Signatur über das heruntergeladene Asset. Wer die Textfrage erst beim Release stellt,
verschiebt das Release.

**Why it happens:**
Weil der Text an vier Stellen in drei Sprachen steht, weil er niemandem gehört, und weil ein
Feature-Commit sich nicht wie eine Änderung an einer Verkaufsaussage anfühlt.

**How to avoid:**
Die Textentscheidung wird **vor** dem Fundament getroffen und schriftlich festgehalten, mit genau
diesen vier Antworten:

1. Wie heißt das Feature nach außen (siehe Pitfall 9), in EN, DE und FR?
2. Bleibt "Audit-Log" in der Enterprise-Zeile stehen, oder rückt es heraus? Wenn es stehen bleibt,
   was ist der Zusatz, der es vom Ausgelieferten abgrenzt (etwa: Weiterleitung, Aufbewahrung
   jenseits der eingebauten Grenze, Gruppen-Policies)?
3. Wird die Messung des Enterprise-Signals dadurch berührt, und wenn ja, wie wird das im lokalen
   Auswertungsdokument des Owners vermerkt?
4. Geht die Textänderung mit 0.1.11 oder mit dem Audit-Release? Beides ist vertretbar, aber es
   muss dieselbe Antwort für alle vier Stellen und alle drei Sprachen sein.

Technisch gehört diese Frage in ein Gate: ein Test, der fehlschlägt, wenn im Repository ein
Audit-Modul existiert und im Manifest weiterhin "geplant"/"planned"/"prévus" neben dem
Audit-Begriff steht. Das ist dieselbe Bauart wie das Vokabular-Gate und dieselbe Lehre wie aus
v1.4: Beweisdokumente und Verkaufstexte brauchen dieselbe Faktenprüfung wie Code.

**Warning signs:**
Ein Feature-Branch, der `info.xml` nicht anfasst. Eine Änderung, die nur EN anfasst. Der Satz
"den Store-Text machen wir beim Release". Ein Release 0.1.11, das Textänderungen ausliefert, die
das noch kommende Audit-Log schon vorwegnehmen.

**Phase to address:**
Meilenstein-Design (Entscheidung) und Release-Phase (Ausführung, dreisprachig, mit dem Gate).
Berührt ausdrücklich auch Release 0.1.11: der `[Unreleased]`-Block darf nicht versehentlich eine
Aussage über das Audit-Log enthalten, die dann drei Wochen lang falsch im Store steht.

---

### Pitfall 11: Ein Protokoll über jeden Nutzeraufruf ist in der Zielgruppe ein Mitbestimmungstatbestand

**What goes wrong:**
Ein Log, das für jeden Werkzeugaufruf Nutzer, Zeit und Werkzeug festhält, ist eine technische
Einrichtung, die geeignet ist, Verhalten und Leistung von Beschäftigten zu überwachen. In
deutschen Organisationen löst genau diese Eignung eine Beteiligungspflicht aus: in Unternehmen
über den Betriebsrat, in Behörden, also in der Zielgruppe dieses Meilensteins, über den
Personalrat. Es kommt dabei nicht darauf an, ob jemand tatsächlich überwacht, sondern ob die
Einrichtung dazu geeignet ist.

Die Folge ist eine Umkehrung: das Feature, das als Enterprise-Verkaufsargument gedacht war, wird
im Einführungsprozess zum zusätzlichen Genehmigungsschritt. Der Betreiber muss eine
Dienstvereinbarung anfassen, bevor er die App einschalten darf. Wenn er das erst nach der
Installation merkt, schaltet er die App ab.

Verschärfend: `docs/privacy.md` verspricht heute ausdrücklich "no telemetry, no analytics, no
usage tracking". Ein Nutzungsprotokoll ist wörtlich das, was ein aufmerksamer Leser dort
ausgeschlossen sieht, auch wenn es lokal bleibt und einem anderen Zweck dient.

**Why it happens:**
Weil Audit-Logs in Produktentwicklungen als Sicherheitsfeature gedacht werden und die
arbeitsrechtliche Seite in einer anderen Abteilung sitzt, die es in einem Solo-Projekt nicht gibt.

**How to avoid:**
Drei Maßnahmen, alle in der Doku- und Konfigurationsschicht, keine davon teuer:

1. **Default aus.** Das Protokoll ist standardmäßig abgeschaltet, so wie `talk_send` hinter einem
   Admin-Schalter sitzt. Wer es einschaltet, trifft eine bewusste organisatorische Entscheidung.
   Das ist zugleich die einfachste Antwort auf Pitfall 6 und 8.
2. **Zweckbindung und Datensparsamkeit dokumentieren, in derselben Datei, die heute die
   Telemetrie-Aussage trägt.** Ein Absatz in `privacy.md`, der Zweck (Nachvollziehbarkeit von
   Zugriffen, Sicherheitsvorfälle), Umfang (Metadaten, keine Inhalte, siehe Pitfall 5),
   Aufbewahrung und den Adressaten benennt. Und ein Satz, der die Telemetrie-Aussage präzisiert,
   statt sie zu widerlegen: das Protokoll verlässt die Instanz nicht.
3. **Einen Hinweis für den Betreiber, wo er ihn liest**, also im Hilfetext der Admin-Einstellung
   und in `docs/faq.md`: dass die Aktivierung in Organisationen mit Personal- oder Betriebsrat
   üblicherweise eine Beteiligung erfordert. Dieser eine Satz macht aus einer bösen Überraschung
   ein Verkaufsargument für Gründlichkeit. Er ist bewusst als Hinweis formuliert, nicht als
   Rechtsauskunft.

**Warning signs:**
Ein Audit-Log, das per Default an ist. Ein `privacy.md`, das nach der Änderung noch dieselbe
Telemetrie-Zeile trägt. Eine Beschreibung, die "Sie sehen, was Ihre Mitarbeiter tun" als Nutzen
verkauft. Rückfragen aus einer Behörde, die mit "unser Personalrat" beginnen.

**Phase to address:**
Audit-Log-Fundament (Default-aus-Schalter) und Doku-Phase (`privacy.md`, `faq.md`, Hilfetext,
dreisprachig).

---

### Pitfall 12: Fremder Text landet im Log, und das Log ist ein neues Ziel

**What goes wrong:**
Dieses Projekt hat die Lethal-Trifecta-Position sorgfältig dokumentiert: der Assistent liest
fremden Text neben privaten Daten, Talk-Senden ist der einzige direkte Ausgangskanal, und der
Administrator kann diesen Kanal abschalten. Ein Audit-Log fügt dem eine neue Oberfläche hinzu, an
die selten gedacht wird:

- **Log-Injection.** Wenn irgendein Wert aus fremdem Text in eine Logzeile fließt (ein
  Werkzeugname ist es nicht, ein Fehlertext einer fremden App aber sehr wohl), kann er
  Zeilenumbrüche, JSON-Ausbrüche oder ANSI-Sequenzen tragen und damit im Log gefälschte Zeilen
  erzeugen. Ein Angreifer, der eine Mail schreiben kann, schreibt dann Zeilen in das Protokoll,
  das ihn überführen soll.
- **Das Log als Leseziel.** Wenn ein Abfrageendpunkt existiert (Pitfall 8), darf er unter keinen
  Umständen als Werkzeug auftauchen. Ein Modell, das das Protokoll aller Nutzer lesen kann, ist
  ein Datenleck mit Ansage, und in einer Instanz ohne strikte Administratorenprüfung liest ein
  Nutzer die Aktivität aller anderen.
- **Fehlermeldungen tragen mehr, als sie sollen.** Der bequemste Weg zu einer aussagekräftigen
  Zeile ist `str(exception)`, und eine Ausnahme aus dem HTTP-Client trägt gerne die vollständige
  URL, also Pfade, Tokens und Suchbegriffe. Das ist Pitfall 5 durch die Hintertür.

**Why it happens:**
Weil das Log als passiver Zuschauer wahrgenommen wird und nicht als Datenpfad mit eigenen
Eigenschaften.

**How to avoid:**
- Nur Werte aus einer geschlossenen Menge in die Zeile: Werkzeugnamen aus der Registry,
  Ergebnisklassen aus einem Enum, Zahlen aus Messungen. Alles Freitextliche wird auf den
  Ausnahmetyp reduziert, nie auf die Ausnahmenachricht. Das Muster gibt es im Repo schon
  (`exapp/purge.py` protokolliert `type(exc).__name__`), es muss nur zur Regel werden.
- Jeder Wert, der doch als Zeichenkette in die Zeile geht, wird auf eine Zeile normalisiert
  (Steuerzeichen und Zeilenumbrüche entfernen) und in der Länge begrenzt. Das ist dieselbe
  Bauart wie `marks.without_marks` und gehört in dasselbe Nachbarmodul.
- Der Abfrageweg ist kein MCP-Tool, sondern ein HTTP-Endpunkt mit Administratorenprüfung, und ein
  Contract-Test in der Bauart von `test_no_destructive_calls.py` stellt sicher, dass in der
  Tool-Registry kein Werkzeug auftaucht, dessen Name oder Beschreibung auf das Protokoll zeigt.

**Warning signs:**
`str(exc)` oder ein f-String mit einer URL in der Audit-Schreibstelle. Ein Werkzeug, das
`audit` im Namen trägt. Eine Logzeile im Test, die ein `\n` enthält.

**Phase to address:**
Audit-Log-Fundament (Wertemenge, Normalisierung) und Audit-Log-Ausgabe (Abfrageweg, Registry-Gate).

---

### Pitfall 13: Der zweite fremde Host verdoppelt still die Wartungslast eines Einzelbetreibers

**What goes wrong:**
Bisher hängt dieses Projekt an genau einer fremden Kadenz: Nextcloud. Mit OpenProject in openDesk
kommen drei weitere dazu, und sie takten schneller als die eigene:

| Quelle | Kadenz | Was uns bricht |
|--------|--------|----------------|
| openDesk | seit 1.3 monatliche Feature-Releases, dazu Patchreleases | Komponentenversionen springen, ohne dass wir gefragt werden: v1.17.2 fuhr Nextcloud 32.0.9 und OpenProject 17.6.0, v1.18.0 vom 19.08.2026 fährt Nextcloud 33.0.7 und OpenProject 17.7.2 |
| OpenProject | eigene Major-Kadenz | Abkündigungen wie die Workspaces-Umstellung, Scope-Pflicht ab 16.0.0 |
| Nubus/Keycloak | eigene Kadenz | Alles, was mit Token und Scopes zu tun hat |
| Nextcloud | bekannt | wie bisher |

Zwei konkrete Folgen, die heute schon feststehen:

1. **Unsere Beweise stehen auf der falschen Version.** Der Ein-Klick-Nachweis und der
   AppAPI-Erreichbarkeitsbeweis sind auf Nextcloud 34.0.3 gemessen. openDesk v1.18.0 fährt 33.0.7.
   Die Zielumgebung ist also nicht "neuer als getestet", sondern **älter**, und in einem Projekt,
   das seine Nachweise wörtlich nimmt, ist ein Nachweis auf einer anderen Hauptversion kein
   Nachweis. Das ist eine Spike-Frage, keine v2.0-Frage.
2. **Die Testmatrix multipliziert.** Heute läuft die Suite gegen eine Nextcloud. Mit OpenProject
   kommt eine zweite Instanz in jede Integrationsstufe, mit eigener Einrichtung, eigenen
   Seed-Daten und eigener Version. Für einen Einzelbetreiber ist das der Punkt, an dem
   Integrationstests aufhören, gefahren zu werden.

Dazu die Budgetseite: `BUDGET_BYTES = 18_000` ist bei 15712 gemessenen Bytes über 21 Werkzeuge
armiert, also rund 2200 Bytes Luft, ausdrücklich "für Formulierungen, nicht für ein neues
Werkzeug". Eine OpenProject-Familie in der Bauart "ein Werkzeug pro Operation" wären fünf bis acht
Werkzeuge und damit sicher über dem Gate. Und der Vergleich läuft nicht ins Leere: es existiert
bereits mindestens ein OpenProject-MCP-Server als Vorbild und als Konkurrenz
(`jtauschl/openproject-ce-mcp`), dessen Existenz die Frage schärft, was unsere Version besser
macht (Antwort: die Identität, siehe Pitfall 1, nicht die Breite).

**Why it happens:**
Weil der Aufwand einer Integration am Client-Modul gemessen wird und nicht an der Zahl der
fremden Kadenzen, denen man sich damit unterwirft.

**How to avoid:**
- Der Spike liefert eine **Wartungsschätzung**, nicht nur eine Machbarkeitsaussage: wie viele
  fremde Versionsstränge kommen dazu, wie oft brechen sie erfahrungsgemäß, und was kostet ein
  Bruch als Store-Release. Diese Zahl gehört in den ISV-Call, weil sie die Preisfrage stellt.
- Die Nextcloud-33-Frage wird im Spike gestellt und beantwortet, nicht in v2.0 entdeckt.
- Für v2.0 gilt die bewährte Gegenmaßnahme aus InfraNode und v1.2: **ein konsolidiertes Werkzeug
  mit Enum-Ressourcenparameter pro Familie**, nicht ein Werkzeug pro Operation. Ziel für
  OpenProject: zwei bis drei Werkzeuge, nicht acht. Und das Budget wird nach der Messregel
  angehoben, nie auf eine runde Zahl.
- Das Audit-Log ist ausdrücklich als **openDesk-unabhängiger** Baustein geplant, und das bleibt
  auch so, wenn der Spike enttäuschend ausgeht. Das ist die richtige Reihenfolge: der Baustein,
  der allein trägt, wird zuerst fertig.

**Warning signs:**
Eine v2.0-Planung ohne Zeile für "Versionspflege". Ein Werkzeugentwurf mit mehr als drei
OpenProject-Werkzeugen. Eine Budgetanhebung ohne Messzeile. Ein Spike, der Nextcloud 33 nicht
erwähnt.

**Phase to address:**
openDesk-Spike (Schätzung, Nextcloud-33-Frage, Werkzeugzuschnitt als Vorschlag) und
Meilenstein-Design (Reihenfolge: Audit-Log trägt allein).

---

### Pitfall 14: Welches der beiden Features hat historisch mehr Zeit gefressen

**What goes wrong:**
Die Intuition sagt: die Fremdintegration ist das große Ding, das Log ist ein Nachmittag. In der
Praxis ist es meist umgekehrt, und zwar aus einem strukturellen Grund: die Integration ist
zeitboxiert und ihr Ergebnis darf "nein" sein, das Log dagegen ist scheinbar klein, hat aber
Querschnittscharakter. Es berührt jeden Werkzeugaufruf, die Persistenz, den Purge-Pfad, die
Admin-Einstellungen, die Latenz, drei Dokumentationsdateien in drei Sprachen, den Store-Text und
die Enterprise-Positionierung. Jede der Pitfalls 5 bis 12 ist eine eigene Entscheidung, und keine
davon ist Code-Aufwand: es sind Entscheidungen, die einzeln eine Stunde dauern und gemeinsam eine
Woche, wenn sie nacheinander in der Implementierung auffallen statt davor.

Die Erfahrung des eigenen Projekts stützt das: v1.4 war ein reiner Textmeilenstein und hat
trotzdem einen vollen Audit-Durchgang gebraucht, weil Beweisdokumente dieselbe Faktenprüfung
brauchen wie Code.

**How to avoid:**
Die Reihenfolge der Phasen entlang der Entscheidungen bauen, nicht entlang der Module: erst eine
kurze Entscheidungsphase (Name, Umfang, Zielort, Default, Textfolge), dann Fundament, dann
Ausgabe, dann Doku und Release. Und der Spike bekommt seine Zeitbox schriftlich, mit einem
definierten Abbruchpunkt, weil eine Fremdintegration ohne Zeitbox die Woche frisst, die für die
Entscheidungen gebraucht wird.

**Phase to address:**
Meilenstein-Design, in der Phasenschneidung selbst.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Im Spike Client Credentials mit Impersonationsnutzer verwenden | OpenProject antwortet in Minuten | Der Machbarkeitsbeweis beweist die falsche Sache; wenn Code davon bleibt, bricht das Kernversprechen | Nur in einem Wegwerfskript unter `scripts/`, nie in `src/`, und der Bericht sagt es im ersten Absatz |
| Aus dem Spike ein Client-Modul mitnehmen | v2.0 startet mit Vorsprung | Der Code trägt die Identitätsannahme des Spikes weiter, und niemand liest sie noch einmal | Nie. Der Spike liefert einen Bericht und Fixtures, keinen Produktionscode |
| Argumente und Antworten ins Audit-Log schreiben | maximale Nachvollziehbarkeit, gute Fehlersuche | Eine zweite Kopie sensibler Daten, `privacy.md` wird falsch, Auskunftspflicht wächst | Nie. Metadaten plus HMAC-Kennungen decken jeden legitimen Zweck |
| Das Audit-Log ohne Größen- und Altersgrenze bauen | ein Feld weniger im Schema | Volume voll, OAuth-Store schreibunfähig, jede Verbindung tot, Reparatur nur mit Hostzugriff | Nie |
| Audit-Zeilen in die bestehende SQLite-Datei neben die OAuth-Tabellen legen | keine zweite Datei, keine zweite Öffnungslogik | Schreiblast auf derselben WAL-Datei, Purge- und Aufbewahrungssemantik kollidieren, ein volles Log killt die Authentifizierung | Nur mit eigener Datei oder mindestens eigener Grenze und ausdrücklich entschiedener Purge-Semantik |
| Das Feature "Audit-Log" nennen, ohne Kette und ohne Grenzbeschreibung | passt zum vorhandenen Store-Text | Erste ernsthafte Prüfung lehnt ab, und die Ablehnung färbt auf die belegten Aussagen ab | Nie. Entweder umbenennen oder die Kette bauen |
| Store-Text erst beim Release anfassen | Feature-Phase bleibt fokussiert | Textfrage blockiert das Release, das am Owner-Gate hängt; oder eine falsche Aussage steht wochenlang im Store | Nie. Die Textentscheidung fällt vor dem Fundament, die Ausführung im Release |
| Audit-Log per Default einschalten | "es wirkt sofort" | Mitbestimmungstatbestand ohne Vorwarnung, Logflut beim Betreiber, `privacy.md` widerspricht sich | Nie. Default aus, wie `talk_send` |
| Auf Warning-Level schreiben, damit es sichtbar ist | umgeht den Default-Loglevel | Der Log des Betreibers wird unbrauchbar, die App wird leiser gestellt oder abgeschaltet | Nur als ausdrücklich wählbare Stellung des Admin-Schalters, nicht als Default |
| Ein Werkzeug pro OpenProject-Operation | einfache Registrierung, klare Namen | Budget-Gate reißt, Cursors 80-Werkzeug-Decke rückt näher, "kuratiert schlank" verliert seine Grundlage | Nur wenn der Gesamtstand nach Messung unter einem neu armierten Gate bleibt |
| Den Spike gegen `openproject:latest` fahren | keine Versionsrecherche nötig | Gemessen wird eine Generation, die die Zielumgebung nicht fährt | Nie. Auf die openDesk-Version pinnen und die Version im Bericht nennen |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| OpenProject-Identität | Client Credentials, weil es sofort geht | Nutzeridentität zuerst klären: Token-Exchange (Frage an ZenDiS), sonst zweiter Authorization-Code-Durchlauf mit eigenem Widerruf |
| OpenProject-Auth-Varianten | API-Key und OAuth als gleichwertig behandeln | Der API-Key ist ein persönlicher Schlüssel pro Nutzer, also genau das App-Passwort-Gebastel, gegen das dieses Projekt antritt |
| OpenProject-Antwortform | HAL-Antwort durchreichen | `_embedded.elements` projizieren, `_links.*.title` für verwandte Objekte nutzen, `_links` sonst verwerfen |
| OpenProject-Filter | Ohne Filter anfragen und "alles" erwarten | Der Standardfilter der Arbeitspaket-Endpunkte liefert nur offene (`status_id`, Operator `o`). Immer explizit filtern |
| OpenProject-Filtersyntax | Query-Parameter wie üblich bauen | Ein URL-kodiertes JSON-Array mit Operator-Objekten; `eprops` (komprimiert) nicht benutzen, es macht Logs unlesbar |
| OpenProject-Paginierung | Cursor erwarten | Offset-Paginierung: `offset` ist die Seitenzahl (Default 1), `pageSize` die Größe (Default 20, dokumentiertes Maximum 1000). Ohne explizites `sortBy` sind Seiten nicht stabil |
| OpenProject-Berechtigungen | 404 als "existiert nicht" lesen | 404 heißt auch "du darfst nicht wissen, ob es existiert". Der Hint muss beide Ursachen nennen, wie beim Mail-404 |
| OpenProject-Handlungsangebote | Aktionen aus dem eigenen Wissen ableiten | Aktionen existieren nur, wenn der passende Link in `_links` steht. Anwesenheit prüfen, nicht raten |
| OpenProject-Versionen | Gegen die Doku von 15/16 bauen | openDesk fährt 17.7.x. Ab 16.0.0 Scope-Pflicht für OIDC-JWT, ab 17 Workspaces statt projektbezogener Endpunkte (MEDIUM: aus Release-Notes, nicht gemessen) |
| OpenProject-Rate-Limits | Annehmen, es gäbe keine | `OPENPROJECT_RATE_LIMITING_API__V3` begrenzt Form-Endpunkte auf 6 pro 3 Sekunden, ist per Default aus, kann aber im Ziel an sein. Nie automatisch wiederholen |
| openDesk-Deployment | "openDesk enthält Nextcloud, also läuft unsere App dort" | Kubernetes, Helm, gepinnte Komponenten. Erst klären, ob ein AppAPI-Deploy-Daemon existiert und ob es eine App-Allowlist gibt |
| openDesk-Versionen | Gegen die neueste Nextcloud testen | v1.18.0 (19.08.2026): Nextcloud 33.0.7, OpenProject 17.7.2, Nubus Keycloak 26.7.0. Unsere Nachweise stehen auf 34.0.3 |
| openDesk-Vorintegration | Eine Nextcloud-OpenProject-Kopplung neu erfinden | `integration_openproject` ist in openDesk vorkonfiguriert (Zwei-Wege-OAuth2). Erst ansehen, dann entscheiden, ob wir daneben oder darauf bauen |
| ZenDiS-Aufnahme | Einen dokumentierten Prozess annehmen | Öffentlich sind Komponentenliste und Releases, kein Aufnahmeverfahren und keine Fristen. Das ist selbst eine Frage für den ISV-Call, und die Antwort bestimmt, ob v2.0 einen Vertriebsweg hat |
| AppAPI-Log | `POST /ocs/v2.php/apps/app_api/api/v1/log` benutzen und fertig | PSR-3-Level 0..7, Nachricht ist eine Zeichenkette (JSON selbst hineinschreiben), ein zusätzlicher OCS-Roundtrip pro Zeile, und der Default-Loglevel der Instanz verschluckt Info |
| Nextcloud-Logdatei als Audit-Ziel | Auf Rotation vertrauen | `log_rotate_size` steht per Default auf 100 MB und überschreibt eine bereits vorhandene rotierte Datei: es existiert genau eine Generation |
| Purge und Audit | Das Audit-Log stillschweigend mitlöschen oder stillschweigend behalten | Bewusst entscheiden, im Purge-Runbook und in `privacy.md` benennen, mit Test |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Synchroner Audit-Roundtrip pro Werkzeugaufruf | jeder Aufruf wird um eine Nextcloud-Antwortzeit langsamer, `prepare_context` sichtbar träger | Eigenes kleines Zeitbudget, Fehler wird zu einer Zählung, nie zu einem Werkzeugfehler; Schreiben nicht im kritischen Pfad der Antwort | Sofort, beim ersten Aufruf gegen eine langsame Instanz |
| Eine Audit-Zeile pro HTTP-Anfrage statt pro Werkzeugaufruf | Logvolumen verfünffacht sich, `prepare_context` erzeugt fünf Zeilen | Eine Zeile pro Werkzeugaufruf, Beine als Zählung im Feld | Ab dem ersten Bundle-Aufruf |
| Audit-Schreiben in dieselbe SQLite-Datei wie der OAuth-Store | Token-Rotation wird langsamer, "database is locked" unter Last | Eigene Datei oder mindestens eigener Schreibpfad, WAL bleibt, `busy_timeout` gilt | Bei parallelen Agentenläufen mehrerer Nutzer |
| Unbegrenztes Wachstum im Volume | Volume läuft voll, Authentifizierung stirbt, Healthcheck merkt nichts | Zeilen- und Altersgrenze, Größe im Status sichtbar | Nach Monaten, bei zweistelliger Nutzerzahl früher |
| OpenProject-Antwort ohne Projektion | eine Werkzeugantwort ist zweistellig kilobytegroß, Client-Kontext läuft voll | Feldprojektion, `_links` verwerfen, `title` der Relationen nutzen | Bei der ersten realen Abfrage mit 20 Arbeitspaketen |
| OpenProject-Anfrage ohne `pageSize` | 20 statt der erwarteten Menge, oder bei hohem `pageSize` sehr langsame Antworten | Immer explizit setzen, Obergrenze im Client kappen, `degraded`-Eintrag wenn die Kappung greift | Bei Projekten mit mehr als 20 Arbeitspaketen, also praktisch immer |
| Zweite fremde Instanz in `prepare_context` | Wandzeit springt, weil ein zweiter Host antworten muss | Wenn OpenProject je ins Bundle kommt: eigenes Budget, eigener `degraded`-Satz, gemessen statt geschätzt | Ab dem ersten Bundle mit einem OpenProject-Bein |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Impersonationsnutzer für OpenProject | Jeder Fragende sieht die Sicht eines fremden Kontos: das Kernversprechen ist gebrochen, in der Zielgruppe ein Ausschlusskriterium | Nutzeridentität klären, bevor Code entsteht; Client Credentials ausdrücklich ausschließen und die Begründung festhalten |
| Ein OpenProject-Zugangsdatum im Container statt pro Nutzer | Ein Secret, das alle Nutzer bedient, ist ein Vorfall mit einem einzigen Lesevorgang | Pro Nutzer, verschlüsselt, an die Autorisierung gebunden, wie das App-Passwort heute |
| Nutzinhalte im Audit-Log | Persistente Zweitkopie sensibler Daten, `privacy.md` wird unwahr, Auskunfts- und Löschpflichten wachsen | Metadatenschema, Kanarientest, Contract-Test über die Schreibstelle |
| Fremder Text ungefiltert in einer Logzeile | Log-Injection: gefälschte Zeilen im Protokoll, das den Angreifer überführen soll | Nur Werte aus geschlossenen Mengen; alles andere auf Typnamen reduzieren; Steuerzeichen entfernen, Länge kappen |
| Ein Werkzeug, das das Protokoll liest | Ein Modell mit Zugriff auf die Aktivität aller Nutzer | Abfrage als HTTP-Endpunkt mit Administratorenprüfung; Registry-Gate gegen ein Werkzeug mit Protokollbezug |
| `str(exception)` in der Audit-Zeile | Vollständige URLs mit Pfaden, Tokens und Suchbegriffen im Log | `type(exc).__name__`, wie in `exapp/purge.py` bereits praktiziert |
| Audit-Log ohne laufende Nummer und ohne Verlustzählung | Fehlende Zeilen sind nicht erkennbar, also ist das Log als Nachweis wertlos | Laufende Nummer je Zeile, Zähler für verworfene Zeilen im Status |
| "Revisionssicher" behaupten ohne Kette | Falsche Zusage gegenüber einem Prüfer, Rufschaden auf alle belegten Aussagen | Entweder Hash-Kette plus Prüfbefehl, oder das Wort nicht benutzen und die Grenze beschreiben |
| Audit-Log per Default an | Mitbestimmungstatbestand ohne Vorwarnung; Widerspruch zur Telemetrie-Aussage | Default aus, Admin-Schalter, Hinweis im Hilfetext |
| Zweiter Host ohne SSRF- und URL-Disziplin | Ein `href` aus einer HAL-Antwort zeigt auf einen fremden Host und wird gefolgt | Die Regel aus `provider_map.absolute_url` gilt auch hier: parsen, nie folgen, jede URL auf der konfigurierten Basis neu bauen |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Der Administrator findet das Protokoll nicht | Ein Feature, das existiert und niemandem nützt; im Support wirkt es wie ein Fehler | Ausgabe in den Nextcloud-Log, wo er ohnehin nachsieht, plus ein Leseweg ohne Shell |
| Protokolleinträge erscheinen nicht, weil der Loglevel sie schluckt | Der Betreiber hält das Feature für kaputt | Der Hilfetext der Admin-Einstellung nennt den Default-Loglevel in einem Satz; der Schalter erlaubt die Stellung, die auch bei Default sichtbar ist |
| Der Nutzer erfährt nicht, dass seine Aufrufe protokolliert werden | Vertrauensverlust genau bei der Zielgruppe, die wegen Datenschutz kommt | Ein Satz auf der `/connections`-Seite, wenn das Protokoll aktiv ist, plus der Absatz in `privacy.md` |
| "Audit-Log" im Store, "Zugriffsprotokoll" in der App | Der Interessent kann nicht prüfen, ob er bekommt, was beworben wurde | Ein Name, in drei Sprachen, überall derselbe |
| OpenProject-Werkzeuge, die 404 als "gibt es nicht" erklären | Der Nutzer sucht ein Arbeitspaket, das er schlicht nicht sehen darf, und glaubt, es sei gelöscht | Hint nennt beide Ursachen: unbekannt oder nicht sichtbar |
| Zweiter Consent-Durchlauf ohne Erklärung | Der Nutzer versteht nicht, warum er sich noch einmal anmelden soll | Wenn es dazu kommt: die `/connections`-Seite zeigt beide Verbindungen getrennt, mit getrenntem Widerruf |

## "Looks Done But Isn't" Checklist

- [ ] **Spike-Bericht:** oft fehlt die Angabe, als welcher Nutzer gemessen wurde. Prüfen: steht
      der Nutzername und der Auth-Weg im ersten Absatz?
- [ ] **Spike-Bericht:** oft fehlt die Versionsangabe. Prüfen: OpenProject-Version genannt, auf
      die openDesk-Version gepinnt?
- [ ] **Spike-Bericht:** oft fehlt die Trennung "gemessen" gegen "angenommen". Prüfen: gibt es
      einen Abschnitt "nicht gemessen, weil keine openDesk-Instanz vorhanden"?
- [ ] **Spike-Bericht:** oft fehlt die Installierbarkeitsfrage. Prüfen: sind Deploy-Daemon,
      App-Allowlist und Nextcloud-33-Frage beantwortet oder als offen markiert?
- [ ] **Fragenliste für den ISV-Call:** oft fehlt die Identitätsfrage in beantwortbarer Form.
      Prüfen: steht sie als erste Frage und ist sie mit Ja oder Nein beantwortbar?
- [ ] **Audit-Zeile:** oft enthält sie Inhalte. Prüfen: Kanarientest mit einer bekannten
      Zeichenkette in Argumenten und Antwort, die in keiner Zeile auftaucht.
- [ ] **Audit-Zeile:** oft trägt sie nur eine Identität. Prüfen: Nutzer, Autorisierung, Client
      und Modus, je ein Test pro Credential-Modus.
- [ ] **Audit-Speicher:** oft fehlt die Grenze. Prüfen: ein Test schreibt über die Grenze und die
      Datei wächst nicht; der OAuth-Store bleibt schreibfähig.
- [ ] **Audit-Ausgabe:** oft nur lokal. Prüfen: auf einer Instanz mit unverändertem Default-
      Loglevel erscheint eine Zeile im Nextcloud-Log, belegt durch einen Logauszug.
- [ ] **Audit-Ausgabe:** oft ohne Leseweg. Prüfen: ein Administrator kommt ohne Shell an die
      letzten Zeilen.
- [ ] **Audit-Latenz:** oft ungemessen. Prüfen: Werkzeuglatenz vor und nach der Aktivierung,
      nach der Messmethodik, die für `prepare_context` schon existiert.
- [ ] **Purge:** oft unentschieden. Prüfen: `occ mcp_connector:purge --force` tut mit dem
      Protokoll das, was `privacy.md` behauptet, mit Test.
- [ ] **Default:** oft an. Prüfen: frische Installation, Protokoll aus, ein Test hält das fest.
- [ ] **Store-Text:** oft nur EN. Prüfen: EN, DE und FR in `info.xml` plus `README.md`,
      `README.de.md`, `README.fr.md` sagen dasselbe, und das Gate gegen "geplant neben
      vorhandenem Audit" ist grün.
- [ ] **`privacy.md`:** oft widerspricht der Telemetrie-Absatz dem neuen Protokoll. Prüfen: der
      Abschnitt "What the app stores" nennt das Protokoll, Zweck, Umfang und Aufbewahrung.
- [ ] **Grenzbeschreibung:** oft fehlt der "was es nicht leistet"-Absatz. Prüfen: er existiert
      und nennt den Administrator ausdrücklich.
- [ ] **Release 0.1.11:** oft nimmt der Changelog schon vorweg, was noch nicht existiert. Prüfen:
      der `[Unreleased]`-Block enthält keine Aussage über das Audit-Log.

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Volume durch das Protokoll vollgelaufen, OAuth-Store schreibunfähig | HIGH | Nur mit Hostzugriff: Container stoppen, Volume aufräumen, starten. In Kubernetes-Umgebungen ein Eskalationsfall beim Betreiber. Deshalb ist die Grenze Pflicht und nicht Kür |
| Nutzinhalte im Protokoll bereits geschrieben | HIGH | Löschen ist technisch trivial und rechtlich nicht das Ende: die Aussage in `privacy.md` war im Auslieferungszeitraum falsch. Korrektur, Changelog-Eintrag, Store-Release. Prävention ist die einzige echte Antwort |
| Store-Text sagt "geplant", während das Feature ausgeliefert ist | MEDIUM | Textänderung, aber sichtbar erst mit dem nächsten Release, also mit Owner-Tag-Gate und Signaturlauf. Wochen, in denen die falsche Aussage steht |
| Prüfer lehnt "Audit-Log" ab | MEDIUM bis HIGH | Umbenennen, Grenzbeschreibung nachziehen, in drei Sprachen, plus ein Gespräch, das die anderen Aussagen wieder trägt. Billiger, wenn die Grenze von Anfang an dokumentiert war |
| Spike hat gegen einen Impersonationsnutzer gemessen und der Code blieb | MEDIUM | Wegwerfen und mit der geklärten Identität neu bauen. Teuer wird es erst, wenn darauf schon Werkzeuge stehen |
| openDesk lässt keine externen ExApps zu | LOW technisch, HIGH strategisch | Kein Code ist verloren, wenn der Spike vor dem Bauen kam. Die Konsequenz ist eine andere v2.0-Reihenfolge, deshalb muss diese Frage zuerst gestellt werden |
| OpenProject-Client gegen abgekündigte Endpunkte gebaut | LOW bis MEDIUM | Endpunktpfad ist eine Konstante im Client, wenn die Generation gepinnt ist. Teuer nur, wenn die Pfade über die Tools verstreut sind |
| Mitbestimmung nachträglich gefordert | LOW für uns, HIGH für den Betreiber | Schalter aus, Betrieb läuft weiter. Genau deshalb ist Default aus die richtige Wahl |

## Pitfall-to-Phase Mapping

Phasennamen sind thematisch; die Roadmap nummeriert sie.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| 9, Anspruch des Wortes "Audit-Log" | **Meilenstein-Design, vor allem anderen** | Eine schriftliche Entscheidung: Name in EN/DE/FR, Umfang, Grenze, Kette ja oder nein |
| 10, Store-Text und Enterprise-Versprechen | **Meilenstein-Design** (Entscheidung), **Release** (Ausführung) | Gate: Audit-Modul im Repo und "geplant" neben dem Audit-Begriff im Manifest schließen sich aus |
| 14, Reihenfolge und Zeitbox | **Meilenstein-Design** (Phasenschneidung) | Der Spike hat einen schriftlichen Abbruchpunkt; die Entscheidungsphase liegt vor dem Fundament |
| 2, Installierbarkeit in openDesk | **openDesk-Spike, Teil 1** | Drei Ja-Nein-Antworten mit Quelle oder Vermerk "offen, ISV-Call" |
| 1, Nutzeridentität gegen OpenProject | **openDesk-Spike, Teil 1** | Genau ein tragfähiger Weg benannt, oder begründet keiner; Client Credentials ausdrücklich ausgeschlossen |
| 3, Spike ohne Zielinstanz | **openDesk-Spike**, Rahmenregel | Bericht trennt Gemessenes von Angenommenem, nennt Versionen, keine Datei unter `src/` |
| 4, OpenProject-API-Form | **openDesk-Spike, Teil 2** | Je ein Abschnitt zu HAL, Filtern, Berechtigungen, Paginierung, mit gemessener Beispielantwort und Bytegröße vor und nach Projektion |
| 13, Wartungslast und Werkzeugbudget | **openDesk-Spike** (Schätzung), **Meilenstein-Design** (Reihenfolge) | Der Bericht nennt die Zahl der neuen Versionsstränge und einen Werkzeugzuschnitt mit maximal drei Werkzeugen |
| 5, zweite Kopie sensibler Daten | **Audit-Fundament**, erste Designentscheidung | Kanarientest grün, Contract-Test über die Schreibstelle, `privacy.md` in derselben Phase geändert |
| 6, unbegrenztes Wachstum | **Audit-Fundament**, mit dem Schema | Test schreibt über die Grenze, Datei wächst nicht, OAuth-Store bleibt schreibfähig, Größe im Status sichtbar |
| 7, Zurechenbarkeit | **Audit-Fundament**, im Zeilenschema | Ein Test je Credential-Modus zeigt, welche Identitätsfelder gefüllt sind |
| 11, Mitbestimmung und Zweckbindung | **Audit-Fundament** (Default aus), **Doku** (Texte) | Frische Installation protokolliert nichts; `privacy.md` und `faq.md` tragen Zweck, Umfang, Aufbewahrung und den Beteiligungshinweis |
| 12, Log-Injection und Leseziel | **Audit-Fundament** (Wertemenge), **Audit-Ausgabe** (Abfrageweg) | Registry-Gate gegen ein Protokoll-Werkzeug; Test mit Steuerzeichen in einem geloggten Wert |
| 8, Log, das niemand sieht | **Audit-Ausgabe**, eigene Phase | Logauszug einer Instanz mit unverändertem Default-Loglevel; Leseweg ohne Shell; Latenzmessung vor und nach |
| Doku, i18n, Store-Text | **Release-Phase** | EN, DE und FR sagen dasselbe; `privacy.md`, `faq.md`, `uninstall.md` und der Changelog nennen das Protokoll und seine Grenze |

## Sources

**Offizielle Dokumentation, OpenProject (HIGH, über Context7 `/websites/openproject` und direkt):**
- API-Einführung, Authentifizierung (API-Key als Bearer und Basic, OAuth 2.0 Authorization Code, PKCE, Client Credentials): https://www.openproject.org/docs/api/introduction/
- Filter-Syntax (URL-kodiertes JSON, Operatoren): https://www.openproject.org/docs/api/filters/
- Arbeitspakete, Standardfilter, Paginierung, Berechtigung "view work packages", Workspaces-Abkündigung: https://www.openproject.org/docs/api/endpoints/work-packages/
- Sammlungsform (HAL, `_embedded.elements`, `count`/`offset`/`pageSize`/`total`): https://www.openproject.org/docs/api/endpoints/documents
- Berechtigungskonzept, kontextabhängig gerenderte Links, 404 statt 403: https://www.openproject.org/docs/development/concepts/permissions/
- Formulare und 403 bei fehlenden Rechten: https://www.openproject.org/docs/api/forms/
- Rate Limiting (`OPENPROJECT_RATE_LIMITING_API__V3`, Form-Endpunkte 6 pro 3 Sekunden, Default aus): https://www.openproject.org/docs/installation-and-operations/configuration
- OAuth-Anwendungen und "Client credentials user": https://www.openproject.org/docs/system-admin-guide/authentication/oauth-applications/
- Docker-Installation für eine lokale Spike-Instanz: https://www.openproject.org/docs/installation-and-operations/installation/docker/
- Release Notes 16.0.0 (Breaking Change: JWT eines OIDC-Providers braucht Scope): https://www.openproject.org/docs/release-notes/16/16-0-0/

**Offizielle Dokumentation, openDesk und ZenDiS (HIGH für Versionen, MEDIUM für den Rest):**
- openDesk-Architektur (Kubernetes, Helmfile, Keycloak, OpenLDAP, Nubus, `integration_openproject`): https://docs.opendesk.eu/operations/architecture/
- openDesk-Release-Matrix (v1.18.0 vom 19.08.2026: Nextcloud 33.0.7, OpenProject 17.7.2, Nubus Keycloak 26.7.0): https://releases.opendesk.eu/
- openDesk-Deployment-Repository auf openCode: https://gitlab.opencode.de/bmi/opendesk/deployment/opendesk
- Kein öffentlich dokumentiertes Verfahren zur Aufnahme neuer Komponenten gefunden. Das ist der Befund, nicht eine Lücke der Recherche: die Frage gehört in den ISV-Call

**Offizielle Dokumentation, Nextcloud (HIGH):**
- Logging: Default-Loglevel 2 (Warning), `admin_audit` schreibt auf Info und wird deshalb per Default unterdrückt, `log_rotate_size` 100 MB und Überschreiben der rotierten Datei, `logfile_audit`/`log_type_audit`: https://docs.nextcloud.com/server/stable/admin_manual/configuration_server/logging_configuration.html
- AppAPI-Logging für ExApps (`POST /ocs/v2.php/apps/app_api/api/v1/log`, PSR-3-Level 0..7): https://docs.nextcloud.com/server/stable/developer_manual/exapp_development/tech_details/api/logging.html
- Deploy-Konfigurationen, `docker-install` gegen `manual-install`, Docker Socket Proxy, HaRP: https://docs.nextcloud.com/server/stable/admin_manual/exapps_management/DeployConfigurations.html

**Feldbelege und Ökosystem (MEDIUM):**
- `nextcloud/user_oidc#925`, "Provide OIDC generated access token to other apps. Support OIDC token exchange": offen, keine verlinkten Pull Requests. Das ist der Beleg dafür, dass der saubere Token-Weg heute nicht bereitsteht: https://github.com/nextcloud/user_oidc/issues/925
- OpenProject-Doku zur Nextcloud-Integration, Zwei-Wege-OAuth2 und OIDC-SSO: https://www.openproject.org/docs/system-admin-guide/integrations/nextcloud/
- Vorhandener OpenProject-MCP-Server als Vorbild und Konkurrenz: `jtauschl/openproject-ce-mcp` (Context7)

**Normen und Rechtsrahmen (MEDIUM, Recherche, keine Rechtsberatung):**
- BSI IT-Grundschutz OPS.1.1.5 Protokollierung: zentrale Protokollierungsinfrastruktur, Administratoren dürfen Protokolldaten nicht ändern oder löschen können, Signatur und Verschlüsselung, Bindung an Datenschutzrecht: https://www.bsi.bund.de/SharedDocs/Downloads/DE/BSI/Grundschutz/IT-GS-Kompendium_Einzel_PDFs_2023/04_OPS_Betrieb/OPS_1_1_5_Protokollierung_Edition_2023.pdf
- BSI-Mindeststandard zur Protokollierung und Detektion von Cyber-Angriffen: https://www.bsi.bund.de/SharedDocs/Downloads/DE/BSI/Mindeststandards/Mindeststandard_BSI_Protokollierung_und_Detektion_Version_1_0a.pdf
- Stand der Technik für manipulationserkennbare Protokolle (Hash-Kette je Eintrag, signierte Kettenköpfe, Weiterleitung vom Host weg): https://mattermost.com/blog/compliance-by-design-18-tips-to-implement-tamper-proof-audit-logs/

**Dieses Repository (HIGH, direkt gelesen):**
- `src/mcp_connector/oauth/store.py` (SQLite, WAL, verschlüsselte App-Passwörter, Token nur als Hash),
  `src/mcp_connector/config.py` (`persistent_storage`, `APP_PERSISTENT_STORAGE`, vier Credential-Modi),
  `src/mcp_connector/exapp/purge.py` und `exapp/occ.py` (`occ mcp_connector:purge`),
  `src/mcp_connector/exapp/config_values.py` (deklarative Admin-Einstellungen),
  `scripts/check_tool_budget.py` (`BUDGET_BYTES = 18_000`, Messzeile 15612 plus 15 Prozent),
  `docs/privacy.md` (Abschnitte "What the app stores", "What the app never does", "Deletion and user control", "Retention"),
  `README.md:512` und `appinfo/info.xml` (Enterprise-Absatz EN 77, DE 122, FR 169),
  `Dockerfile` (unprivilegierte uid 10001, `/nc_app_mcp_connector_data` mit 0700),
  `.planning/PROJECT.md` (Meilensteinziel, Schlüsselentscheidungen, Nachweislage v1.1 bis v1.4)

---
*Pitfalls research for: OpenProject/openDesk als zweiter Host und ein Audit-Log über jeden Tool-Aufruf*
*Researched: 2026-08-28*
