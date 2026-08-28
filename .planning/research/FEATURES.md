# Feature Research: v1.5 Vorlauf openDesk (OpenProject + Audit-Log)

**Domain:** Erste openDesk-Komponente (OpenProject) in einer bestehenden MCP-only-ExApp, plus Protokollierung von KI-Werkzeugaufrufen als Enterprise-Baustein
**Researched:** 2026-08-28
**Confidence:** HIGH für die OpenProject-API-Lage (Endpunkte, Filter-Syntax und `select`-Signaling direkt aus Doku und Quellcode geprüft), HIGH für die Wettbewerbslage (offizielle OpenProject-MCP-Doku und drei Community-Server direkt gelesen), HIGH für die Nextcloud-Protokollmechanik (Admin- und Developer-Manual), MEDIUM für die regulatorischen Erwartungen (Primärquellen zu Art. 12/26 AI Act und DSK-Orientierungshilfe gelesen, aber keine Aussage eines echten Behörden-Einkäufers), LOW für Nutzerpriorisierung innerhalb OpenProject (Ableitung aus Wettbewerbs-Toolschnitten und der OpenProject-eigenen UI, keine eigenen Store-Rückmeldungen)

> Die v1.2-Fassung dieser Datei (Talk, Tables, Mail) steht in der Git-Historie. Dieses Dokument
> betrachtet ausschließlich die beiden neuen Bausteine des Meilensteins v1.5. Die neun bestehenden
> Familien, `prepare_context`, `fetch` und OAuth 2.1 sind Voraussetzung, nicht Gegenstand.

## Ausgangslage in drei Sätzen

