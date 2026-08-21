---
phase: 08-erreichbarkeits-spike-und-tables
plan: 05
subsystem: testing
tags: [tables, integration-test, appapi, impersonation, permission-fidelity, harp, ocs]

# Dependency graph
requires:
  - phase: 08-erreichbarkeits-spike-und-tables
    provides: "tables 2.2.2 in beiden Topologien plus Bootstrap-Idempotenz (Plan 08-01), tools/tables.py mit browse und create_row (Plan 08-03), Registrierung und Gates (Plan 08-04)"
  - phase: 02-exapp-shell
    provides: "HaRP-Testtopologie, vierter Credential-Modus appapi, test_exapp_dav_matrix.py als Vorbild fuer den Credential-Bau"
  - phase: 01-server-kern
    provides: "test_deck_roundtrip.py als Vorbild, live_env und exapp_env in tests/conftest.py, ocs-Parser und Fehlersaetze"
provides:
  - "Live-Nachweis der Tables-Familie gegen Nextcloud 34.0.3 mit Tables 2.2.2: Zeile ueber Spaltentitel anlegen, ueber browse(level=rows) zurueckelesen, erzwungenes limit in der echten URL, rowsCount und can_create aus der echten Antwort"
  - "Annahme A2 ist gemessen statt angenommen: Auswahl-Label und ISO-Datum gehen ohne eigene Umformung durch"
  - "Annahme A6 ist bestaetigt: der Einzeltabellenaufruf traegt rowsCount und onSharePermissions"
  - "Korrektur K5 live belegt: can_create ist True fuer die eigene Tabelle, obwohl onSharePermissions nur read meldet"
  - "Zwei-Konten-Negativbeweis fuer Tables (T-08-26): kein Listen, kein Inhalt bei bekannter Id, kein Schreibvorgang, Zeilenzahl des Eigentuemers unveraendert"
  - "Messbefund fuer Phase 10 und 11: Nextcloud beantwortet den Zugriff auf eine fremde Tabelle mit 404 und leerem Koerper, nicht mit 403"
affects: [09-talk, 10-mail-strikt-lesend, 11-buendelung-budget-release]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Messwerte eines gruenen Integrationslaufs werden per warnings.warn sichtbar gemacht, weil ein print nur im roten Fall erscheint"
    - "Ein Wertformen-Probelauf statt einer Behauptung: die Attempt-Kette schreibt zuerst die vollstaendige Wertmenge und faellt spaltenweise zurueck, damit ein 400 die Spalte benennt"
    - "Zwei Messschichten in einer Datei, beide im Docstring benannt: Kettenfaelle ueber HaRP mit App-Passwort, Tables-Faelle auf der Impersonation-Naht mit MODE_APPAPI"
    - "Testgeruest-POSTs ueber ocs_post mit creds.auth(), damit auch das Geruest kein Nutzerpasswort braucht"

key-files:
  created:
    - tests/integration/test_tables_roundtrip.py
  modified:
    - tests/integration/test_permission_fidelity_exapp.py
    - src/mcp_connector/nextcloud/clients/ocs.py
    - tests/unit/test_tables_client.py
    - CHANGELOG.md

key-decisions:
  - "Die Spalten des Testgeruests entstehen ueber die typisierten api/2-Routen (columns/text, columns/number, columns/selection, columns/datetime) und nicht ueber den vom Plan genannten v1-Pfad: die Schreibrouten fuer Spalten liegen unter api/2 in dieser Form, gemessen an der openapi.json der laufenden App"
  - "Die Textspalte des Geruests traegt subtype line, weil Tables die Business-Klasse aus type plus subtype aufloest und TextBusiness nicht existiert: eine Textspalte ohne subtype macht jeden Lese- und Schreibzugriff auf die ganze Tabelle zu einem 500"
  - "Ein Status ab 400 ohne JSON-Koerper wird an seinem Status erklaert und nicht als Loginseite: die echte 404-Antwort auf eine unbekannte Tabelle traegt Content-Type text/html und einen leeren Koerper, und der alte Hinweis schickte das Modell zum App-Passwort statt zur Id"
  - "Der Zwei-Konten-Beweis fuer Tables laeuft eine Schicht unter den bestehenden Kettenfaellen, auf der Impersonation-Naht mit zwei Credential-Objekten im Modus appapi; die Grenze ist im Modul-Docstring benannt statt verschwiegen, weil Tabelle und Spalte ohnehin einen Direktaufruf brauchen"
  - "Der Roundtrip laeuft ueber die Zeilen paginiert statt mit einem breiten Lesen: die Testtabelle ueberlebt jeden Lauf, und nur der Cursor findet die eigene Zeile spaeter wieder"

patterns-established:
  - "Annahme mit Ausgang messen: eine im Plan offene Wertform wird im Integrationstest sowohl im Erfolgs- als auch im Ablehnungsfall gruen, und der gemessene Ausgang wandert in die Zusammenfassung"
  - "Idempotentes Testgeruest nach Titel (T-08-30): eine Tabelle mit festem Titel wird gesucht und nur beim Fehlen angelegt, ein zehnter Lauf hinterlaesst keine zehnte Tabelle"

requirements-completed: [TABLES-01, TABLES-02]

# Metrics
duration: 24 min
completed: 2026-08-21
---

# Phase 8 Plan 05: Integration und Berechtigungstreue Summary

**Die Tables-Familie ist gegen eine echte Nextcloud belegt: eine Zeile mit Umlauten entsteht über Spaltentitel und kommt über `browse(level="rows")` zurück, die echte Zeilen-URL trägt `limit`, Auswahl- und Datumswert gehen ohne eigene Umformung durch (Annahme A2 beantwortet), und ein zweites Konto sieht die Tabelle des ersten nicht, kann bei bekannter Id nichts lesen und nichts schreiben.**

## Performance

- **Duration:** 24 min
- **Started:** 2026-08-21T08:16:00Z
- **Completed:** 2026-08-21T08:40:00Z
- **Tasks:** 2
- **Files modified:** 5 (1 neu, 4 geändert)

## Accomplishments

- `tests/integration/test_tables_roundtrip.py` läuft mit fünf Tests grün gegen die App-Passwort-Topologie, ohne einen einzigen Skip: Capabilities, Roundtrip, erzwungenes Limit in der echten URL, `rowsCount` plus `can_create`, unbekannte Tabelle.
- Die drei offenen Punkte der Recherche sind jetzt Messwerte und keine Annahmen mehr (A2, A6, K5), und der teuerste davon fiel zugunsten des Plans aus: es braucht keine clientseitige Typumformung.
- Der Zwei-Konten-Negativbeweis gilt auch für Tables. Er ist in beide Richtungen abgesichert: der positive Teil läuft im selben Lauf, und der negative benutzt die echte Tabellen-Id statt einer geratenen.
- Der Schreibversuch des zweiten Kontos wird nicht nur an der Fehlermeldung geprüft, sondern an der Zeilenzahl des Eigentümers davor und danach. Eine abgelehnte Schreiboperation, die trotzdem eine Zeile hinterlässt, wäre schlimmer als eine stille Ablehnung, weil kein Werkzeug dieses Servers eine Zeile wieder entfernen kann.
- Zwei Fallen der Tables-App sind unterwegs aufgefallen und im Code begründet festgehalten: eine Textspalte ohne `subtype` macht die ganze Tabelle zu einem 500, und der Zugriff auf eine fremde Tabelle antwortet mit 404 und leerem Körper statt mit 403.

## Die Messwerte (wörtlich, für Phase 10 und 11)

Gemessen am 2026-08-21 gegen Nextcloud 34.0.3, Tables 2.2.2, AppAPI 34.0.0.