**OpenProject ist gelöst, nur anders als erwartet.** OpenProject liefert seit kurzem einen eigenen
MCP-Server unter `/mcp` der eigenen Instanz, ausdrücklich **read-only** ("tools to manipulate data
might be added in the future") und ausdrücklich als **Enterprise-Add-on** ab Professional-Plan. Damit
ist unser Wert bei OpenProject nicht die Werkzeugabdeckung, sondern die **Verbindung**: ein Endpunkt,
eine Zustimmung, Nextcloud-Daten und Projektdaten in derselben Sitzung, und das auch auf einer
Community-Instanz, die den offiziellen Server gar nicht bekommt.

**Der Audit-Log ist kein Log, sondern drei Oberflächen.** Was Käufer wollen, ist eine beantwortbare
Frage ("wer hat wann über welchen Client welche Daten berührt"), ein Export und eine Löschfrist. Was
sie ausdrücklich nicht wollen, ist eine zweite Kopie ihrer Mail- und Chat-Inhalte in einer neuen
Datenbank und eine Auswertung, die zur Leistungskontrolle taugt.

**Der billigste Hebel liegt bereits im Repo.** Jedes Werkzeug trägt den `graceful`-Dekorator aus
`server/__init__.py`, es gibt eine persistente SQLite-Ablage mit WAL und Verschlüsselung
(`oauth/store.py`), eine servergerenderte Nutzerseite mit HMAC-Formularschutz (`oauth/connections.py`),
einen occ-Pfad über AppAPI-PublicFunctions (`exapp/purge.py`) und Declarative Admin-Settings mit fünf
Werten. Der Audit-Log ist damit ein Aufsatz auf vorhandene Bauteile, kein neues Subsystem.

---

# Teil A: OpenProject

## A.0 Was ein Assistent an einem Projektmanagement-System wirklich tun soll

Die Frage lässt sich nicht aus Endpunktlisten beantworten, sondern aus dem, was OpenProject selbst,
die Vendor-MCPs und die Community-Server als Einstiegspunkte bauen. Vier Fragen decken den
allergrößten Teil ab, und sie sind nach Häufigkeit sortiert, nicht nach API-Eleganz:

1. **"Was liegt heute bei mir?"** Arbeitspakete, mir zugewiesen, offen, nach Fälligkeit sortiert.
   Das ist ein einziger Request mit zwei Filtern und der mit Abstand häufigste Einstieg.
2. **"Was ist passiert, das mich betrifft?"** Der OpenProject-Posteingang (`/api/v3/notifications`)
   trägt pro Eintrag bereits den Grund (`mentioned`, `assigned`, `commented`, `dateAlert`, `created`)
   und das betroffene Arbeitspaket. Das ist der Talk-Digest-Moment dieses Meilensteins: hoher
   Kontextgewinn für einen Request.
3. **"Wie steht es um X, und worüber wurde geredet?"** Ein Arbeitspaket im Detail plus seine
   Kommentare. Der Detailsatz allein ist Statuszeile, den eigentlichen Nutzen für ein Modell tragen
   die Aktivitäten.
4. **"Welche Dokumente hängen daran?"** Über die Nextcloud-Integration führen `file_links` von einem
   Arbeitspaket zu echten Nextcloud-Dateien mit deren `fileid`. Das ist der einzige Punkt, an dem
   unser Produkt etwas kann, das weder der offizielle OpenProject-MCP noch ein Nextcloud-MCP für sich
   kann.

**Wo der Nutzen aufhört, das Tool-Budget wert zu sein**, lässt sich präzise benennen: sobald eine
Frage in OpenProject selbst schneller beantwortet ist als über ein Modell. Projektlisten,
Board-Konfigurationen, Versionen, Mitgliedschaften, Kategorien, Budgets, Meetings, Wiki-Seiten, News,
Dokumente, Zeiterfassungs-Auswertungen und der ganze Schema-Apparat (Typen, Prioritäten, Custom
Fields) sind Nachschlagewerte, keine Assistenz-Fragen. Der Community-Server `jtauschl/openproject-ce-mcp`
bildet genau diese Breite ab: 132 Werkzeuge, 106 ohne Admin-Schreibpfade. Jedes davon kostet in jeder
Sitzung Bytes, auch wenn es nie gerufen wird. Für uns ist die Grenze dort, wo eine fünfte Enum-Stufe
in einem Browse-Werkzeug nicht mehr trägt.

## A.1 API-Lage, verifiziert

| Fähigkeit | Endpunkt / Mechanik | Confidence |
|-----------|---------------------|------------|
| Wer bin ich | `GET /api/v3/users/me` | HIGH |
| Arbeitspakete filtern | `GET /api/v3/work_packages?filters=[{"assignee":{"operator":"=","values":["me"]}}]`, dazu `sortBy`, `pageSize`, `offset` | HIGH |
| Sonderwert `me` | Im Quellcode belegt: `Queries::Filters::MeValue::KEY = "me"`, eingebunden über `MeValueFilterMixin` in `PrincipalBaseFilter`, also für `assignee`, `author`, `responsible`, `watcher` | HIGH |
| Nur offene Vorgänge | Operator `o` auf `status` mit leerem `values` | HIGH |
| Volltext im Arbeitspaket | Operator `**` (Filtergrammatik der API) | MEDIUM |
| Posteingang | `GET /api/v3/notifications`, Filter `readIAN`, `reason`, `project`, `resourceId`, Default-Seitengröße 20, nur was der Nutzer sehen darf | HIGH |
| Kommentare | `GET /api/v3/work_packages/{id}/activities` (Collection mit `count`/`total`) | HIGH |
| Nextcloud-Dateien am Arbeitspaket | `/api/v3/work_packages/{id}/file_links`, `originData` trägt `id` (die Nextcloud-Dateikennung), `name`, `mimeType`, `size` | HIGH |
| Zeiteinträge | `GET /api/v3/time_entries` mit `user_id`, `project_id`, `spentOn`, `ongoing`; POST verlangt Projekt, Entität, Nutzer, Stunden, Datum und die Berechtigung "Log time" | HIGH |
| Antwortgröße senken | `select`-Signaling: `?select=total,elements/id,elements/subject`, Wildcard `*` je Ebene, Links sind atomar und nicht teilbar. **Nicht alle Endpunkte unterstützen es**, unterstützende sind ausdrücklich dokumentiert | HIGH für den Mechanismus, MEDIUM je Endpunkt |
| Authentifizierung | OAuth-2.0-Applikation in OpenProject, Scope `api_v3` ist der Default; alternativ persönliche API-Token. OIDC-SSO gegen einen gemeinsamen IdP ist Enterprise-Add-on | HIGH |

Der wichtigste Befund für die Phasenplanung: **HAL+JSON ist unbrauchbar teuer.** Ein
Arbeitspaket-Element schleppt `_links` mit zwei Dutzend Verweisen und `_embedded` mit ganzen
Unterressourcen mit. Der Community-Server wirbt mit bis zu "−99 Prozent" Token gegenüber der Rohantwort.
`select` plus eigene Projektion ist deshalb keine Optimierung, sondern Voraussetzung, damit die
Familie überhaupt in ein Kontextfenster passt.

## A.2 Schreiboperationen: was existiert und was das Versprechen bricht

Das v1-Versprechen lautet wörtlich: kein Löschen, kein Überschreiben, kein Ändern von Freigaben.
Daran gemessen:

| Operation | API | Bricht das Versprechen? | Urteil |
|-----------|-----|--------------------------|--------|
| Arbeitspaket ändern (Status, Zuweisung, Datum, Text) | `PATCH /work_packages/{id}` | **Ja, Überschreiben.** Zusätzlich verlangt OpenProject optimistisches Sperren über `lockVersion`, ein Modell erzeugt damit reihenweise 409-Konflikte | Nicht bauen |
| Arbeitspaket löschen | `DELETE /work_packages/{id}` | **Ja, destruktiv.** Nimmt Kommentare, Zeiteinträge und Relationen mit | Nicht bauen |
| Projekt anlegen, kopieren, ändern, löschen | `/projects` | **Ja** bei Ändern und Löschen; Anlegen ist Struktur-Arbeit und gehört Menschen | Nicht bauen |
| Benachrichtigung als gelesen markieren | `POST /notifications/{id}/read_ian` | **Ja im Geist:** wir haben bei Talk teuer bewiesen, dass Lesen nichts verändert (`setReadMarker=0`). Ein Read-Tool, das den Posteingang leert, wirft das weg | Nicht bauen |
| Datei-Link anlegen | `POST /work_packages/{id}/file_links` | **Grenzfall.** Technisch additiv und rückholbar, aber es trägt die Existenz und den Namen einer Nextcloud-Datei in einen Projektkontext. Das ist freigabenah, und "keine Freigaben ändern" ist ein wörtliches Versprechen | Nicht in v1.5 |
| Anhang hochladen | `POST /work_packages/{id}/attachments` | Binärupload, Token-Unfall, Schadcode-Fläche | Nicht bauen |
| Watcher hinzufügen | `POST /work_packages/{id}/watchers` | Additiv und selbstbezogen, aber Nutzen nahe null | Nicht bauen |
| **Kommentar anlegen** | `POST /work_packages/{id}/activities` | **Nein.** Rein anfügend, Historie bleibt vollständig, Korrektur ist ein zweiter Kommentar. Exakt die Form von `talk_send` | Erlaubt, aber vertagt (A.5) |
| **Zeiteintrag anlegen** | `POST /time_entries` | **Nein.** Anfügend, auf den eigenen Nutzer bezogen, in der UI korrigierbar | Erlaubt, aber vertagt (A.5) |
| Arbeitspaket anlegen | `POST /work_packages` | Anfügend, also formal zulässig. Praktisch teuer: Typ, Projekt, Status und Pflicht-Custom-Fields müssen vorher aus dem Schema geholt werden, sonst rät das Modell | Nicht in v1.5 |

**Konsequenz für v1.5: OpenProject wird rein lesend ausgeliefert.** Das ist kein Rückstand, sondern
Gleichstand mit dem Hersteller: der offizielle OpenProject-MCP kann heute ebenfalls ausschließlich
lesen. Dazu kommt ein Milestone-interner Grund: im selben Release entsteht der Audit-Log. Ein neuer
Schreibpfad im selben Schnitt würde die erste Frage jedes Prüfers ("wer hat diesen Kommentar
geschrieben, das Modell oder der Mensch?") stellen, bevor die Antwort ausgeliefert ist.

## A.3 Feature Landscape OpenProject

### Table Stakes (Users Expect These)

Fehlt eines davon, wirkt die Familie halb gebaut.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Meine offenen Arbeitspakete | Die Einstiegsfrage schlechthin; jeder Wettbewerber hat ein Äquivalent, OpenProject selbst hat dafür eine Standardansicht | LOW | Ein Request: `filters=[{"assignee":{"operator":"=","values":["me"]}},{"status":{"operator":"o","values":[]}}]&sortBy=[["dueDate","asc"]]&pageSize=25`. Projektion auf id, subject, project, type, status, priority, dueDate, percentageDone |
| Posteingang lesen | "Was ist neu für mich" ist der zweite Reflex und in OpenProject ein eigener Navigationspunkt | LOW-MEDIUM | `GET /notifications?filters=[{"readIAN":{"operator":"=","values":["f"]}}]`. Der `reason` gehört unbedingt in die Antwort, sonst kann das Modell nicht priorisieren |
| Ein Arbeitspaket im Detail | Ohne Detailsatz ist eine Trefferliste eine Sackgasse | LOW | Kein eigener Tool-Slot: `fetch` um Präfix `wp:<id>` erweitern, achte Id-Art neben file, note, card, event, mail, message, table |
| Kommentare eines Arbeitspakets | Der eigentliche Kontext für Zusammenfassungen; Statusfelder allein erklären nichts | MEDIUM | `/activities` paginiert und mischt Systemänderungen mit echten Kommentaren. Systemeinträge per Default heraus, gleiche Regel wie bei Talk-Systemnachrichten |
| Arbeitspakete eines Projekts suchen und filtern | "Zeig mir die offenen Bugs in Projekt X" | MEDIUM | Derselbe Endpunkt wie `my_work`, andere Filterkombination. Volltext über den `**`-Operator, kein eigenes Suchwerkzeug |
| Projektliste | Nur als Vokabular: ohne Projektkennungen lässt sich kein Filter bilden | LOW | Hart kappen, projizieren auf id, identifier, name, active. Keine Hierarchie-Entfaltung |
| App-Erkennung und ehrlicher Fehlersatz | Etabliertes Muster (SRV-04): kein Stacktrace, keine HTML-Loginseite, wenn OpenProject fehlt, nicht konfiguriert oder der Nutzer nicht verbunden ist | LOW | Drei unterscheidbare Fälle mit je einem konkreten nächsten Schritt: "Administrator hat keine OpenProject-Adresse hinterlegt", "du bist nicht mit OpenProject verbunden, hier verbinden", "OpenProject antwortet nicht" |
| Instanzweiter Aus-Schalter | Gleiche Erwartung wie bei `NC_MCP_TALK_SEND`: eine ganze Familie muss administrativ abschaltbar sein | LOW | Sechster Wert in den Declarative Admin-Settings, Default aus. Eine Behörde, die OpenProject nicht anbindet, sieht die Familie im `tools/list`, bekommt aber einen klaren Satz statt eines Fehlers |

### Differentiators (Competitive Advantage)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Ein Endpunkt für Nextcloud und OpenProject** | Der offizielle OpenProject-MCP ist ein zweiter Server mit zweiter Autorisierung an einer anderen Adresse. Wer beides will, verbindet zwei MCP-Server, zahlt zweimal Tool-Budget und hat zwei Zustimmungsdialoge. Wir liefern eine Verbindung, eine Nutzerseite, ein Protokoll | MEDIUM (die Arbeit steckt in der Anmeldung, nicht in den Tools) | Das ist die Kernaussage des ganzen Bausteins und gehört wörtlich in die Store-Beschreibung und in den ISV-Call |
| **Der Sprung vom Arbeitspaket in die Datei** | `file_links` liefert `originData.id`, und das ist genau die Nextcloud-`fileid`, die unser `fetch("file:<id>")` schon auflöst. "Fass die Dokumente zu Arbeitspaket 4711 zusammen" ist damit eine Kette, die kein anderer MCP schließen kann | MEDIUM | Ein Request zusätzlich im `wp:`-Detail, hart gekappt (Vorschlag 10 Links). Der Nutzen ist genau dann da, wenn die Nextcloud-OpenProject-Integration bereits eingerichtet ist, was in openDesk der Regelfall ist |
| **Verfügbar auf der Community Edition** | Der offizielle MCP-Server ist Enterprise-Add-on ab Professional. Jede Behörde, jeder Verein und jedes Selfhosting-Setup ohne Enterprise-Lizenz hat heute keinen Weg zu OpenProject über MCP | LOW (ergibt sich) | Ehrliche Kehrseite: in einer openDesk-Enterprise-Installation existiert der Hersteller-Server. Unsere Aussage dort ist die Bündelung und der Audit-Log, nicht die Abdeckung |
| **Lesen ohne Nebenwirkung, auch hier** | Wir lassen den Posteingang ungelesen. Das ist dieselbe messbare Eigenschaft, die bei Talk zum Verkaufsargument geworden ist, und sie lässt sich als Regressionstest festnageln | LOW | Ein Test, der beweist, dass nach einem `inbox`-Aufruf `readIAN` unverändert ist |
| **`select`-Signaling konsequent genutzt** | Der Hersteller-MCP bietet dem Administrator drei Antwortformate zur Token-Steuerung an, weil das Problem real ist. Wir lösen es serverseitig auf API-Ebene und schicken gar nicht erst mehr über die Leitung | LOW-MEDIUM | Wo `select` nicht unterstützt wird, projizieren wir nach dem Empfang. Die Messung gehört in denselben Beleg wie das Budget-Gate |
| **Ein Browse-Werkzeug statt einer CRUD-Spiegelung** | 1 neues Werkzeug gegen 116 bis 132 bei den Community-Servern für dasselbe System | LOW | Setzt `deck_browse`, `tables_browse`, `mail_browse` fort. Dieselbe Antworthülle: `level`, `count`, `results`, `truncated` |
| **`prepare_context` bekommt ein openDesk-Bein** | "Was liegt heute an" umfasst dann Termine, Suche, Talk, Mail-Zähler und Projektarbeit. Das ist die einzige Stelle, an der sich Groupware und Projektmanagement in einer Antwort treffen | LOW-MEDIUM | Eigenes Zeitbudget, eigener `degraded`-Eintrag, Kappe 3 Einträge, nur ungelesene Benachrichtigungen und diese Woche fällige Arbeitspakete. Muss abschaltbar sein, sonst zahlt jeder Nutzer ohne OpenProject Latenz |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| **Volle CRUD-Abdeckung wie die Community-Server** | 132 Werkzeuge wirken vollständig; "kann alles" verkauft sich in einer README | Client-Tool-Limits sind real (Cursor warnt ab 40, kappt bei 80), und wir haben mit 21 Werkzeugen aus gutem Grund die Gegenposition | 1 Werkzeug plus eine `fetch`-Id-Art |
| **PATCH auf Arbeitspakete ("setz das auf erledigt")** | Der meistgewünschte Schreibwunsch überhaupt | Überschreiben ohne Historie im Feldsinn, plus `lockVersion`-Konflikte, die ein Modell nicht auflösen kann | Kommentar statt Feldänderung, sobald Schreiben überhaupt kommt. Statusänderung bleibt Menschenarbeit |
| **Alles was `DELETE` heißt** | Aufräum-Fantasie | Frontal gegen das Kernversprechen | Gar nicht |
| **Benachrichtigungen als gelesen markieren** | "Der Assistent räumt meinen Posteingang auf" | Verwandelt ein Lesewerkzeug in ein Schreibwerkzeug und macht `readOnlyHint=true` zur Lüge | Nur lesen. Markieren bleibt in OpenProject |
| **Den offiziellen OpenProject-MCP durchreichen (Proxy/Aggregator)** | Klingt nach null Arbeit und voller Abdeckung | Enterprise-Add-on (also für die Hälfte der Zielgruppe nicht vorhanden), zweite Autorisierung, fremde Werkzeugliste unkontrolliert in unserem Budget, fremde Beschreibungen in unserem Kontext, und unser Audit-Log sähe nur "proxy_call" | Eigene, schmale Werkzeuge. Falls ein Kunde den Hersteller-Server hat, soll er ihn direkt einbinden, das ist ehrlicher |
| **Eigenes `openproject_search`** | Wirkt wie eine Lücke, weil `unified_search` OpenProject nicht erreicht | Ein Tool-Slot für etwas, das eine Filterkombination im vorhandenen Browse ist | Volltext über den `**`-Operator als Parameter des `work_packages`-Levels |
| **OpenProject-Treffer in `unified_search` einmischen** | "Eine Suche über alles" ist der Traum | `unified_search` ist berechtigungstreue Nextcloud-OCS-Mechanik. Ein Fremdsystem dort einzuhängen bedeutet zwei Berechtigungsmodelle in einer Antwort und einen Treffer, dessen `kind` in kein bestehendes Schema passt | Getrennt lassen. `prepare_context` ist die Stelle, an der beide Welten nebeneinander stehen dürfen, klar getrennt beschriftet |
| **Rohes HAL+JSON durchreichen** | Spart Projektionscode | Ein einzelnes Arbeitspaket wird zu einem vierstelligen Token-Betrag, davon die Mehrheit `_links` | `select` plus feste Projektion, `truncated` benennen |
| **Custom Fields als eigene Werkzeugebene** | Jede Instanz hat welche, und die Kunden fragen danach | Instanzspezifisch, unbenannt (`customField12`), nicht generisch beschreibbar | Custom Fields im Detailsatz mit ihrem Anzeigenamen aus dem Schema mitliefern, aber kein Schema-Werkzeug |
| **Boards, Wiki, Meetings, News, Dokumente, Budgets, Versionen, Mitgliedschaften, Relationen, Backlogs** | Vollständigkeitsreflex | Jedes Werkzeug kostet Bytes in jeder Sitzung, auch bei Nutzern ohne OpenProject | Weglassen, bis ein Abnehmer eine konkrete Frage benennt, die daran scheitert |
| **Zeiterfassungs-Auswertung ("wie viel habe ich diesen Monat gebucht")** | Klingt nützlich | Aggregierte Arbeitszeit je Person ist genau die Datenart, die Personalvertretungen als Leistungskontrolle einstufen. Ein KI-Werkzeug, das sie bequem abrufbar macht, ist ein Verkaufshindernis, kein Feature | Nicht bauen. Eigene Zeiteinträge einzeln lesen wäre zulässig, ist aber ohne Aggregation nutzlos, also gleich weglassen |
| **Persönlicher API-Token als Anmeldeweg** | Am schnellsten gebaut, alle Community-Server machen es so | Wir positionieren uns seit v1.0 gegen "App-Passwort-Gebastel". Ein Produkt, dessen Kernversprechen spec-konformes OAuth ist, darf für die zweite Anwendung nicht auf Token-Einkleben zurückfallen | OAuth-2.0-Authorization-Code gegen OpenProject mit Scope `api_v3`, Refresh-Tokens in der bestehenden verschlüsselten Ablage. OIDC-Token-Tausch über den openDesk-IdP ist die v2-Antwort und eine Frage für den ISV-Call |

## A.4 Vorgeschlagener Tool-Schnitt

| Tool | Annotation | Form | Ergebnis |
|------|-----------|------|----------|
| `openproject_browse` | READ_ONLY | `level="my_work"\|"inbox"\|"projects"\|"work_packages"\|"comments"`, `project_id?`, `work_package_id?`, `query?`, `limit`, `offset` | 1 neuer Tool-Slot |
| (kein neues Tool) | READ_ONLY | `fetch` um Präfix `wp:<id>` erweitern: Detailsatz, Beschreibung gekappt, bis zu 10 `file_links` als `file:<id>` | ~20 Bytes |
| (kein neues Tool) | READ_ONLY | `prepare_context`: fünftes Bein, ungelesene Benachrichtigungen plus diese Woche fällige Arbeitspakete, Kappe 3 | 0 Bytes im `tools/list` |

**Budget-Rechnung.** Heute 15712 von 18000 Bytes bei 21 Werkzeugen. Ein Browse-Werkzeug mit
Fünf-Enum und sechs Parametern liegt nach der v1.2-Erfahrung bei 800 bis 1000 Bytes. Ergebnis grob
16700 von 18000. **Das Gate muss nicht angehoben werden**, und das ist ein prüfbarer Satz, der in die
Requirements gehört. 22 Werkzeuge bleiben weit unter der Cursor-Warnschwelle von 40.

## A.5 Vertagt, mit benanntem Auslöser

- `openproject_comment` (CREATE_ONLY, anfügend): Auslöser ist eine konkrete Abnehmerfrage nach dem
  ISV-Call. Vorbedingung: Audit-Log ausgeliefert, damit jeder Kommentar einen Protokolleintrag hat.
  Muss dieselbe Behandlung bekommen wie `talk_send`: eigener Admin-Schalter, Vorprüfung der
  Berechtigung, ausdrückliche Nennung in der Trifecta-Dokumentation.
- `openproject_log_time`: Auslöser ist eine Nachfrage aus dem Store. Vorher klären, ob Zeitbuchungen
  im Zielkundenkreis mitbestimmungspflichtig sind.
- Datei-Link anlegen (Nextcloud-Datei an Arbeitspaket hängen): frühestens v2, gemeinsam mit einer
  belastbaren Aussage dazu, wer die Datei danach sieht.
- Arbeitspaket anlegen: erst wenn Schema-Auflösung (Typ, Pflichtfelder, Status) nachweislich stabil
  ist, sonst rät das Modell.

---

# Teil B: Audit-Log

## B.0 Was ein Audit-Log als Produkt ist

Ein Log-File ist ein Nebenprodukt des Betriebs. Ein Audit-Log ist ein Versprechen, dass eine
bestimmte Frage beantwortbar bleibt. Der Unterschied äussert sich in drei Oberflächen für drei
Publika, und ein Meilenstein, der nur die erste baut, hat kein Feature gebaut:

1. **Für den Nutzer:** "Was hat der Assistent in meinem Namen getan?" Gehört auf die bestehende
   `/connections`-Seite unter Einstellungen/Sicherheit, direkt neben die Verbindung, die es getan hat.
   Das beantwortet nebenbei ein Auskunftsersuchen nach Art. 15 DSGVO und ist der Teil, den kein
   Wettbewerber hat.
2. **Für die Administration und die Revision:** "Wer hat wann über welchen Client welche Daten
   berührt, und was wurde abgelehnt?" Braucht Filter und einen Export, nicht Schönheit.
3. **Für den Betrieb:** strukturierte Zeilen, die eine SIEM- oder Loki-Pipeline einsammelt. In einer
   openDesk-Installation auf Kubernetes ist das der einzige Weg, der wirklich genutzt wird.

## B.1 Der Fragenkatalog, aus dem das Schema folgt

Die Käuferfrage lautet nie "habt ihr Logging", sondern immer eine dieser sechs. Jede Zeile ist ein
Feld, jedes Feld hat einen Grund:

| Frage des Käufers | Feld | Anmerkung |
|-------------------|------|-----------|
| Wer hat gefragt? | `user` (Nextcloud-Nutzerkennung, nicht der Anzeigename) | Der Anzeigename ändert sich, die Kennung nicht |
| Über welchen Client? | `client_id`, `client_name`, `connection_handle`, `transport` | Das ist unser struktureller Vorteil: durch OAuth 2.1 kennen wir den Client namentlich. Ein App-Passwort-Server kann diese Frage nicht beantworten |
| Wann, wie lange? | `ts` (UTC, monoton), `duration_ms` | |
| Was wurde vom System verlangt? | `tool`, `tool_kind` (READ_ONLY / CREATE_ONLY aus der Registry-Annotation) | Die Annotation ist bereits vorhanden und ist die Trennlinie, auf die Prüfer zuerst schauen |
| Welche Daten sind berührt worden? | `resources` (Liste, etwa `file:1234`, `wp:4711`, `talk:<token>`, `mail:<id>`) | Das Purview-Muster (`AccessedResources`). Der teuerste, aber wertvollste Teil des Schemas |
| Was ist herausgekommen? | `outcome` (`ok`, `denied`, `error`, `degraded`), `reason`, `result_bytes`, `truncated` | `denied` mit Grund ist ein Feature, kein Fehlerfall: es beweist, dass die Schutzmechanik greift |

Zwei Felder fehlen bewusst und diese Lücke muss ausgesprochen werden: **wir sehen den Prompt des
Nutzers nicht und wir sehen die Antwort des Modells nicht.** Ein MCP-Server bekommt Werkzeugaufrufe,
keine Konversation. Wer "wer hat was gefragt" im Sinne von Prompt-Text erwartet, wird enttäuscht,
und diese Erwartung muss die Dokumentation zerstören, bevor der Vertrieb sie weckt. Microsoft trennt
genau hier ebenfalls: Audit Standard protokolliert, *dass* eine Copilot-Interaktion stattfand, den
Prompt-Inhalt gibt es erst in Audit Premium.

## B.2 Regulatorische Lage, realistisch statt vollmundig

**EU AI Act.** Art. 12 verpflichtet zu automatischer Protokollierung, Art. 26 Abs. 6 verpflichtet den
Betreiber, diese Protokolle mindestens sechs Monate aufzubewahren, sofern nichts Längeres gilt.
**Beides trifft Hochrisiko-KI-Systeme und deren Betreiber, nicht uns.** Unser Connector ist kein
KI-System, sondern eine Datenschnittstelle. Die ehrliche Formulierung lautet daher: der Audit-Log
liefert dem Betreiber Nachweise, die er für seine eigenen Pflichten braucht, und die einstellbare
Aufbewahrung muss mindestens 180 Tage erreichen können, damit sie für einen solchen Betreiber
überhaupt brauchbar ist. Jede Formulierung in Richtung "AI-Act-konform" ist unbelegt und gehört
nicht in den Store-Text.

**DSGVO.** Hier ist die Lage konkreter und schneidet in beide Richtungen:

- Art. 5 Abs. 2 (Rechenschaftspflicht) und Art. 30 (Verzeichnis von Verarbeitungstätigkeiten): der
  Verantwortliche muss belegen können, welche Verarbeitung stattfindet. Ein Werkzeugprotokoll ist
  dafür ein Baustein, kein Ersatz.
- Art. 15 (Auskunft): "welche meiner Daten hat der Assistent gelesen" ist eine legitime Frage. Die
  Nutzeransicht beantwortet sie ohne Zutun der Administration.
- Art. 32/33: ohne Protokoll lässt sich nach einem Vorfall nicht sagen, was abgeflossen ist.
- **Gegenrichtung:** Der Audit-Log ist selbst eine Verarbeitung personenbezogener Daten. Die
  Orientierungshilfe "Protokollierung" des AK Technik der Datenschutzkonferenz verlangt strikte
  Zweckbindung, Datensparsamkeit, Manipulationsschutz und Löschfristen und hält ausdrücklich fest,
  dass eine Leistungskontrolle von Beschäftigten unzulässig ist. Praktische Faustregel aus derselben
  Ecke: Löschung spätestens zum Ende des Folgejahres.

**Mitbestimmung.** Ein System, das je Beschäftigtem festhält, wann er welchen KI-Client benutzt hat,
ist eine technische Einrichtung, die zur Überwachung von Verhalten und Leistung geeignet ist. In
Behörden greift die Personalvertretung, in Unternehmen der Betriebsrat. **Das ist die wichtigste
Produktkonsequenz des ganzen Bausteins:** ein Audit-Log mit Nutzerstatistiken verlängert die
Beschaffung um Monate, ein Audit-Log mit Zweckbindung, Löschfrist und ohne Auswertungsfunktion ist
verhandelbar. Die Dokumentation muss dem Datenschutzbeauftragten die Argumente fertig liefern.

**BSI IT-Grundschutz OPS.1.1.5.** Der relevante Baustein für Behörden. Er verlangt unter anderem
unveränderte Aufbewahrung der Protokolldaten, zentrale Sammlung und, ab höherem Schutzbedarf,
Integritätssicherung. Daraus folgt für uns: anfügende Ablage ohne Update-Pfad, exportierbares
maschinenlesbares Format für die zentrale Sammlung, und eine Hash-Kette als ehrlicher Mittelweg bei
der Integrität. Nicht daraus folgt: der Begriff "revisionssicher", der eine ganz andere Zusage ist.

## B.3 Feature Landscape Audit-Log

### Table Stakes (Users Expect These)

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Jeder Werkzeugaufruf wird erfasst | Ohne Vollständigkeit ist ein Audit-Log wertlos; eine Lücke entwertet den ganzen Nachweis | LOW-MEDIUM | Genau ein Ort: der `graceful`-Dekorator in `server/__init__.py`, den heute jedes Werkzeug trägt. Ein neuer Dekorator daneben oder darin erfasst alle 21 plus die neuen automatisch, auch künftige |
| Wer, wann, welches Werkzeug, welches Ergebnis | Der Minimalsatz, den jede Auditvorstellung enthält | LOW | Identität und Client stehen im selben `ctx`, aus dem `deps.resolve_clients` heute die Zugangsdaten holt |
| Vom Nextcloud-Loglevel unabhängig | Ein Audit, das bei `loglevel=2` verschwindet, ist kein Audit | LOW | Eigener Kanal, eigener Schalter. Nextcloud macht es genauso: `log_type_audit`, `logfile_audit`, `syslog_tag_audit` getrennt vom Hauptlog |
| Administrativer Ein-/Aus-Schalter | Erwartung an jede Protokollierung; ohne Aus-Schalter ist es eine Zumutung, mit Aus-Schalter eine Entscheidung | LOW | Siebter Declarative-Admin-Wert. Frage für die Planung: Default an oder aus. Empfehlung an, weil ein Audit-Log, den niemand einschaltet, den Store-Text nicht wahr macht |
| Aufbewahrungsfrist mit automatischer Löschung | DSGVO-Löschpflicht und BSI gleichzeitig; ohne Frist ist der Log ein Datenschutzverstoß auf Raten | LOW | Admin-Wert in Tagen, Default 90, Bereich bis mindestens 365 (damit 180 Tage für AI-Act-Betreiber erreichbar sind). Aufräumen im vorhandenen Ablauf für abgelaufene Token, nicht als neuer Dienst |
| Export | Ein Log, das man nicht aus dem System bekommt, ist für Revision und SIEM unbrauchbar. Anthropic exportiert CSV, Purview geht in die zentrale Auswertung | LOW-MEDIUM | CSV plus JSON Lines, mit denselben Filtern wie die Ansicht |
| Administrativer Zugriff | Der Käufer ist die Administration, nicht der Nutzer | **LOW über occ, MEDIUM-HIGH über eine Weboberfläche** | Siehe B.5: `occ mcp_connector:audit` ist der billige und sichere Weg, weil occ per Definition administrativ ist und der Pfad über AppAPI-PublicFunctions durch `purge` bereits bewiesen ist |
| Dokumentiertes Schema | Ohne Feldbeschreibung kann niemand eine SIEM-Regel bauen oder ein Verarbeitungsverzeichnis füllen | LOW | Eine Seite in `docs/`, dreisprachig ist hier nicht nötig, englisch reicht, aber die Datenschutzseite `docs/privacy.md` muss mitziehen |

### Differentiators (Competitive Advantage)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Nutzeransicht "was hat der Assistent in meinem Namen getan"** | Kein Nextcloud-MCP hat das, und kaum ein KI-Produkt hat es. Es verwandelt eine Kontrollmaßnahme in ein Vertrauensangebot und ist der beste Beleg für unser "der Assistent sieht nie mehr als du" | LOW | Zweiter Abschnitt auf der bestehenden `/connections`-Seite. Identität kommt aus dem AppAPI-Header, Formularschutz per HMAC ist vorhanden. Kappe auf die letzten N Einträge, keine Suche |
| **Abgelehnte Aufrufe mit Grund protokollieren** | Der Beweis, dass die Schutzmechanik arbeitet, ist für einen Prüfer mehr wert als die Liste der erfolgreichen Aufrufe. "Verbindung pausiert", "talk_send instanzweit deaktiviert", "Mail ist strikt lesend", "Berechtigung fehlt" | LOW-MEDIUM | Setzt voraus, dass die Ablehnungen unterscheidbar sind. Die vier Autorisierungspunkte der Pause sind bereits benannt |
| **Berührte Ressourcen statt nur Werkzeugnamen** | Beantwortet die eigentliche Frage "welche Daten sind rausgegangen". Microsoft baut dafür `AccessedResources`, weil "Copilot hat gesucht" niemandem hilft | **MEDIUM bis HIGH** | Ehrliche Abstufung: Kennungen aus den *Argumenten* zu ziehen ist billig und deckt jeden Detailabruf ab (`fetch("file:123")`, `wp:4711`). Kennungen aus *Trefferlisten* zu ziehen verlangt je Werkzeug einen Extraktor und kollidiert damit, dass `graceful` bereits die fertig serialisierte Zeichenkette sieht. Empfehlung: v1.5 nur Argumente plus Trefferzahl, Listen-Extraktion vertagen |
| **Verbindungs-Ereignisse im selben Protokoll** | Zugriffsrechte sind für Revisoren wichtiger als einzelne Lesezugriffe: wann wurde eine Verbindung erteilt, pausiert, widerrufen, wann hat ein Administrator einen Schalter umgelegt | LOW | Die Ereignisse existieren bereits als Codepfade in `oauth/connections.py`, `oauth/provider.py` und `exapp/admin_settings.py` |
| **Hash-Kette über die Einträge** | Manipulationsindiz ohne die unhaltbare Zusage "revisionssicher". Ein fehlendes oder geändertes Glied fällt bei der Prüfung auf. BSI OPS.1.1.5 verlangt Integritätsschutz, ohne eine bestimmte Technik vorzuschreiben | LOW | `prev_hash` je Zeile plus ein Prüfbefehl. Kein Signieren, keine externen Zeitstempel, keine Blockchain-Wortwahl |
| **Kritische Ereignisse zusätzlich in Nextclouds Log** | Betreiber schauen in Administration/Logging, nicht in unsere Oberfläche. Ein kleiner, ausgewählter Satz Ereignisse dort macht die App im Alltag sichtbar | LOW | Über `POST /ocs/v1.php/apps/app_api/api/v1/log` (AppAPI). **Wichtige Einschränkung, die geprüft gehört:** das landet im normalen Nextcloud-Log, nicht in `audit.log`. Der PHP-Weg dorthin wäre `OCP\Log\Audit\CriticalActionPerformedEvent` (seit NC 28), den eine ExApp ohne PHP-Anteil nicht auslösen kann. Also: sparsam, nur Verbindungs- und Schalter-Ereignisse, und nicht als "schreibt in Nextclouds Audit-Log" verkaufen |
| **Ein Protokollierungskonzept als Dokument** | Der Datenschutzbeauftragte der Behörde ist der eigentliche Türsteher. Eine Seite, die Zweck, Rechtsgrundlage, Felder, Frist, Empfänger und die ausdrückliche Nicht-Nutzung zur Leistungskontrolle benennt, ist beschaffungswirksamer als jede UI-Politur | LOW | Genau die Struktur der DSK-Orientierungshilfe abarbeiten. Wird ein Baustein für Art. 30 |
| **Inhaltsstufe als bewusster Opt-in** | Purview trennt Standard und Premium, Anthropic trennt Metadaten-Feed und Inhalts-Export. Wir trennen genauso, nur ist bei uns der sparsame Modus der Default | LOW | Ein Admin-Wert `arguments: none | keys | full`. Default `keys`: Parameternamen ja, Werte nein |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| **Argumente und Ergebnisse vollständig speichern** | "Dann sieht man ja alles" | Der Log wird eine zweite, schlechter geschützte Kopie der sensibelsten Daten der Instanz: Mail-Volltexte, Talk-Verläufe, Notizinhalte. Wir haben vier Meilensteine lang argumentiert, dass Mail strikt lesend bleibt, und würden sie hier in eine neue Datenbank schreiben | Metadaten plus Kennungen als Default, Argumentwerte als ausdrücklicher Admin-Opt-in, **Ergebnisinhalte nie** |
| **Nutzungsstatistiken, Bestenlisten, Dashboards** | "Wer nutzt KI am meisten" ist die erste Frage jeder Führungskraft | Genau die Auswertung, die die DSK als unzulässige Leistungskontrolle benennt und die Mitbestimmung auslöst. Verlängert die Beschaffung, statt sie zu gewinnen | Gar nicht. Aggregation gehört, wenn überhaupt, in eine anonymisierte Betriebskennzahl ohne Nutzerbezug, und die braucht v1.5 nicht |
| **Ein MCP-Werkzeug `audit_search`** | "Der Assistent soll sein eigenes Protokoll lesen können" | Rechte-Umkehr: das Modell bekäme Zugriff auf die Aktivität anderer Nutzer und auf eine Datenquelle, die es beeinflussen kann. Außerdem eine perfekte Prompt-Injection-Beute | Der Audit-Log ist ausschließlich Mensch-Oberfläche. Kein Tool-Slot, keine Ausnahme |
| **"Revisionssicher", WORM, Signaturen, Blockchain** | Klingt nach Enterprise | Revisionssicherheit ist eine Zusage über Ablage, Aufbewahrung und Organisation, die wir in einem Container-Volume nicht halten können. Eine falsche Zusage im Store-Text ist teurer als ein fehlendes Feature | Hash-Kette plus die Aussage "anfügend, kein Änderungspfad im Code, Prüfbefehl liegt bei" |
| **Alarmierung, Anomalie-Erkennung, Live-Streaming, Webhooks** | Der Markt der MCP-Gateways verkauft genau das | Das ist ein SIEM. Wir sind ein Solo-Projekt und würden ein zweites Produkt bauen | JSON Lines exportieren und die vorhandene Pipeline des Betreibers gewinnen lassen |
| **Unbegrenzte Aufbewahrung als Default** | "Sicher ist sicher" | Verstößt gegen Speicherbegrenzung; ein Log ohne Frist ist bei der Prüfung ein Befund | Default 90 Tage, konfigurierbar, dokumentiert |
| **Audit-Daten beim Trennen der Verbindung mitlöschen** | Wirkt konsequent zum bestehenden Purge | Dann kann jeder Nutzer seine eigene Spur beseitigen, indem er die Verbindung beendet. Ein Audit, den der Protokollierte löschen kann, ist keiner | Klare, dokumentierte Regel (B.4): Trennen löscht nicht, Löschfrist löscht, Nutzerlöschung löscht, Instanz-Purge löscht |
| **Prompt-Text protokollieren** | Erwartungshaltung aus Copilot-Vergleichen | Wir sehen ihn nicht. Ihn zu versprechen wäre schlicht falsch | In der Dokumentation ausdrücklich als Grenze benennen |
| **Eigene Log-Datei im Container als einziger Ausgabeweg** | Am einfachsten | In Kubernetes und damit in openDesk ist ein Pfad im Container nicht das, was eingesammelt wird | Strukturierte Zeilen nach stdout als Pflicht, Datei als Option |
| **Den Audit-Log über die Declarative Admin-Settings anzeigen** | Die Oberfläche existiert schon | Declarative Settings sind für Konfigurationswerte gedacht, nicht für eine gefilterte Tabelle mit hunderten Zeilen | occ für Export, eigene Seite später, falls Nachfrage besteht |

## B.4 Die Regel, die geschrieben werden muss: Purge gegen Aufbewahrung

Der bestehende `occ mcp_connector:purge` löscht bewusst alles. Der Audit-Log darf sich nicht
stillschweigend daran hängen, denn dann kollidieren zwei berechtigte Anforderungen. Vorschlag als
Entscheidungsvorlage, weil das eine Owner-Entscheidung ist:

| Ereignis | Audit-Einträge | Begründung |
|----------|----------------|------------|
| Nutzer beendet eine Verbindung | **bleiben** | Sonst löscht der Protokollierte seine eigene Spur |
| Nutzer pausiert | bleiben | Kein Löschanlass |
| Aufbewahrungsfrist abgelaufen | werden gelöscht | Speicherbegrenzung |
| Nutzer wird in Nextcloud gelöscht | seine Einträge werden gelöscht | Es gibt keinen Betroffenen mehr, dessen Verhalten belegt werden müsste |
| Administrator ruft `purge` / App wird deinstalliert | alles wird gelöscht | Bestehendes Versprechen "Deinstallation entfernt alle Daten", das nicht aufgeweicht werden darf |

Die letzte Zeile bedeutet: der Audit-Log überlebt eine Deinstallation nicht. Wer ihn aufbewahren
will, exportiert vorher. Das gehört wörtlich in die Dokumentation, sonst ist es eine böse
Überraschung.

## B.5 Warum occ und nicht sofort eine Weboberfläche

Die administrative Ansicht ist der Table Stake, und sie ist zugleich der teuerste Teil, weil eine
ExApp-Seite selbst prüfen müsste, ob der aufrufende Nutzer Administrator ist. Die AppAPI liefert die
Nutzerkennung, eine belastbare Admin-Eigenschaft daraus abzuleiten ist eine offene Frage und wäre
eine neue, sicherheitsrelevante Fläche.

`occ mcp_connector:audit --since ... --user ... --tool ... --format csv|jsonl` umgeht das
vollständig: occ ist per Definition administrativ, der Weg über AppAPI-PublicFunctions ist durch
`purge` bereits gebaut und bewiesen, es kommt keine deklarierte Route und damit keine
Internet-Angriffsfläche hinzu, und Betriebspersonal in Behörden lebt ohnehin in occ. Eine
Weboberfläche für Administratoren ist danach ein Aufsatz mit Nachfrage-Auslöser, kein
Meilenstein-Risiko.

---

## Feature Dependencies

```
OpenProject-Familie
    └──requires──> Per-Nutzer-Zugang zu OpenProject (heute NICHT vorhanden)
    │                  ├── OAuth 2.0 Authorization Code gegen OpenProject, Scope api_v3  (Empfehlung)
    │                  ├── OIDC-Token-Tausch über den openDesk-IdP  (v2, Enterprise, ISV-Call-Frage)
    │                  └── persönlicher API-Token  (abgelehnt, Positionsbruch)
    └──requires──> Admin-Wert "OpenProject-Basisadresse" + Aus-Schalter (6. Declarative-Wert)
    └──requires──> Verschlüsselte Ablage für Refresh-Tokens  (vorhanden: oauth/store.py, oauth/crypto.py)
    └──requires──> Ablauf zum Trennen/Purgen der OpenProject-Verbindung  (vorhanden: exapp/purge.py, erweitern)

openproject_browse(level="my_work"|"inbox"|"projects")
    └──enables───> openproject_browse(level="work_packages"|"comments")   (Projekt- und Paketkennungen)
    └──enables───> fetch("wp:<id>")                                        (Kennung aus der Liste, nie aus Text)
    └──enables───> prepare_context openDesk-Bein                           (dieselben zwei Requests)

fetch("wp:<id>")
    └──requires──> file_links-Auflösung
    └──enables───> fetch("file:<id>")   (vorhanden seit v1.0: die Kette Arbeitspaket zu Dokument)

Audit-Kern
    └──requires──> genau ein Aufrufpunkt für alle Werkzeuge  (VORHANDEN: graceful in server/__init__.py)
    └──requires──> Identität und Client im ctx                 (VORHANDEN: deps.resolve_credentials)
    └──requires──> Werkzeug-Annotation READ_ONLY/CREATE_ONLY    (VORHANDEN: server/__init__.py)
    └──requires──> persistente Ablage                            (VORHANDEN: SQLite/WAL in oauth/store.py)
    └──enables───> Nutzeransicht auf /connections    (VORHANDEN als Seite: oauth/connections.py)
    └──enables───> occ mcp_connector:audit           (VORHANDEN als Pfad: exapp/purge.py)
    └──enables───> JSON-Lines nach stdout
    └──enables───> Hash-Kette

Audit-Aufbewahrung ──konfliktiert mit──> purge/Deinstallation  (Regel B.4 entscheidet)
Audit-Nutzeransicht ──konfliktiert mit──> "Trennen löscht alles"  (Regel B.4 entscheidet)
Audit-Argumentwerte ──konfliktiert mit──> "Mail ist strikt lesend"  (Default keys, nie full)

Store-Text EN/DE/FR ──requires──> Audit-Log ausgeliefert
    (heute steht dort dreisprachig: geplant, existiert in keiner Form.
     Die Zeile wird in dem Moment falsch, in dem der Code live geht.)

Audit-Log ──enhances──> jeder künftige Schreibpfad
    (openproject_comment, Mail-Entwürfe: die Frage "wer hat das geschrieben"
     ist dann vorab beantwortet)
```

### Dependency Notes

- **Der teuerste Teil von OpenProject ist nicht OpenProject.** Die Werkzeuge sind ein Nachmittag,
  der Zugang ist der Meilenstein. Ohne beantwortete Auth-Frage gibt es keine Familie, deshalb ist der
  zeitboxierte Spike aus PROJECT.md richtig geschnitten und muss vor jedem Toolcode stehen.
- **Der Audit-Log hat fast keine Abhängigkeiten und ist deshalb die sichere Hälfte des
  Meilensteins.** Alle sechs Bauteile existieren. Falls der OpenProject-Spike ein Auth-Hindernis
  findet, das den Meilenstein sprengt, trägt der Audit-Log v1.5 allein, genau wie PROJECT.md es
  vorsieht. Die beiden Bausteine sollten deshalb **unabhängige Phasen** sein, nicht ineinander
  verzahnt.
- **Reihenfolge innerhalb OpenProject:** `my_work` und `inbox` zuerst (ein Request, sofort sichtbarer
  Nutzen), dann `projects`/`work_packages`/`comments`, dann `fetch("wp:")` mit file_links, zuletzt das
  `prepare_context`-Bein. Der Datei-Sprung ist der Differenzierer, aber er hängt an einer
  eingerichteten Nextcloud-OpenProject-Integration und ist deshalb der richtige Kandidat zum Streichen,
  wenn der Zeitplan kippt.
- **Reihenfolge innerhalb Audit:** Kern und Schema zuerst, danach Aufbewahrung und stdout (beide
  billig und ohne die andere Reihenfolge unvollständig), dann occ-Export, dann Nutzeransicht,
  Hash-Kette und Dokumentation. Der Store-Text ist Teil derselben Phase wie das Feature, nicht danach.
- **Die Annotation ist die Trennlinie im Protokoll.** `READ_ONLY` und `CREATE_ONLY` liegen bereits in
  der Registry. Sie in jeden Eintrag zu schreiben kostet nichts und macht die eine Auswertung möglich,
  die jeder Prüfer als erstes will: zeig mir alle Schreibvorgänge.
- **Wenn OpenProject-Schreiben je kommt, kommt es nach dem Audit-Log**, nicht davor. Diese
  Reihenfolge ist ein Verkaufsargument, kein Zufall.

## MVP Definition

### Launch With (v1.5)

**OpenProject (nur wenn der Spike den Zugang trägt):**
- [ ] Auth-Weg entschieden und einmal live bewiesen: ein Nutzer verbindet OpenProject über unsere
      Seite, ein Werkzeug antwortet mit seinen echten Daten, das Trennen nimmt den Zugang mit
- [ ] `openproject_browse` mit `my_work` und `inbox`: Filter `assignee=me` plus `status=o`,
      ungelesene Benachrichtigungen mit `reason`, Projektion statt HAL, `select` wo unterstützt
- [ ] `openproject_browse` mit `projects`, `work_packages` (inklusive Volltext über `**`) und
      `comments` (Systemeinträge per Default heraus)
- [ ] `fetch` um `wp:<id>` erweitert, inklusive bis zu 10 `file_links` als auflösbare `file:<id>`
- [ ] Drei unterscheidbare Fehlersätze (nicht konfiguriert, nicht verbunden, nicht erreichbar), je
      mit konkretem nächsten Schritt
- [ ] Instanzweiter Aus-Schalter als sechster Admin-Wert, Default aus
- [ ] Lesen ohne Nebenwirkung als Regressionstest: nach `inbox` ist `readIAN` unverändert
- [ ] Budget nachgemessen, Gate bleibt bei 18000 (Nachweiszeile im Skript)
- [ ] Kein Schreibpfad im OpenProject-Client, per AST-Gate festgenagelt wie bei Mail

**Audit-Log (trägt den Meilenstein auch allein):**
- [ ] Ein Aufrufpunkt erfasst jeden Werkzeugaufruf: `ts`, `user`, `client_id`, `client_name`,
      `connection_handle`, `transport`, `tool`, `tool_kind`, `outcome`, `reason`, `duration_ms`,
      `result_bytes`, `truncated`, `resources` (aus den Argumenten)
- [ ] Abgelehnte Aufrufe werden mit Grund erfasst, nicht nur erfolgreiche
- [ ] Verbindungs- und Admin-Ereignisse im selben Protokoll (erteilt, pausiert, fortgesetzt,
      widerrufen, Schalter umgelegt)
- [ ] Argumentwerte per Default **nicht** gespeichert (`arguments=keys`), `full` als bewusster
      Admin-Opt-in, Ergebnisinhalte in keiner Stufe
- [ ] Aufbewahrungsfrist als Admin-Wert, Default 90 Tage, mindestens 365 erreichbar, automatische
      Löschung im vorhandenen Aufräumlauf
- [ ] Anfügende Ablage ohne Update-Pfad, Hash-Kette über die Einträge plus Prüfbefehl
- [ ] `occ mcp_connector:audit` mit Filtern und Ausgabe als CSV und JSON Lines
- [ ] Strukturierte JSON-Zeilen nach stdout, unabhängig vom Nextcloud-Loglevel
- [ ] Nutzeransicht "letzte Aktivität dieser Verbindung" auf der bestehenden `/connections`-Seite
- [ ] Purge- und Aufbewahrungsregel entschieden, implementiert und dokumentiert (B.4)
- [ ] `docs/`-Seite mit Schema, Zweck, Frist, Empfängern und der ausdrücklichen Aussage, dass keine
      Auswertung zur Leistungskontrolle vorgesehen ist; `docs/privacy.md` zieht mit
- [ ] **Store-Beschreibung und READMEs EN/DE/FR im selben Release angepasst:** Audit-Log von
      "geplant" nach "vorhanden, mit diesen Grenzen", Gruppen-Policies und SSO bleiben "geplant".
      Verbotene Wörter im neuen Text: revisionssicher, AI-Act-konform, DSGVO-konform, SIEM-zertifiziert

### Add After Validation (v1.x)

- [ ] `prepare_context`-Bein für openDesk: Auslöser, sobald `openproject_browse` stabil ist und die
      Latenz gemessen wurde; muss abschaltbar sein
- [ ] Berührte Ressourcen auch aus Trefferlisten statt nur aus Argumenten: Auslöser ist eine
      Nachfrage, die an der Granularität scheitert
- [ ] Administrative Weboberfläche für den Audit-Log: Auslöser ist eine Nachfrage, die occ nicht
      erfüllt; verlangt vorher eine belastbare Admin-Prüfung in der ExApp
- [ ] `openproject_comment` hinter eigenem Admin-Schalter: Auslöser ist eine konkrete Abnehmerfrage
      nach dem ISV-Call
- [ ] Zeiteintrag anlegen: Auslöser ist Store-Feedback plus geklärte Mitbestimmungsfrage
- [ ] Kritische Ereignisse zusätzlich in Nextclouds Log über die AppAPI-Log-Route: Auslöser ist die
      Messung, wie störend das im Alltag ist

### Future Consideration (v2+)

- [ ] OIDC-Token-Tausch über den openDesk-IdP statt eigener OAuth-Anwendung: braucht eine
      openDesk-Instanz und ist eine Frage für den ISV-Call, keine Bauentscheidung
- [ ] Gruppen-Policies (welche Gruppe darf welche Werkzeugfamilie): der zweite der drei
      Enterprise-Punkte aus dem Store-Text, eigener Meilenstein. Der Audit-Log ist die Vorbedingung,
      weil eine Policy ohne Nachweis wertlos ist
- [ ] Datei-Link von Nextcloud nach OpenProject anlegen: erst mit belastbarer Aussage zur Sichtbarkeit
- [ ] Arbeitspakete anlegen oder ändern: nur mit Bestätigungs-Infrastruktur (Elicitation), also
      frühestens wenn Überschreiben konzeptionell überhaupt erlaubt wird
- [ ] Weitere openDesk-Komponenten (XWiki, Matrix, OX): v2.0, eigener Meilenstein
- [ ] Anonymisierte Betriebskennzahlen ohne Nutzerbezug: nur falls ein Kunde danach fragt, und
      strikt getrennt vom Audit-Log

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Audit-Kern am `graceful`-Aufrufpunkt | HIGH | LOW-MEDIUM | P1 |
| Aufbewahrungsfrist mit automatischer Löschung | HIGH (ohne sie ist das Feature ein Befund) | LOW | P1 |
| Abgelehnte Aufrufe mit Grund | HIGH | LOW-MEDIUM | P1 |
| Verbindungs- und Admin-Ereignisse im Protokoll | MEDIUM-HIGH | LOW | P1 |
| `occ mcp_connector:audit` mit CSV/JSONL | HIGH | LOW-MEDIUM | P1 |
| JSON-Zeilen nach stdout | MEDIUM-HIGH (in openDesk HIGH) | LOW | P1 |
| Purge-/Aufbewahrungsregel entschieden und dokumentiert | HIGH | LOW | P1 |
| Store-Text und READMEs dreisprachig nachgezogen | HIGH (sonst wird eine wahre Aussage falsch) | LOW | P1 |
| Protokollierungskonzept-Seite | HIGH beim Käufer, LOW beim Nutzer | LOW | P1 |
| Nutzeransicht auf `/connections` | HIGH (Differenzierer) | LOW | P1 |
| Hash-Kette plus Prüfbefehl | MEDIUM | LOW | P1 |
| OpenProject-Auth einmal live bewiesen | HIGH (Voraussetzung von allem) | **HIGH** | P1 |
| `openproject_browse` `my_work` und `inbox` | HIGH | MEDIUM | P1 |
| `openproject_browse` `projects`, `work_packages`, `comments` | MEDIUM-HIGH | MEDIUM | P1 |
| `fetch("wp:<id>")` mit file_links | HIGH (Differenzierer) | MEDIUM | P1 |
| Instanzweiter Aus-Schalter OpenProject | MEDIUM | LOW | P1 |
| AST-Gate gegen OpenProject-Schreibaufrufe | MEDIUM | LOW | P1 |
| Argument-Inhaltsstufe als Admin-Opt-in | MEDIUM | LOW | P2 |
| `prepare_context` openDesk-Bein | HIGH | MEDIUM | P2 |
| Ressourcen aus Trefferlisten | MEDIUM | MEDIUM-HIGH | P2 |
| Kritische Ereignisse in Nextclouds Log | LOW-MEDIUM | LOW | P2 |
| Admin-Weboberfläche für den Audit-Log | MEDIUM | MEDIUM-HIGH | P3 |
| `openproject_comment` | MEDIUM | LOW-MEDIUM | P3 |
| Zeiteintrag anlegen | LOW-MEDIUM | MEDIUM | P3 |

## Competitor Feature Analysis

### OpenProject

| Aspekt | OpenProject MCP (offiziell) | jtauschl/openproject-ce-mcp | AndyEverything, brunofin, weitere | Unser Ansatz |
|--------|------------------------------|------------------------------|-----------------------------------|--------------|
| Umfang | Read-only, Werkzeuge einzeln vom Administrator abschaltbar, drei Antwortformate zur Token-Steuerung | 132 Werkzeuge, 106 ohne Admin-Schreibpfade, volle v3-Abdeckung | Voller CRUD inklusive Löschen, Anhängen, Watchern, Relationen | 1 Werkzeug mit fünf Ebenen plus eine `fetch`-Id-Art, rein lesend |
| Verfügbarkeit | **Enterprise-Add-on ab Professional**, Endpunkt `/mcp` der eigenen Instanz | Community Edition, selbst betrieben | Community Edition, selbst betrieben | ExApp im Nextcloud-Store, ein Klick, jede Edition |
| Anmeldung | Persönliches API-Token oder OAuth 2.0 mit Scope `mcp`, vertraulicher Client | API-Token in der Umgebung | API-Token in der Umgebung | OAuth 2.1 zum Client (vorhanden) plus OAuth 2.0 zu OpenProject, per Nutzer in der Nextcloud-Oberfläche verwaltet |
| Schreiben | Heute keins, laut Doku künftig möglich | Preview-then-confirm mit `confirm=true`, nicht abschaltbar | Direktes Schreiben, teils mit `AUTO_CONFIRM`-Ausweg | Keins in v1.5, und Löschen und Überschreiben nie |
| Zusammen mit Nextcloud | Zweiter Server, zweite Autorisierung | Zweiter Server | Zweiter Server | **Ein Endpunkt, eine Zustimmung, `wp:` führt nach `file:`** |

**Ehrliche Einordnung:** In einer openDesk-Enterprise-Installation existiert der Hersteller-Server,
und er wird für reine OpenProject-Fragen besser sein als wir, weil er das Datenmodell kennt. Unsere
Aussage muss deshalb die Bündelung sein, nicht die Abdeckung. Auf der Community Edition sind wir der
einzige Weg mit ordentlicher Anmeldung.

### Audit-Log

| Aspekt | nextcloud/context_agent | cbcoutinho/nextcloud-mcp-server | Microsoft Purview (Copilot) | Anthropic Compliance API | Unser Ansatz |
|--------|--------------------------|----------------------------------|------------------------------|---------------------------|--------------|
| Protokoll über Werkzeugaufrufe | Nicht dokumentiert | Nicht dokumentiert | Ja, `CopilotInteraction` und verwandte Satzarten | Ja, rund 30 typisierte Ereignisse | Ja, jeder Aufruf inklusive Ablehnungen |
| Berührte Ressourcen | entfällt | entfällt | `AccessedResources` mit Datei-Ids, Site-URLs, Namen | Auf Konversations- und Datei-Ebene | Kennungen aus Argumenten in v1.5, Trefferlisten später |
| Inhalt (Prompt, Antwort) | entfällt | entfällt | Nur in Audit Premium | Metadaten-Feed ohne Inhalt | Nie Ergebnisinhalte, Argumentwerte nur als Opt-in, Prompt sehen wir nicht |
| Aufbewahrung | entfällt | entfällt | Nach Lizenz gestaffelt | Metadaten sechs Jahre, CSV-Export 180 Tage | Konfigurierbar, Default 90 Tage |
| Export | entfällt | entfällt | In die zentrale Auswertung | CSV-Export und API | CSV und JSON Lines über occ, plus stdout für SIEM |
| Sicht für die betroffene Person | entfällt | entfällt | Nein | Nein | **Ja, auf der eigenen Verbindungsseite** |

Der Befund "nicht dokumentiert" beruht auf den READMEs beider Projekte, nicht auf einer
Quellcode-Durchsicht. Als Produktaussage ist die README die richtige Messlatte, als technische
Behauptung wäre sie zu schwach.

## Antwort-Größen-Leitplanken (für die Phasenplanung)

| Antwort | API-Default | Vorschlag | Begründung |
|---------|-------------|-----------|------------|
| `my_work` | `pageSize` frei | Default 25, Max 50, `total` mitliefern | Ein Arbeitspaket in HAL ist vierstellig in Tokens |
| `inbox` | 20 | Default 15, Max 30, nur ungelesene, `reason` immer | Posteingänge laufen dreistellig voll |
| `projects` | frei | Max 50, projiziert auf vier Felder | Reines Vokabular |
| `comments` | Collection | Default 10, Max 25, Systemeinträge heraus, Textkappe je Eintrag | Wie bei Talk: einzelne Beiträge können sehr lang sein |
| `fetch("wp:<id>")` | ganzes HAL-Objekt | Bestehende `fetch`-Byte-Kappe, Beschreibung gekappt, `file_links` auf 10 | Beschreibungen sind ganze Dokumente |
| `prepare_context` openDesk-Bein | (neu) | Max 3 Einträge, eigenes Zeitbudget, eigener `degraded`-Eintrag | Das Bündel muss vorhersagbar bleiben |
| Audit-Eintrag | (neu) | Feste Feldliste, `resources` auf 20 Einträge gekappt, keine Freitextfelder ohne Kappe | Ein Audit-Satz muss eine Zeile bleiben, sonst ist JSON Lines nutzlos |
| Nutzeransicht `/connections` | (neu) | Letzte 25 Einträge je Verbindung, keine Suche, keine Aggregation | Transparenz, nicht Auswertung |

## Sources

**OpenProject**
- openproject.org `docs/system-admin-guide/integrations/mcp-server` (offizieller MCP-Server:
  read-only, Enterprise-Add-on ab Professional, Endpunkt `/mcp`, Anmeldung über persönliches
  API-Token oder OAuth 2.0 mit Scope `mcp` als vertraulicher Client, einzelne Werkzeuge abschaltbar,
  drei Antwortformate) [HIGH]
- openproject.org `docs/api/endpoints/work-packages`, `docs/api/filters`, `docs/api/signaling`,
  `docs/api/endpoints/notifications`, `docs/api/endpoints/time-entries`,
  `docs/api/endpoints/file-links`, `docs/api/endpoints/queries` (Endpunkte, Filter-Syntax und
  Operatoren `=`, `!`, `o`, `c`, `**`, `t+`, `t-`; `select`-Signaling mit Wildcard und atomaren
  Links; Notification-Filter `readIAN`, `reason`, `project`; Time-Entry-Filter und POST-Pflichtfelder;
  `file_links` mit `originData.id/name/mimeType/size`) [HIGH, teils über Context7 `/websites/openproject`]
- opf/openproject Quellcode `app/models/queries/work_packages/filter/principal_base_filter.rb`,
  `.../me_value_filter_mixin.rb`, `app/models/queries/filters/shared/me_value_filter.rb`,
  `app/models/queries/filters/me_value.rb` (`KEY = "me"`, Ersetzung durch die aktuelle Nutzerkennung:
  der Beleg, dass `values: ["me"]` funktioniert) [HIGH]
- openproject.org `docs/system-admin-guide/authentication/oauth-applications` (Scope `api_v3` ist der
  Default, wenn keiner gewählt wird) [HIGH]
- openproject.org `docs/system-admin-guide/integrations/nextcloud/` und `.../two-way-oauth2`,
  `.../oidc-sso` (Zwei-Wege-OAuth funktioniert mit jeder Installation, OIDC-SSO über einen gemeinsamen
  IdP ist Enterprise-Add-on) [HIGH]
- github.com/jtauschl/openproject-ce-mcp README (132 Werkzeuge, 106 ohne Admin-Schreibpfade,
  preview-then-confirm ohne Umgehung, bis zu −99 Prozent Tokens gegenüber roher HAL-Antwort) [HIGH]
- github.com/AndyEverything/openproject-mcp-server, github.com/brunofin/openproject-mcp,
  github.com/jtauschl/openproject-mcp (voller CRUD inklusive Löschen, Anhänge, Watcher, Relationen;
  `AUTO_CONFIRM_WRITE`-Ausweg) [MEDIUM, Übersichtsebene]
- docs.opendesk.eu `operations/enterprise` und `operations/architecture`, openproject.org
  `blog/opendesk-1-0` (OpenProject ist die Projektmanagement-Komponente von openDesk, zentrale
  Anmeldung über Keycloak/Nubus, Enterprise-Artefakte unter `/zendis`, OpenProject braucht eine
  domänenspezifische Enterprise-Lizenz für den Enterprise-Funktionsumfang) [MEDIUM-HIGH]

**Audit-Log**
- artificialintelligenceact.eu Art. 12 (Aufzeichnungspflichten für Hochrisiko-Systeme) und
  ai-act-service-desk.ec.europa.eu Art. 26 (Betreiberpflichten, Abs. 6: Protokolle mindestens sechs
  Monate, längere Fristen gehen vor) [HIGH für den Wortlaut, MEDIUM für die Auslegung, dass uns die
  Pflicht nicht selbst trifft]
- Orientierungshilfe "Protokollierung" des AK Technik der Konferenz der Datenschutzbeauftragten
  (baden-wuerttemberg.datenschutz.de) sowie SDM-Baustein "Protokollieren" (datenschutz-mv.de):
  strikte Zweckbindung, Datensparsamkeit, Manipulationsschutz, Löschfristen, Leistungskontrolle
  unzulässig [MEDIUM-HIGH]
- BSI IT-Grundschutz-Baustein OPS.1.1.5 Protokollierung (Edition 2023) und BSI-Mindeststandard
  Protokollierung und Detektion (unveränderte Aufbewahrung, zentrale Sammlung, Integritätssicherung
  bei höherem Schutzbedarf) [MEDIUM-HIGH, Anforderungsebene]
- personalrat-online.de zu technischen Kontrolleinrichtungen im BPersVG (Mitbestimmung bei
  Einrichtungen, die zur Überwachung von Verhalten oder Leistung geeignet sind) [MEDIUM]
- docs.nextcloud.com Administration Manual, Logging (`log_type_audit`, `logfile_audit`,
  `syslog_tag_audit`, eigene `audit.log` in `data/`, Anzeige über die logreader-App) [HIGH]
- docs.nextcloud.com Developer Manual, Logging (`OCP\Log\Audit\CriticalActionPerformedEvent`, seit
  NC 28, dritter Parameter `obfuscateParameters`) [HIGH]
- docs.nextcloud.com Developer Manual, ExApp `POST /ocs/v1.php/apps/app_api/api/v1/log` (PSR-3-Level,
  Kontext ist die App-Id; die Doku sagt **nicht**, dass Einträge in `audit.log` landen, und es gibt
  keine audit-spezifische ExApp-Schnittstelle) [HIGH für die Existenz, MEDIUM für die Zielsenke, die
  im Spike gemessen gehört]
- learn.microsoft.com `purview/audit-copilot` und `purview/ai-m365-copilot` (`AccessedResources`,
  `Messages` mit `IsPrompt`, `Contexts`, Satzarten `CopilotInteraction`, `AIAppInteraction`; Standard
  protokolliert das Stattfinden, Premium den Prompt-Inhalt) [HIGH]
- support.claude.com "Access audit logs" und platform.claude.com "Compliance API" (rund 30
  typisierte Ereignisse, CSV-Export über 180 Tage ohne Inhalt, Activity Feed mit langer Aufbewahrung,
  getrennte Zugangsschlüssel) [MEDIUM-HIGH]
- MCP-Gateway-Anbieter (MintMCP, TrueFoundry, Lunar, Obot, Authzed) zum erwarteten Feldsatz je
  Werkzeugaufruf: Zeitstempel, Identität, Server, Werkzeug, Eingabeparameter, Ergebniszusammenfassung,
  Policy-Entscheidung mit Begründung, Laufzeit; und zur Feststellung, dass MCP selbst keine
  persistente Protokollierung vorsieht [MEDIUM]
- github.com/cbcoutinho/nextcloud-mcp-server README und github.com/nextcloud/context_agent README:
  kein dokumentiertes Audit- oder Protokollierungs-Feature [MEDIUM, Abwesenheit in der README]

**Eigener Code (Abhängigkeitsbelege)**
- `src/mcp_connector/server/__init__.py` (`graceful` liegt auf jedem Werkzeug, `READ_ONLY` und
  `CREATE_ONLY` als Annotationen, `compact` als Serialisierung, `_load_registrations` über `reg_*`)
  [HIGH]
- `src/mcp_connector/oauth/store.py` (SQLite mit WAL, `BEGIN IMMEDIATE`, verschlüsselte Geheimnisse,
  zwei Prozesse auf einer Datei als unterstützter Fall) [HIGH]
- `src/mcp_connector/oauth/connections.py` (servergerenderte Nutzerseite, Identität aus dem
  AppAPI-Header, HMAC-Formularschutz) [HIGH]
- `src/mcp_connector/exapp/purge.py` (occ über AppAPI-PublicFunctions ohne deklarierte Route, die
  Vorlage für einen Audit-Export-Befehl; zugleich die Stelle, an der die Aufbewahrungsregel B.4
  wirksam wird) [HIGH]
- `src/mcp_connector/exapp/admin_settings.py`, `src/mcp_connector/exapp/config_values.py`
  (Declarative Admin-Settings als Ort für die neuen Werte) [HIGH]
- `scripts/check_tool_budget.py` und PROJECT.md (15712 von 18000 Bytes bei 21 Werkzeugen: die Basis
  der Budget-Rechnung in A.4) [HIGH]

---
*Feature research for: v1.5 Vorlauf openDesk (OpenProject lesend, Audit-Log als erster
Enterprise-Baustein)*
*Researched: 2026-08-28*