| Frage | Messwert |
|-------|----------|
| Statuscode des Zeilen-Anlegens | 200, der Aufruf liefert `id`, `table_id`, `url` und `values_written` (Falle 4 bestätigt: eine Prüfung auf 201 wäre rot) |
| `capabilities.tables.apiVersions` | `['1.0', '2.0', '2.1']`, also beide vom Client gesprochenen Generationen plus eine dritte |
| `rowsCount` im Einzeltabellenaufruf (A6) | vorhanden, `rowsCount=1` beim ersten Lauf, danach wachsend |
| `onSharePermissions` im Einzeltabellenaufruf (A6) | vorhanden, für die eigene Tabelle `{'read': True, 'create': False, 'update': False, 'delete': False, 'manage': False}` |
| `can_create` für die eigene Tabelle (K5) | `True`, obwohl das Share-Objekt nur `read` meldet; die Eigentümer-Regel ist damit live belegt |
| Auswahlwert (A2) | akzeptiert. Das **Label** der Option (`"offen"`) geht ohne Umformung durch, Antwort 200 |
| Datumswert (A2) | akzeptiert. Ein ISO-Datum (`"2026-08-21"`) geht ohne Umformung durch, Antwort 200 |
| Gemeinsamer Schreibvorgang | alle vier Werte in einem Aufruf (Text, Zahl, Auswahl, Datum) mit 200; es war kein Rückfall auf Text plus Zahl nötig |
| Live gebaute Zeilen-URLs | `/index.php/apps/tables/api/1/tables/3/rows/simple?limit=25&offset=0` und `?limit=200&offset=0` (aus `limit=5000` gekappt) |
| Zugriff des zweiten Kontos auf die fremde Tabelle | HTTP **404** mit leerem Körper und `Content-Type: text/html`, nicht 403: die Instanz gibt die Existenz der Tabelle nicht preis |
| Werkzeuge im Abnahmelauf | `OK: all 18 tools answered over stdio`, Exit-Code 0 |
| `tools/list` | 12801 Bytes bei 18 Werkzeugen, Gate 15000, Exit-Code 0 |

**Konsequenz für Annahme A2:** die Empfehlung der Recherche bleibt gültig und wird durch die Messung gestützt: keine clientseitige Typvalidierung. Die zwei Formen jenseits von Text und Zahl, die ein Modell natürlich schreibt (Option-Label, ISO-Datum), akzeptiert die App unverändert. Was weiterhin ungemessen bleibt, sind `usergroup`, `relation` und die Untertypen von `datetime`; sie gehören in die Phase, die sie braucht, nicht in eine Vorabvalidierung.

**Konsequenz für die Rückgabe der Zeilenwerte:** die kompakte Zeilenform liefert eine leere Auswahl als `null` und ein leeres Datum als `""`. Beides erreicht das Modell unverändert; Phase 11 entscheidet, ob das für `prepare_context` reicht (Tabellenzeilen bekommen dort ohnehin bewusst keinen Auszug).

## Task Commits

1. **Task 1: Roundtrip gegen eine echte Nextcloud** - `8bd61fe` (fix, die Voraussetzung aus Abweichung 2) und `db3e50a` (test)
2. **Task 2: Zwei-Konten-Negativbeweis für Tables** - `4909f94` (test)

Zusätzlich: `11ea777` (docs, Changelog-Eintrag zur geänderten Fehlermeldung, Regel der Changelog-Pflege)

## Files Created/Modified

- `tests/integration/test_tables_roundtrip.py` (neu, 336 Zeilen) - fünf Tests plus zwei Geräst-Helfer (`_post` mit Skip ab Status 400, `_table_with_columns` idempotent nach Titel), die Attempt-Kette `_create_measuring_the_value_shapes` für Annahme A2, `_row_with_task` als paginierte Suche, `measured()` für die Messwerte eines grünen Laufs
- `tests/integration/test_permission_fidelity_exapp.py` (geändert, 478 Zeilen) - drei neue Tests am Dateiende plus Credential-Fabrik `_appapi_clients`, zwei Konto-Fixtures, das Geräst `_scaffold` und der Zeilen-Leser `_rows`; der Modul-Docstring benennt die zweite Messschicht und schränkt die alte Aussage über `httpx.BasicAuth` auf die Kettenfälle ein, statt sie unwahr werden zu lassen. Die neun bestehenden Fälle sind unverändert
- `src/mcp_connector/nextcloud/clients/ocs.py` (geändert) - `_check_transport` erklärt einen Status ab 400 ohne JSON-Körper über `_status_error`; neuer Prädikat-Helfer `_looks_like_json`
- `tests/unit/test_tables_client.py` (geändert) - ein Test hält die echte Form einer unbekannten Tabellen-Id fest (404, leerer Körper, `text/html`) und behauptet, dass der Hinweis nicht vom App-Passwort spricht
- `CHANGELOG.md` (geändert) - `### Fixed` im `[Unreleased]`-Block, aus Nutzersicht formuliert

## Decisions Made

- **Die Spalten entstehen über die typisierten `api/2`-Routen.** Der Plan nennt `POST /ocs/v2.php/apps/tables/api/1/columns/...` als Geräst-Route. Diese Adresse existiert nicht: Generation 1 liegt unter `/index.php`, und die Spalten-Schreibrouten der Generation 2 sind nach Typ getrennt (`columns/text`, `columns/number`, `columns/selection`, `columns/datetime`), jede mit `baseNodeId` und `baseNodeType` im Körper. Geprüft an der `openapi.json` der laufenden App, nicht an der Erinnerung.
- **`subtype: "line"` für die Textspalte, und das ist kein Detail.** `ColumnsHelper::getColumnBusinessObject` baut den Klassennamen aus `ucfirst(type) . ucfirst(subtype) . 'Business'`. `TextBusiness` gibt es nicht, nur `TextLineBusiness`, `TextLongBusiness`, `TextLinkBusiness` und `TextRichBusiness`. Eine ohne `subtype` angelegte Textspalte macht jeden Lese- und Schreibzugriff auf die ganze Tabelle zu einem 500, obwohl die `openapi.json` `subtype` als optional führt und als Werte `progress` und `stars` nennt, die zu einer Zahlenspalte gehören. `number`, `selection` und `datetime` haben je eine Klasse ohne `subtype` und sind deshalb nicht betroffen.
- **Messwerte per `warnings.warn` statt per `print`.** Ein `print` erscheint nur im roten Fall, und genau der grüne Lauf ist der, dessen Zahlen gebraucht werden. Die Warnungen erscheinen auch unter `-q` im Bericht und sind die Quelle der Messtabelle oben.
- **Der Tables-Beweis liegt eine Schicht unter den Kettenfällen.** Tabelle und Spalte sind keine Connector-Fähigkeiten, das Geräst braucht also ohnehin einen Direktaufruf, und die interessante Grenze dieser Familie ist die Impersonation-Naht. Beide Identitäten sind daher `Credentials` im Modus `appapi` mit `APP_SECRET` als einziger Berechtigung, so wie in `test_exapp_dav_matrix.py`. Der Docstring sagt das, statt die alte Aussage der Datei stillschweigend unwahr werden zu lassen.
- **Die Zeilensuche paginiert.** Die Testtabelle überlebt jeden Lauf und wächst um eine Zeile pro Lauf. Ein breites Lesen mit `limit=200` würde nach genug Läufen die eigene Zeile verpassen; der Cursor findet sie und belegt zugleich, dass der Handle live die Tabellen-Id als Scope trägt.

## Deviations from Plan

### Auto-fixed Issues

**1. [Regel 3 - Blockierend] Die Geräst-Route für Spalten und der fehlende `subtype`**

- **Found during:** Task 1
- **Issue:** Zwei Fehler in einer Zeile des Plans. Erstens nennt er `POST /ocs/v2.php/apps/tables/api/1/columns/...`, eine Adresse, die es nicht gibt (Generation 1 liegt unter `/index.php`, und die Spaltenrouten der Generation 2 sind nach Typ getrennt). Zweitens ist eine Textspalte ohne `subtype` in Tables 2.2.2 unbenutzbar: der erste Lauf legte die Tabelle samt Spalten an und jeder Zeilenzugriff darauf endete mit 500 (`Could not resolve OCA\Tables\Service\ColumnTypes\TextBusiness`), also auch der Roundtrip, der eigentlich gemessen werden sollte.
- **Fix:** Die vier Spalten entstehen über `columns/text`, `columns/number`, `columns/selection` und `columns/datetime` mit `baseNodeId` plus `baseNodeType`, und die Textspalte trägt `subtype: "line"`. Der Grund steht als Absatz im Docstring des Geräst-Helfers, damit die nächste Familie ihn nicht neu messen muss. Die im ersten Lauf entstandene defekte Tabelle wurde per API entfernt, damit die Idempotenz-Prüfung eine echte Aussage trifft.
- **Files modified:** `tests/integration/test_tables_roundtrip.py`
- **Verification:** `uv run pytest tests/integration/test_tables_roundtrip.py -m integration -q` fünf Tests grün, kein Skip; die Instanz trägt nach vier Läufen genau eine Testtabelle
- **Committed in:** `db3e50a`

**2. [Regel 1 - Bug] Ein 4xx ohne JSON-Körper wurde als Loginseite gemeldet**

- **Found during:** Task 1 (Test fünf, unbekannte Tabelle)
- **Issue:** Die Instanz beantwortet `GET /ocs/v2.php/apps/tables/api/2/tables/99999999` mit 404, leerem Körper und `Content-Type: text/html`. `_json_payload` liest daraus wörtlich eine HTML-Seite und meldete: "Nextcloud answered ... with an HTML page instead of JSON. That is the Nextcloud login page. Check the app password ...". Der Satz ist für den häufigsten Modellfehler überhaupt, eine geratene Id, der falsche nächste Schritt: das Modell tauscht ein Passwort aus, statt die Id zu suchen. Derselbe Pfad trägt in Task 2 den Negativbeweis, dort hätte eine fremde Tabelle als Credential-Problem gemeldet worden.
- **Fix:** `_check_transport` erklärt einen Status ab 400 ohne JSON-Körper über `_status_error`, also für 404 mit "Nextcloud did not find the table 2. Search for it first; the id or the name is unknown to this instance." Ein 4xx **mit** JSON-Körper geht unverändert weiter durch die App-eigene Meldung, und der 5xx-Zweig bleibt vor dem neuen, damit seine Formulierung erhalten bleibt.
- **Files modified:** `src/mcp_connector/nextcloud/clients/ocs.py`, `tests/unit/test_tables_client.py`, `CHANGELOG.md`
- **Verification:** neuer Unit-Test grün, `uv run pytest` 2268 Tests grün (keine Regression in den sechs anderen Familien, die denselben Parser benutzen), Live-Messung in beiden Topologien zeigt den neuen Satz
- **Committed in:** `8bd61fe`, Changelog in `11ea777`

**3. [Regel 2 - Fehlende Kritikalität] Der Wertformen-Probelauf statt eines einzelnen Versuchs**

- **Found during:** Task 1
- **Issue:** Der Plan verlangt, im Create-Test zusätzlich einen Auswahl- und einen Datumswert zu schreiben, und den 400 gegebenenfalls sichtbar zu machen. Ein einzelner Versuch mit allen vier Werten hätte im Fehlerfall aber nur gesagt, dass irgendetwas abgelehnt wurde, nicht welche der zwei offenen Formen. Genau diese Zuordnung ist der Zweck der Messung für Phase 10.
- **Fix:** Eine Attempt-Kette: alle vier Werte, dann Text plus Zahl plus Auswahl, dann Text plus Zahl plus Datum, dann Text plus Zahl. Der erste Erfolg gewinnt, jeder Ausgang wird berichtet. Im tatsächlichen Lauf griff schon der erste Versuch, die Kette blieb also ungenutzt und ist die Versicherung für den Tag, an dem eine neue Tables-Version eine Form ablehnt.
- **Files modified:** `tests/integration/test_tables_roundtrip.py`
- **Verification:** der rote Zwischenstand aus Abweichung 1 hat die Kette unfreiwillig vollständig durchlaufen und alle vier Ablehnungen einzeln berichtet
- **Committed in:** `db3e50a`

**4. [Regel 2 - Fehlende Kritikalität] Der Modul-Docstring der Fidelity-Datei wurde nachgezogen**

- **Found during:** Task 2
- **Issue:** Der Plan verlangt für die neuen Fälle zwei Credential-Objekte im Modus `appapi` und lässt die bestehenden Fälle unberührt. Der Docstring der Datei behauptete aber wörtlich, dass in ihr **nichts** ein `Credentials`-Objekt baut. Mit den neuen Fällen wäre dieser Satz unwahr geworden, und eine unwahre Aussage in genau der Datei, die die Beweiskraft der Messung begründet, ist schlimmer als eine fehlende.
- **Fix:** Der Satz ist auf die Kettenfälle eingeschränkt, und ein eigener Absatz benennt die zweite Messschicht, ihren Grund (Tabelle und Spalte sind keine Connector-Fähigkeiten) und die Eigenschaften, die auch dort gelten (positiver Teil im selben Lauf, echte Id im negativen). Der Abschnitt im Code trägt zusätzlich eine Trennlinie mit der Bedrohungs-Id T-08-26.
- **Files modified:** `tests/integration/test_permission_fidelity_exapp.py`
- **Verification:** `uv run pytest tests/integration/test_permission_fidelity_exapp.py -m integration` 12 Tests grün, die neun bestehenden unverändert
- **Committed in:** `4909f94`

---

**Total deviations:** 4 auto-behoben (1 blockierend, 1 Bug im Produktionscode, 2 fehlende Kritikalität)
**Impact on plan:** Keine Umfangsänderung, keine neue Abhängigkeit (`pyproject.toml` und `uv.lock` unangetastet, T-08-SC bleibt `accept`). Drei Dateien mehr als die Plan-Liste (`src/mcp_connector/nextcloud/clients/ocs.py`, `tests/unit/test_tables_client.py`, `CHANGELOG.md`), alle drei aus Abweichung 2, also aus einem Bug, den erst der Live-Lauf sichtbar macht. Die Änderung im Produktionscode ist die einzige an einer geteilten Datei; sie ist eng gefasst (ein Zweig, ein Prädikat) und von 2268 grünen Tests plus zwei Live-Topologien gedeckt.

## Issues Encountered

- **Der erste Live-Lauf war rot, und das war der Punkt.** Vier Ablehnungen in Folge (`500` auf jedem Schreibversuch) führten über das Nextcloud-Log auf die fehlende `subtype`-Angabe. Das ist der Fall, für den Integrationstests existieren: kein Unit-Test hätte diese Falle finden können, weil sie in der Antwort der App und nicht in der Form unseres Requests liegt. Behoben als Abweichung 1.
- **Die Testinstanz `nc-mcp-test` hatte die Tables-App noch nicht.** `bash scripts/bootstrap_test_nc.sh` hat sie installiert (`app tables: installed`), so wie Plan 08-01 es vorgesehen hat; die Zeile war da, gelaufen war sie auf dieser Instanz noch nicht. Kein Codebedarf, nur die Reihenfolge des Laufs.
- **Zwei Läufe von `ruff format` haben Umbruchstellen verschoben**, einmal folgte eine Zeile über 100 Zeichen, die von Hand gekürzt wurde. Im selben Task behoben.

## Known Stubs

Keine. Beide Tests messen echte Antworten einer laufenden Instanz; es gibt keinen Datenpfad, der noch verdrahtet werden müsste, und keinen Platzhalterwert. Was fehlt, fehlt absichtlich und ist oben benannt: die Wertformen `usergroup` und `relation` sowie die Untertypen von `datetime` sind ungemessen, weil kein Plan dieses Meilensteins sie braucht.

## Threat Flags

Keine neue Sicherheitsfläche außerhalb des Threat Models des Plans. Zwei Einträge sind live belegt statt nur geplant: T-08-26 (fremde Tabelle) durch die drei neuen Fälle, T-08-30 (wiederholte Läufe) durch die Idempotenz nach Titel in beiden Topologien. Der Befund, dass Nextcloud eine fremde Tabelle mit 404 und leerem Körper beantwortet, ist für T-08-26 eine Verstärkung: die Instanz gibt nicht einmal die Existenz preis.

## User Setup Required

Keine, keine externe Dienstkonfiguration und keine neue Abhängigkeit.

## Verification

| Prüfung | Ergebnis |
|---------|----------|
| `uv run pytest tests/integration/test_tables_roundtrip.py -m integration -q` (App-Passwort-Topologie) | 5 passed, kein Skip |
| `uv run pytest tests/integration/test_permission_fidelity_exapp.py -m integration` (HaRP-Topologie) | 12 passed (9 bestehende plus 3 neue), kein Skip |
| `uv run pytest` (Default-Auswahl) | 2268 passed, 107 deselected |
| `uv run ruff check .` und `uv run ruff format --check .` | grün, 181 Dateien formatiert |
| `uv run pyright` (ganzes Projekt) | 0 errors, 0 warnings |
| `uv run vulture src scripts vulture_whitelist.py` | Exit 0 |
| `uv run python scripts/check_tool_budget.py` | 12801 Bytes, 18 Werkzeuge, Gate 15000, Exit 0 |
| `uv run python scripts/acceptance_all_tools.py` | `OK: all 18 tools answered over stdio`, Exit 0 |
| Zweiter und dritter Lauf beider Integrationstests | je genau eine Testtabelle pro Instanz (`MCP-Test Übergaben Straßenbau` id 3, `MCP-Test Berechtigungstreue` id 2), nur die Zeilenzahl wächst |
| `grep -c "def test_"` in der neuen Datei | 5 |
| `grep -c "tables"` in der Fidelity-Datei | 30 |
| Em-Dash und En-Dash in den geänderten Textdateien | keine |
| `git diff --diff-filter=D` über die vier Commits | leer, keine Datei gelöscht |

## Next Phase Readiness

- Erfolgskriterium 3, 4 und 5 der Phase sind live belegt; Phase 8 hat damit alle fünf Pläne und keinen offenen Nachweis mehr.
- Phase 10 (Mail) und Phase 11 (Bündelung) können auf die Messtabelle oben aufsetzen. Für Phase 11 heißt das konkret: `prepare_context` braucht für Tabellenzeilen keine Typumformung, und das Budget-Gate steht unverändert auf 12801 Bytes bei 18 Werkzeugen.
- Der Befund aus Abweichung 2 gilt für alle sieben Familien, nicht nur für Tables: jede unbekannte Id, die eine App mit einem leeren 4xx beantwortet, wird jetzt an ihrem Status erklärt. Wenn Phase 9 (Talk) auf eine App trifft, die Fehler in einer HTML-Seite mit Status 200 ausliefert, greift weiterhin der alte Zweig, und das ist die Aufteilung, die er auch soll.
- Offen und bewusst ausgeklammert: die Wertformen `usergroup` und `relation` sowie die Untertypen von `datetime`. Sie gehören in die Phase, die ein Werkzeug dafür braucht; heute existiert keines.

## Self-Check: PASSED

- `tests/integration/test_tables_roundtrip.py` FOUND (336 Zeilen, `min_lines` 150 erfüllt)
- `tests/integration/test_permission_fidelity_exapp.py` FOUND, enthält `tables` (30 Treffer) und `MODE_APPAPI`
- Commits `8bd61fe`, `db3e50a`, `4909f94`, `11ea777` in `git log --all` gefunden
- `key_links` des Plans nachgewiesen: `tables_tools.browse` und `tables_tools.create_row` in beiden Testdateien, `MODE_APPAPI` in der Fidelity-Datei
- Alle Abnahmekriterien beider Aufgaben nachgelaufen, siehe Abschnitt Verification

---
*Phase: 08-erreichbarkeits-spike-und-tables*
*Completed: 2026-08-21*
