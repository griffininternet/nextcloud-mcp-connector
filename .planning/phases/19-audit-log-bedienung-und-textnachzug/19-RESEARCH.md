# Phase 19: Audit-Log Bedienung und Textnachzug - Research

**Researched:** 2026-08-31
**Domain:** AppAPI-occ-Kommandos (Registrierung, Symfony-Abbildung, Draht-Form), Declarative-Settings-Beschriftung, Textwahrheit und Wortlisten-Gates in einem bestehenden Repo
**Confidence:** HIGH (die Fremdkomponente app_api v34.0.3 und symfony/console sind an der Quelle gelesen; alle Repo-Aussagen sind am Code belegt)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**occ-Lesekommando (AUDIT-04)**
- Lesen und Exportieren über ein `occ`-Kommando; KEINE neue Route im Manifest. Muster ist das in Phase 18 gebaute `occ mcp_connector:audit:verify`: AppAPI-PublicFunctions auf einen Pfad ohne `<url>`-Eintrag, Doppelprüfung x-origin-ip (404) dann require_appapi (401), immer Status 200 mit Urteil im Rumpf (AppAPI verwirft den Rumpf bei jedem anderen Status, T-18-20).
- Ausgabe klammert Nutzer- und Client-Namen vor der Ausgabe (Muster T-18-08); nie Parameterwerte, nie IPs, nie Fehlermeldungstexte.

**Admin-Schalter und Beschriftung (AUDIT-05)**
- Ab Werk aus, einschaltbar in den Admin-Einstellungen (existiert seit Phase 18 als siebter Wert `audit_log`). Diese Phase zieht die BESCHRIFTUNG nach: was das Log leistet, was es nicht leistet (Grenzbeschreibung ist Pflichtbestandteil, D-v1.5-02), und dass ein nutzerbezogenes Protokoll mitbestimmungsrelevant sein kann (D-v1.5-04).
- Keine Stufe, die Parameterwerte oder Ergebnisinhalte protokolliert; `keys` ist der einzige einschaltbare Inhaltsumfang, `full` existiert nirgends in der Oberfläche.
- Befund aus dem Phase-18-Review (Info-Finding, hier einzulösen): die bisherige Formularbeschreibung verschweigt, dass auch Parameternamen, Ablehnungsgrund und Dauer gespeichert werden. Die neue Beschriftung nennt das ehrlich.

**Textnachzug (AUDIT-06)**
- `docs/privacy.md` und `docs/uninstall.md` sagen im eigenen Text, dass das Audit-Log Purge und Deinstallation übersteht und die Aufbewahrungsfrist der einzige automatische Löscher ist (plus Nutzerlöschung in Nextcloud). Das v1.0-Erfolgskriterium "eine Deinstallation entfernt alle Daten" wird ausdrücklich umgeschrieben statt stillschweigend falsch (D-v1.5-01). Restpunkt R-18-04 aus 18-SECURITY.md: uninstall.md nennt das Audit-Log heute namentlich NICHT, die D-18-Grenze (`--rm-data` entfernt das Volume samt Log) steht bisher nur im Phasenartefakt und gehört in den Nutzertext.
- Enterprise-Absatz nennt das Audit-Log in allen drei Sprachen (EN/DE/FR) nicht länger als geplant; der Satz "heute in keiner Form vorhanden" ist mit Phase 18 falsch geworden.
- Wörter-Gate: ein Test hält die Wörter revisionssicher, AI-Act-konform, DSGVO-konform und SIEM-zertifiziert aus den Texten heraus (D-v1.5-02, Verbotsliste).
- Dreisprachigkeit ist Projektregel: README- und Store-Text-Änderungen immer EN/DE/FR nachziehen; echte Umlaute und Accents, keine Em-Dashes; in info.xml-Descriptions kein Backtick und keine Tabelle, die Version in info.xml wird NICHT angefasst.
- Alles wartet im `[Unreleased]`-Block des Changelogs; kein Tag (Milestone-Tags heißen milestone-v*, NIE v*, weil release.yml auf v* triggert).

### Claude's Discretion

- Ob das Lesekommando ein eigenes `mcp_connector:audit:read`/`:export` wird oder das bestehende verify-Kommando eine Leseausgabe bekommt; Exportformat (JSONL/CSV) und Filteroptionen.
- Ob die drei Env-Variablen (`NC_MCP_AUDIT_LOG`, `NC_MCP_AUDIT_RETENTION_DAYS`, `NC_MCP_AUDIT_MAX_BYTES`) jetzt einen `<environment-variables>`-Eintrag in appinfo/info.xml bekommen (deferred item aus 18-07; reine Bequemlichkeit für Hand-Installationen, Admin-Formular bleibt der Hauptweg BL-06).
- Ob die Restrisiken R-18-06/07/08 aus 18-SECURITY.md hier miterledigt werden (drei divergente Namensreiniger/Bidi, note() vs CancelledError, isdigit ohne isascii in audit_verify._payload); sie sind klein, code-nah und berühren die Bedienoberfläche dieser Phase.

### Deferred Ideas (OUT OF SCOPE)

- EXAPP-12: Release 0.1.12 mit dem Audit-Log; ausdrücklich nicht Teil dieses Meilensteins.
- Flakiger Test `test_a_flood_of_accepted_authorization_requests_ends_in_429` (zeitabhängig, ohne Bezug zur Phase).
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| AUDIT-04 | Ein Administrator liest und exportiert das Log über ein `occ`-Kommando, ohne dass dafür eine neue Route im Manifest deklariert wird | §Muster 1 (drittes Kommando am gemessenen `command_schemes()`-Muster), §Muster 2 (Wert-Optionen und ihre Draht-Form, an app_api v34.0.3 gelesen), §Muster 3 (neue Lesemethode in `AuditStore`, weil heute keine existiert), Pitfalls 1 bis 8, Code-Beispiele 1 bis 4 |
| AUDIT-05 | Das Audit-Log ist ab Werk abgeschaltet und über die Admin-Einstellungen einschaltbar; die Beschriftung sagt, was das Log leistet, was es nicht leistet, und dass ein nutzerbezogenes Protokoll mitbestimmungsrelevant sein kann | §Muster 4 (Beschriftung in `ui/strings.py`, Formular unverändert), §Was ein Eintrag wirklich trägt (17 Felder, Grundlage der ehrlichen Beschriftung), Pitfalls 9 bis 12, Code-Beispiel 5 |
| AUDIT-06 | `docs/privacy.md` und `docs/uninstall.md` sagen die neue Wahrheit über Speicherung und Purge, und der Enterprise-Absatz nennt das Audit-Log nicht länger als geplant, in allen drei Sprachen und ohne die vier verbotenen Wörter | §Fundstellen-Karte (jede falsche Aussage mit Datei und Zeile), §Drei automatische Löscher statt einem (der wichtigste Befund dieser Recherche), §Muster 5 (Wörter-Gate am bestehenden Vokabular-Gate), Pitfalls 13 bis 20, Code-Beispiel 6 |
</phase_requirements>

---

## Summary

Diese Phase baut kein neues Fundament, sie schließt eine Bedienlücke und eine Textlücke. Der Weg für das Lesekommando ist durch Phase 18 vollständig vorgezeichnet und an der Quelle von app_api v34.0.3 gemessen: `command_schemes()` in `src/mcp_connector/exapp/occ.py` bekommt einen dritten Eintrag, ein neues Handler-Modul mit eigener Pfadkonstante und derselben Doppelprüfung entsteht neben `exapp/audit_verify.py`, und `entry_exapp.build_exapp_app` hängt es in derselben Aufzählung auf. Der einzige echte Neubau am Code ist eine **Lesemethode in `AuditStore`**: der Speicher hat heute `verify_chains`, `overview`, `last_entry` und `size`, aber keinen Weg, Zeilen herauszugeben. Das ist die eine substanzielle Ergänzung.

Neu ist gegenüber Phase 18 nur eines an der Schnittstelle: das Lesekommando braucht Optionen **mit Wert** (`--user`, `--since`, `--limit`, `--format`), und das verify-Kommando kennt bisher nur eine wertlose Flagge. Die Abbildung dieser Modi ist die gefährlichste Stelle der Phase, und sie ist keine Geschmacksfrage: `appinfo/register_command.php` von app_api baut beim Start **jedes** occ-Aufrufs alle ExApp-Kommandos und fängt dabei nur Container-Ausnahmen. Ein Kommandoschema mit einem von Symfony abgelehnten Modus legt damit die gesamte `occ`-Kommandozeile der Instanz still, nicht nur das eigene Kommando. Die erlaubten Modi und die eine verbotene Kombination stehen unten mit Zeilenverweis.

Der Textnachzug ist grösser als er aussieht, und die Recherche hat dabei einen Widerspruch gefunden, der vor dem ersten Satz entschieden werden muss: CONTEXT, ROADMAP und D-v1.5-01 sagen, die Aufbewahrungsfrist sei der **einzige** automatische Löscher (plus Nutzerlöschung). Der Code von Phase 18 kennt **drei** automatische Löschwege: die Frist (D-09), die Obergrenze von 100 MB, die die ältesten Nutzerzeilen mit einem Grabstein verdrängt (D-10, `_sweep_over_limit`), und die Kontoprüfung, die eine ganze Kette fallen lässt, wenn das Konto in Nextcloud nicht mehr existiert (D-12, `drop_user_chain`). Ein Datenschutztext, der nur die Frist nennt, wäre erneut falsch, nur diesmal wissentlich. Der Vorschlag steht unten, samt Textbaustein.

**Primary recommendation:** Ein drittes occ-Kommando `mcp_connector:audit:read` mit ausschliesslich Wert-Optionen im Modus `optional` (nie `array`), einer neuen `AuditStore.read_entries()`-Methode mit hartem Vorgabelimit und JSONL als Exportform; die Beschriftung in `ui/strings.py` um die drei fehlenden Felder und den Mitbestimmungssatz erweitern; den Textnachzug an sechs Enterprise-Stellen und vier Doku-Stellen führen und dabei alle drei automatischen Löscher benennen; das Vier-Wörter-Gate als zweite Wortliste in das bestehende Vokabular-Gate in `tests/unit/test_exapp_env_setup.py` einhängen, mit Wortformen statt Teilwörtern.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Kommandozeile, Optionsparsing, Ausgabe auf die Konsole | Nextcloud PHP (app_api, Symfony Console) | ExApp (liefert das Schema) | Das Kommando ist ein Symfony-Command, den Nextcloud aus der Registrierung baut; die ExApp bestimmt nur Name, Beschreibung, Optionen und Handlerpfad |
| Registrierung des Kommandos | ExApp (`exapp/occ.py`, im `enabled=1`-Zweig) | Nextcloud-DB (`insertOrUpdate` je (appid, name)) | Ein POST je Kommando auf `/ocs/v2.php/apps/app_api/api/v1/occ_command`; Abmeldung erledigt AppAPI selbst |
| Zugriffsentscheid für den Handler | ExApp (Handler-Doppelprüfung) | Manifest (Abwesenheit der Route) | HaRP schützt undeklarierte Pfade, der PHP-Proxy nicht: die Abwesenheit im Manifest IST die Kontrolle (T-18-07) |
| Leseabfrage, Filter, Limit | ExApp (`audit/store.py`, SQLite in `asyncio.to_thread`) | - | Der Speicher besitzt das Schema und die Verkettung; nur er darf Zeilen herausgeben |
| Formung, Klammerung, Format | ExApp (neues Handlermodul) | - | Klammerung gehört unmittelbar vor die Ausgabe, wie in `audit_verify._printable` |
| Admin-Schalterzustand | Nextcloud (Declarative Settings, `oc_appconfig_ex`) | ExApp (`config_values`, liest zurück) | AppAPI speichert den Wert des Admin-Feldes unter der Feld-Id als Konfigurationsschlüssel |
| Admin-Beschriftung | ExApp (`exapp/ui/strings.py`) | Nextcloud (rendert Titel und Beschreibung) | Declarative Settings haben keinen Button und keine Hilfeseite: der Beschreibungstext ist der einzige Ort für Leistung, Grenze und Mitbestimmung |
| Store-Beschreibung (Enterprise-Absatz) | `appinfo/info.xml` | apps.nextcloud.com (liest nur beim Upload) | Eine Textänderung erreicht den Store erst mit dem nächsten Release; hier ausdrücklich nicht Teil der Phase (EXAPP-12) |
| Nutzerdokumentation | Repo (`docs/*.md`, `README*.md`) | - | Was ein Leser des Repositories bekommt, ist die zweite öffentliche Fläche neben dem Store |
| Wörter-Gate | Testschicht (`tests/unit/test_exapp_env_setup.py`) | - | Das bestehende Vokabular-Gate hält bereits Reichweite und Gegenprobe; eine zweite Liste erbt beides |

---

## Standard Stack

### Core

Diese Phase installiert **kein** Paket. Alles Nötige liegt bereits im Baum.

| Baustein | Version / Ort | Purpose | Why Standard |
|----------|---------------|---------|--------------|
| Python-Standardbibliothek `json` | 3.13 | JSONL-Zeilen, Optionsrumpf lesen | `audit/store.py` kanonisiert schon mit `json.dumps(separators=(",",":"), ensure_ascii=False)`; dieselbe Form für den Export [VERIFIED: `src/mcp_connector/audit/store.py:495-503`] |
| Python-Standardbibliothek `sqlite3` | 3.13 (SQLite 3.50.4 auf diesem Rechner) | Leseabfrage mit Platzhaltern | Der Speicher fährt bereits so, inklusive WAL, `busy_timeout` und `asyncio.to_thread` [VERIFIED: `store.py:1108-1134`] |
| Python-Standardbibliothek `csv` | 3.13 | nur falls CSV als zweites Format gewählt wird | Kein Paket nötig; siehe Empfehlung unten (JSONL statt CSV) |
| `starlette.responses.Response` | via mcp/FastAPI im Lock | Antwort mit `text/plain` und `no-store` | Genau das tut `audit_verify._text` [VERIFIED: `exapp/audit_verify.py:400-406`] |
| `pytest` + `starlette.testclient.TestClient` | im Lock | Handler-Tests ohne Netz | Das Testmuster von `tests/unit/test_exapp_audit_verify.py` ist eins zu eins übertragbar [VERIFIED: Datei gelesen] |
| `lxml` | >=6.1,<7 (im Lock) | Manifest-Gates lesen `appinfo/info.xml` geparst | Das Vokabular-Gate liest den Elementtext ohne Kommentare [VERIFIED: `tests/unit/test_exapp_env_setup.py:1713-1727`] |

### Supporting

| Baustein | Ort | Purpose | When to Use |
|----------|-----|---------|-------------|
| `config._bounded_number` | `src/mcp_connector/config.py` | Zahl aus Text mit Untergrenze und Unicode-Falle abgesichert | Vorbild für `--limit` und `--since`; es prüft `isascii()` **und** `isdigit()`, was `audit_verify._payload` heute unterlässt (R-18-08) |
| `audit_verify._printable` | `exapp/audit_verify.py:277-296` | Kettenkennung druckbar und begrenzt | Vorbild für die Klammerung von `nc_user` in der Leseausgabe |
| `audit/store._clean_client_name` | `store.py:506-520` | Client-Name gereinigt und gekürzt | Bereits beim Schreiben angewandt; der Export muss ihn nicht erneut reinigen, aber `nc_user` sehr wohl |
| `tests/unit/test_oauth_store.py::test_the_privacy_doc_describes_the_clients_table_as_it_is` | `:1490-1509` | Muster: eine Doku-Aussage an ein Codefaktum binden | Vorbild für Tests, die die neuen Sätze in `privacy.md` gegen den Code halten statt gegen eine Absicht |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Drittes Kommando `mcp_connector:audit:read` | Leseausgabe an `:verify` anhängen | Verworfen: `verify` ist die Integritätsaussage und hat heute genau eine Flagge; ein Kommando, das je nach Option prüft oder ausgibt, macht aus einer klaren Antwort zwei. Der Kommentar in `occ.py:81-83` hat den zweistufigen Namensraum ausdrücklich für dieses zweite Kommando gebaut |
| Ein Kommando `:read` mit `--format` | Zwei Kommandos `:read` (Text) und `:export` (JSONL) | Verworfen für v1: jede Registrierung ist ein eigener POST und ein eigener Fehlerpfad, und `--json` ist im verify-Kommando schon die etablierte Form für "dasselbe für eine Maschine" |
| JSONL | CSV | JSONL empfohlen: die Zeile trägt 17 Felder mit `NULL`-Semantik und eine JSON-Liste in `params`; CSV müsste `params` erneut kodieren und verliert die Unterscheidung leer/nicht gesetzt. CSV kann später als zweiter `--format`-Wert nachkommen, ohne dass sich etwas anderes ändert |
| Vorgabelimit plus `--limit` | Streaming-Antwort über den ganzen Speicher | Limit empfohlen: AppAPI liest den Rumpf mit `stream => true` und `timeout => 0`, also wäre Streaming grundsätzlich möglich, aber ein Starlette-`StreamingResponse` durch HaRP ist in diesem Projekt nirgends belegt (kein Vorkommen in `src/`). Ein Vorgabelimit ist die belegbare Form; Streaming bleibt eine spätere Option |
| Zweite Wortliste im bestehenden Gate | Eigene Gate-Datei für die vier Wörter | Verworfen: die Begründung des bestehenden Gates sagt selbst, zwei Orte mit derselben Aufgabe wären zwei Wahrheiten (Kommentar `test_exapp_env_setup.py:1953-1961`) |

**Installation:**

```bash
# Keine. Diese Phase fügt keine Abhängigkeit hinzu.
# pyproject.toml und uv.lock bleiben unberührt (Präzedenz: T-18-SC in 18-SECURITY.md).
```

**Version verification:** Nicht anwendbar, weil kein Paket hinzukommt. Die geprüften Fremdstände: `app_api` v34.0.3 (Quelle gelesen), `symfony/console` 7.3 (Quelle gelesen), lokal `uv 0.11.7`, `Python 3.13.1`, `ruff 0.16.3`.

---

## Package Legitimacy Audit

Diese Phase installiert **kein** externes Paket. `pyproject.toml` und `uv.lock` bleiben unberührt.

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| (keine) | - | - | - | - | - | Nicht anwendbar |

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

Der Planer soll für diese Phase eine Prüfung mitführen, die das belegt statt es zu behaupten: `git diff --stat <base> HEAD -- pyproject.toml uv.lock` muss leer sein. Genau diese Form führt 18-SECURITY.md als T-18-SC.

---

## Was ein Eintrag wirklich trägt

Grundlage für die ehrliche Beschriftung (AUDIT-05) und für jede Aussage in `privacy.md`. Die 17 Felder der kanonischen Form, gelesen aus `store.py:220-286`:

| Feld | Inhalt | In der heutigen Formularbeschreibung genannt? |
|------|--------|-----------------------------------------------|
| `seq` | Fortlaufende Nummer, in den Hash eingerechnet | nein (technisch, muss nicht) |
| `chain` | `u:<nc_user>` oder `i:instance` | mittelbar über "das Konto" |
| `kind` | `call`, `tombstone`, `switch` | nein |
| `at` | Unix-Sekunden des Schreibens | ja ("die Zeit") |
| `actor` | wer geschaltet hat, heute immer `unknown` (D-16) | nein |
| `nc_user` | Kontoname | ja |
| `tool` | Werkzeugname | ja |
| `client_id` | Client-Id der Registrierung | ja ("die App, die aufgerufen hat") |
| `auth_id` | Verbindungs-Id | nein |
| `client_name` | Name aus der dynamischen Registrierung, gereinigt, auf 80 gekürzt | ja |
| `outcome` | `ok` / `rejected` / `failed` | ja ("ob der Aufruf gelungen ist") |
| `reason` | eine von sechs eingefrorenen Ablehnungskennungen, nie eine Fehlermeldung | **nein (Lücke IN-06)** |
| `duration_ms` | Dauer des Aufrufs | **nein (Lücke IN-06)** |
| `params` | sortierte JSON-Liste von Parameter**namen**, nie Werte | **nein (Lücke IN-06)** |
| `removed`, `gap_chain`, `gap_hash` | Buchführung der Grabsteine | nein (technisch) |

Die drei fett markierten Felder sind genau die Lücke, die das Phase-18-Review als IN-06 festgehalten hat und die CONTEXT hier einzulösen verlangt. Der heutige Text steht in `ui/strings.py:649-654`.

Nicht im Schema, und das ist zusagbar: keine IP, kein User-Agent, kein Parameterwert, kein Ergebnisinhalt, keine Fehlermeldung, kein Geheimnis (belegt in 18-SECURITY.md T-18-01, T-18-08, T-18-12).

---

## Drei automatische Löscher statt einem

**Das ist der wichtigste Befund dieser Recherche, und er widerspricht dem Wortlaut der Vorgabe.**

CONTEXT, ROADMAP-Erfolgskriterium 4 und D-v1.5-01 formulieren: "die Aufbewahrungsfrist ist der einzige automatische Löscher" (plus die Nutzerlöschung in Nextcloud). Der Code von Phase 18 löscht auf **drei** Wegen von selbst:

| Weg | Auslöser | Wirkung | Belegstelle |
|-----|----------|---------|-------------|
| Aufbewahrungsfrist | 180 Tage (Vorgabe, mindestens erreichbar), geprüft je 500. Zeile im Schreibpfad | Das abgelaufene Präfix jeder Nutzerkette geht, ein Grabstein erklärt die Lücke | `store.py:93`, `store.py:632-665`, `config.py:99` |
| Obergrenze | `used_bytes > 100 MB`, im selben Aufräumlauf | Die ältesten Zeilen **ausserhalb** der Instanzkette weichen, ein Grabstein erklärt sie (D-10) | `store.py:98`, `store.py:667-702` |
| Konto existiert nicht mehr | jede 20. Aufräumrunde, Kette 30 Tage stumm und Konto fehlt in der AppAPI-Nutzerliste | Die ganze Kette fällt, ein Grabstein in der Instanzkette nennt sie (D-12) | `store.py:111`, `store.py:912-989`, `audit/accounts.py` |

Die dritte Zeile ist die "Nutzerlöschung", die die Vorgabe schon nennt: sie ist kein manueller Akt am Log, sondern eine automatische Folge einer Löschung in Nextcloud, mit 30 Tagen Stille als Schwelle. Die **zweite Zeile fehlt in der Vorgabe vollständig**.

**Empfehlung an den Planer:** Der Textnachzug nennt alle drei, in genau dieser Rangfolge, und schreibt die Vorgabeformulierung nicht wörtlich ab. Ein Datenschutzdokument, das "einziger automatischer Löscher" behauptet, während die Obergrenze bei einem vollen Speicher die ältesten Einträge verdrängt, wäre wieder unwahr, und diesmal wäre es geprüft und trotzdem geschrieben. Vorschlag für die Sache selbst (Formulierung ist Sache des Plans):

> Automatisch entfernt werden Einträge in drei Fällen und in keinem anderen: wenn die Aufbewahrungsfrist von 180 Tagen abgelaufen ist, wenn die Obergrenze von 100 MB erreicht ist und die ältesten Einträge weichen müssen, und wenn das Konto, zu dem sie gehören, in Nextcloud gelöscht wurde. In allen drei Fällen bleibt eine Markierung stehen, die sagt, wie viele Einträge fehlen; deshalb meldet die Kettenprüfung eine erklärte Lücke und keinen Bruch.

Diese Ergänzung ändert keine gelockte Entscheidung: D-v1.5-01 entscheidet, **dass** das Log Purge und Deinstallation überlebt und dass der Text umgeschrieben wird. Wie viele automatische Löscher es gibt, ist eine Messung, keine Entscheidung. Der Planer soll das als ausdrücklichen Punkt in den Plan schreiben, damit es beim Verifizieren nicht als Abweichung gelesen wird.

---

## Fundstellen-Karte: jede Aussage, die heute falsch oder unvollständig ist

### Enterprise-Absatz, sechs Stellen in drei Sprachen

| Datei | Zeile | Heutiger Wortlaut (gekürzt) |
|-------|-------|------------------------------|
| `appinfo/info.xml` | 79 | "Audit log, group policies and SSO ... are planned as a commercial add-on" |
| `appinfo/info.xml` | 124 | "Audit-Log, Gruppen-Policies und SSO ... sind als kommerzielles Add-on für Organisationen geplant" |
| `appinfo/info.xml` | 171 | "Journal d'audit, politiques de groupe et SSO ... sont prévus comme module commercial" |
| `README.md` | 512-516 | "Audit log, group policies and SSO ... are planned as a commercial add-on" |
| `README.de.md` | 527-531 | "Audit-Log, Gruppen-Policies und SSO ... sind als kommerzielles Add-on geplant" |
| `README.fr.md` | 545-549 | "Journal d'audit, politiques de groupe et SSO ... sont prévus comme module commercial" |

CONTEXT nennt ausdrücklich nur den Enterprise-Absatz; der Changelog-Eintrag zu 0.1.10 belegt, dass dieser Absatz **immer** in allen sechs Stellen gepflegt wurde ("of the store description and of all three READMEs"). Der Plan muss alle sechs führen, sonst driften Store-Text und READMEs auseinander.

Zusatzbefund: der 0.1.10-Changelog-Eintrag behauptet über die drei genannten Dinge "exist in this version in no form and behind no setting". Das ist ein **Release-Eintrag über 0.1.10** und damit ein Datum, kein Anspruch für heute; er darf nicht rückwirkend geändert werden (dieselbe Begründung, mit der `docs/store-submission.md` vom Vokabular-Gate ausgenommen ist). Der neue Stand gehört in den `[Unreleased]`-Block.

### Speicher- und Purge-Aussagen

| Datei | Zeile | Was daran nicht mehr stimmt |
|-------|-------|------------------------------|
| `docs/privacy.md` | 27-40 | Die Tabelle "What the app stores" nennt nur `oauth.sqlite3` und seine Spalten. `audit.sqlite3` fehlt vollständig, obwohl es Kontoname, Werkzeug, Client und Parameternamen dauerhaft hält |
| `docs/privacy.md` | 29 | "The app keeps **one** SQLite database inside its own container" - es sind zwei |
| `docs/privacy.md` | 174-176 | "empties every table of its database" - der Purge leert die Tabellen des OAuth-Speichers; das Audit-Log überlebt (T-18-22, vier Tests in `test_exapp_purge.py:800-860`) |
| `docs/privacy.md` | 183-184 | "spells out both steps and how to verify that nothing is left" - nach dem Purge bleibt das Log |
| `docs/privacy.md` | 186-191 | Abschnitt "Retention": "There is no long lived store of personal data beyond the active connections a user has chosen to keep" - das ist die zentrale falsche Aussage. 180 Tage sind ein langlebiger Speicher |
| `docs/uninstall.md` | 1 | Titel "Removing this app, and proving that nothing is left" |
| `docs/uninstall.md` | 151 | Abschnittstitel "What the occ way leaves behind: nothing" |
| `docs/uninstall.md` | 155-219 | Schritt 1, der Purge: die Feldtabelle der Antwort erklärt `tables_cleared` als "whether all seven tables were emptied", ohne zu sagen, dass es die sieben Tabellen des OAuth-Speichers sind und die Audit-Datei daneben liegen bleibt |
| `docs/uninstall.md` | 96-135 | Die acht Checks lesen `oauth.sqlite3` (Check 2). Es gibt keinen Check, der `audit.sqlite3` nennt, obwohl genau dessen Fortbestehen die neue Wahrheit ist |
| `docs/uninstall.md` | 229-241 | Die Gegenprüfungen nach `--rm-data` ("all measured, all empty") sind richtig, aber es fehlt der Satz, dass mit dem Volume auch das Log geht: das ist die benannte Ausnahme aus D-18 und der Restpunkt R-18-04 |
| `docs/uninstall.md` | 47 | Die Versionstabelle nennt für NC 32/33 "Delete data on remove" - dieser Weg entfernt das Volume ebenso, also auch das Log |
| `docs/faq.md` | 114-122 | "How do I remove the app and its data completely?" plus "empties every table of its database". Kandidat, den CONTEXT nicht nennt; Empfehlung: mitziehen, weil die Frageüberschrift das Wort "completely" trägt und die FAQ die kürzeste öffentliche Antwort ist |

`grep -ri audit docs/uninstall.md` findet heute **keinen** Treffer. Das ist der messbare Ausgangszustand für R-18-04.

### Changelog

`CHANGELOG.md` hat heute **keinen** `[Unreleased]`-Block: die Datei beginnt nach dem Kopf direkt mit `## [0.1.11] - 2026-08-28` (Zeile 12). Phase 16 hat den Block nicht geleert stehen gelassen, sondern in 0.1.11 überführt. Der Plan muss den Block also **neu anlegen**, nicht befüllen. Format: Keep a Changelog 1.1.0, Abschnitte `### Added` / `### Changed` / `### Fixed`, wie in den bestehenden Einträgen.

---

## Architecture Patterns

### System Architecture Diagram

```
Administrator an der Shell
        |
        | occ mcp_connector:audit:read --user alice --limit 200
        v
+-------------------------------------------------------------+
|  Nextcloud occ (Symfony Console)                            |
|  appinfo/register_command.php baut BEIM START alle          |
|  ExApp-Kommandos: ExAppOccService::buildCommand             |
|  -> configure(): addArgument/addOption aus dem Schema       |
|     (ein ungueltiger Modus wirft hier und legt occ still)   |
|  -> execute(): sammelt Argumente und Optionen               |
+-------------------------------------------------------------+
        |
        | PublicFunctions::exAppRequest(appid, handlerpfad,
        |   params={"occ": {"arguments": ..., "options": ...}},
        |   options={"stream": true, "timeout": 0})
        v
+-------------------------------------------------------------+
|  HaRP / AppAPI-Innenweg (kein Manifest-Eintrag noetig)      |
|  haengt gueltige AppAPI-Kopfzeilen selbst an                |
+-------------------------------------------------------------+
        |
        v
+-------------------------------------------------------------+
|  ExApp: neues Handlermodul exapp/audit_read.py              |
|                                                             |
|  1. Guard      x-origin-ip vorhanden? -> 404                |
|                require_appapi schlaegt fehl? -> 401         |
|                (keine Auskunft, welche Pruefung ablehnte)   |
|  2. Optionen   Rumpf <= 4096 Byte lesen, occ-Umschlag       |
|                oeffnen, Werte pruefen (isascii+isdigit)     |
|  3. Abfrage    store.read_entries(filter, limit)            |
|  4. Formung    nc_user klammern, Hashes hexen,              |
|                params als Liste durchreichen                |
|  5. Antwort    IMMER 200, text/plain oder JSONL,            |
|                Cache-Control: no-store                      |
+-------------------------------------------------------------+
        |
        v
+-------------------------------------------------------------+
|  audit/store.py  (SQLite, WAL, asyncio.to_thread)           |
|  NEU: read_entries(chain?, since?, until?, limit)           |
|  vorhanden: append, sweep, verify_chains, overview,         |
|             last_entry, drop_user_chain, size               |
+-------------------------------------------------------------+
        |
        v
   audit.sqlite3 im ExApp-Volume, neben oauth.sqlite3

Antwortweg zurueck: Rumpf wird von buildCommand in 1024-Byte-
Stuecken auf die Konsole geschrieben, aber NUR bei Status 200.
Rueckgabewert des Kommandos ist immer 0.

Parallel und ohne Codeweg dazwischen:

  Admin-Einstellungen (Declarative Settings, section security)
        ^
        | Titel + Beschreibung aus exapp/ui/strings.py,
        | Formular aus exapp/admin_settings.py (7 Felder,
        | audit_log default False, NIE sensitive)
        |
  Textflaeche:  appinfo/info.xml (EN/DE/FR)  ->  Store beim Upload
                README.md/.de/.fr            ->  Leser des Repos
                docs/privacy.md, uninstall.md, faq.md
                CHANGELOG.md [Unreleased]
        ^
        | gehalten von: Manifest-Gate (Rendering, Vokabular),
        |   Vokabular-Gate ueber READMEs + CHANGELOG + docs/**,
        |   NEU: Vier-Woerter-Gate mit derselben Reichweite
```

### Empfohlene Dateizuordnung

```
src/mcp_connector/
├── audit/
│   └── store.py              # NEU: read_entries() + Lesestatement
├── exapp/
│   ├── audit_read.py         # NEU: Handler, Pfadkonstante, Formung
│   ├── occ.py                # dritter Eintrag in command_schemes()
│   └── ui/strings.py         # Beschriftung erweitert, __all__ pflegen
├── entry_exapp.py            # audit_read_routes(...) in die Aufzaehlung
appinfo/info.xml              # sechster abwesender Pfad im Kommentar,
                              # Enterprise-Absatz x3, Version NICHT
docs/privacy.md               # zweite Datenbank, Retention, Purge
docs/uninstall.md             # Titel, Abschnitt, Checks, rm-data-Grenze
docs/faq.md                   # "completely"-Antwort praezisieren
README.md / .de.md / .fr.md   # Enterprise-Absatz
CHANGELOG.md                  # [Unreleased] NEU anlegen
tests/unit/
├── test_exapp_audit_read.py  # NEU, Muster: test_exapp_audit_verify.py
├── test_exapp_env_setup.py   # Vier-Woerter-Gate + Gegenprobe
├── test_exapp_admin_settings.py  # Beschriftungszusagen
└── test_audit_store.py       # read_entries: alle Pfade
```

### Muster 1: Drittes occ-Kommando am gemessenen Registrierungsmuster

**Was:** `command_schemes()` gibt eine Liste zurück, `register_occ_commands` schleift mit einem `try` je Kommando darüber, weil `OccCommandController::registerCommand` genau ein Kommando pro POST nimmt.
**Wann:** Immer, wenn ein Kommando hinzukommt.
**Belegt:** `registerCommand(string $name, string $description, string $execute_handler, int $hidden = 0, array $arguments = [], array $options = [], array $usages = [])` [VERIFIED: app_api v34.0.3, `lib/Controller/OccCommandController.php`]. `insertOrUpdate` keyed auf (appid, name), also idempotent [VERIFIED: `lib/Service/ExAppOccService.php:42-76`].

**Regeln, die aus dem Repo folgen:**
- `execute_handler` wird aus der Pfadkonstante abgeleitet (`PATH.removeprefix("/")`), nie zweitgeschrieben. `occ.py:30` begründet das: eine driftende Handlerangabe ist ein Kommando, das existiert, dokumentiert ist und am Tag des Bedarfs 404 antwortet.
- `"hidden": 0`, damit es in `occ list` steht.
- Registrierung nur im `enabled=1`-Zweig von `exapp/lifecycle.py`, in eigenem `try`; ein nicht leeres `error`-Feld dort schaltet die App sofort wieder ab (Fallstrick 11 aus Phase 2).
- Abmelden muss niemand: `ExAppService::unregisterExApp` ruft `unregisterExAppOccCommands($appId)` selbst.

### Muster 2: Optionen mit Wert und ihre Draht-Form

**Was:** AppAPI überträgt Argumente und Optionen als `{"occ": {"arguments": ..., "options": ...}}` im POST-Rumpf; die Flagge liegt eine Ebene unter der Spitze.
**Wann:** Bei jedem Handler, der Optionen liest.

**Die erlaubten Modi, an der Quelle gelesen** [VERIFIED: app_api v34.0.3, `lib/Service/ExAppOccService.php:217-256`]:

| Ort | Erlaubte `mode`-Werte | Kombinierbar? |
|-----|----------------------|----------------|
| Argumente | `required`, `optional`, `array` (unbekannt fällt auf `optional`) | ja, per Komma (`buildArgumentMode` macht `explode(',', $mode)`) |
| Optionen | `required`, `optional`, `none`, `array`, `negatable` (unbekannt fällt auf `none`) | **nein**, `buildOptionMode` macht kein `explode` |

**Was daraus folgt, und es ist die schärfste Regel dieser Phase:** eine Option mit `mode: "array"` wird zu `InputOption::VALUE_IS_ARRAY` **allein**, und Symfony wirft dafür `InvalidArgumentException('Impossible to have an option mode VALUE_IS_ARRAY if the option does not accept a value.')` [VERIFIED: symfony/console 7.3, `Input/InputOption.php:113`]. Diese Ausnahme entsteht in `configure()`, also in `buildCommand`, also in `appinfo/register_command.php`, und dort werden nur `NotFoundExceptionInterface|ContainerExceptionInterface` gefangen [VERIFIED: app_api v34.0.3, `appinfo/register_command.php:20,35`]. Ergebnis: **jeder** `occ`-Aufruf der Instanz bricht ab, nicht nur der eigene. Mehrwertige Optionen sind über AppAPI 34.0.3 nicht sicher registrierbar; wer mehrere Werte braucht, nimmt eine Option `optional` und trennt im Handler per Komma (dasselbe Muster, das `ADMIN_FIELD_ALLOWED_CLIENTS` für die Client-Liste fährt).

**Was bei einer Option je Modus im Rumpf ankommt:**

| Modus | Nicht gesetzt | Gesetzt |
|-------|---------------|---------|
| `none` | `false` | `true` |
| `optional` / `required` | der deklarierte `default`, sonst `null` | die Zeichenkette |

`_is_set` in `audit_verify.py:349-368` deckt die `none`-Form vollständig ab (bool, `None`, 1, Wortliste). Für Wert-Optionen braucht das neue Modul eine eigene, kleine Leseform: Wert holen, `None` als "Vorgabe" behandeln, Zeichenkette prüfen.

**Zweite Falle in derselben Datei:** bei Argumenten liest AppAPI `$argument['default']` unbedingt, sobald der Modus `optional` oder `array` ist (`in_array(...) ? $argument['default'] : null`, **ohne** `?? null`), während es bei Optionen `$option['default'] ?? null` schreibt. Ein `optional`-Argument ohne `default`-Schlüssel erzeugt damit eine PHP-Warnung pro occ-Start. Empfehlung: **keine Argumente registrieren**, nur Optionen; falls doch, immer `default` mitgeben.

### Muster 3: Lesen im Speicher, weil es dort heute keinen Weg gibt

**Was:** `AuditStore` hat `append`, `sweep`, `silent_users`, `drop_user_chain`, `last_entry`, `verify_chains`, `overview`, `size` und sonst nichts. Es gibt **keine** Methode, die Zeilen herausgibt.
**Wann:** Das Lesekommando braucht genau eine neue, und sie gehört in den Speicher, nicht in den Handler.

Vorgaben aus dem Modul, die sie erben muss:
- Statement aus `CANONICAL_FIELDS` zusammensetzen, nie eine handgeschriebene Spaltenliste (`store.py:288-291` begründet das).
- Jeder Wert als Platzhalter; nichts von einem Aufrufer im Statement.
- `_read(work)` als Weg (kein `BEGIN`, Arbeit in `asyncio.to_thread`).
- Ergebnis als `Entry`-Objekte über `_entry_of_row`, damit der Handler nicht die Spaltenordnung kennt. Wenn `seq`, `prev_hash` oder `hash` in die Ausgabe sollen (empfohlen: `seq` ja, die Hashes als Hex optional), braucht es eine eigene kleine Rückgabeform, weil `Entry` diese drei absichtlich nicht trägt.
- Hartes Vorgabelimit und ein Höchstlimit, das `--limit` nicht überschreiten kann. Bei 100 MB Speicher sind das nach der Messung in 18-RESEARCH.md §8 rund 440.000 Zeilen; ein Kommando, das die ohne Not alle in den Speicher zieht, ist ein Selbstschuss.
- Sortierung: `ORDER BY seq DESC` für die Leseansicht (neueste zuerst, was ein Administrator sucht), `ORDER BY seq ASC` für den Export (Reihenfolge der Kette). Der Plan soll das entscheiden und begründen, nicht offen lassen.

### Muster 4: Beschriftung, nicht Formular

**Was:** Das Formular ist fertig. `admin_settings.form_scheme()` baut die sieben Felder aus `CONFIG_KEYS`, `audit_log` ist Checkbox mit `"default": False` und trägt kein `sensitive`. Diese Phase ändert **nur** `ADMIN_FIELD_AUDIT_LOG_LABEL` und `ADMIN_FIELD_AUDIT_LOG_DESCRIPTION` in `exapp/ui/strings.py`.
**Wann:** Immer, wenn Text an der Oberfläche gemeint ist: `strings.py` ist die einzige Stelle, an der ein Satz steht, den ein Mensch liest (Modul-Docstring, Regel aus 03-UI-SPEC.md).

Was die neue Beschreibung tragen muss, aus CONTEXT und aus dem Review:
1. Was ein Eintrag enthält, **inklusive** Parameternamen, Ablehnungsgrund und Dauer (IN-06).
2. Was nie enthalten ist: Parameterwerte, Ergebnisinhalte, IP, User-Agent, Fehlermeldungstexte.
3. Die Grenzbeschreibung: was das Log nicht leistet. Der fertige Satz existiert schon als `audit_verify.LIMIT_SENTENCE` und darf inhaltlich nicht davon abweichen: die Prüfung findet eine unbemerkte Änderung, sie findet nicht, wer die Datei schreiben kann.
4. Dass ein nutzerbezogenes Protokoll mitbestimmungsrelevant sein kann (D-v1.5-04).
5. Dass es Purge und Deinstallation übersteht und wie lange es aufbewahrt wird.
6. Der Aktivierungszyklus, den jedes andere Feld dieses Formulars spricht: "A change takes effect after you disable and enable this app again."

Grenzen: kein Wort der Verbotsliste (ein Test hält das bereits, `test_exapp_admin_settings.py:335`), keine Stufe, kein `full`, kein Auswahlfeld. Neue Konstanten müssen in `__all__` von `strings.py`, sonst meldet das Dead-Code-Gate (`uv run vulture src scripts vulture_whitelist.py`).

### Muster 5: Vier-Wörter-Gate am bestehenden Vokabular-Gate

**Was:** Das Repo hat schon ein Wortlisten-Gate mit Reichweite und Gegenprobe:
- `FORBIDDEN_VOCABULARY = "archiv"`, ein Wort, casefold, als Substring [VERIFIED: `tests/unit/test_exapp_env_setup.py:1686`]
- `vocabulary_findings(text, name)` gibt eine Meldung je Zeile mit Datei und Zeilennummer [`:1993-2006`]
- `public_markdown_pages()` deckt `README.md`, `README.de.md`, `README.fr.md`, `CHANGELOG.md` und `docs/**/*.md` rekursiv ab, ausgenommen `docs/store-submission.md` [`:2009-2036`]
- `description_problems(root)` prüft dasselbe Wort über den Elementtext des Manifests ohne Kommentare [`:1730-1791`]
- Zu jedem Gate existiert eine Gegenprobe, die das Gate absichtlich rot macht [`:1942-1950`, `:2067-2083`]

**Wann:** Für die vier Wörter dieselbe Reichweite, dieselbe Meldungsform, eigene Gegenprobe.

**Zwei Entscheidungen, die der Plan treffen muss, weil eine naive Substring-Liste heute rot wird:**

1. **`siem` als Substring ist ein Falsch-Positiv-Generator.** `docs/spike-opendesk.md:1707` trägt "Audit-Log mit SIEM-Ausleitung" in einer offenen Verhandlungsfrage. Das ist ein internes Spike-Protokoll unter `docs/`, also in der Reichweite des bestehenden Gates. Drei Wege: (a) die Verbotsliste als Wortformen führen ("SIEM-zertifiziert" statt "siem"), (b) die Frage in `spike-opendesk.md` umformulieren, (c) eine zweite Ausnahme. Empfehlung: **(a)**, denn verboten ist die Behauptung, nicht das Wort. Ein Datenschutztext darf sagen, dass das Log keine SIEM-Anbindung hat.
2. **Deutsche Wortformen allein halten die englische und die französische Fläche nicht.** `revisionssicher`, `AI-Act-konform`, `DSGVO-konform`, `SIEM-zertifiziert` sind deutsche Zusammensetzungen; die Store-Beschreibung und die READMEs tragen die Behauptung notfalls als "GDPR compliant", "AI Act compliant", "tamper-proof", "conforme au RGPD". Empfehlung: die Liste je Behauptung mit ihren EN- und FR-Entsprechungen führen und als Regex mit optionalem Trennzeichen prüfen (`gdpr[\s-]*(compliant|konform)`), **nicht** als nacktes Substring: `compliant` und `conforme` kommen heute legitim vor (`docs/oauth-setup.md:204` "specification compliant client", `README.fr.md:68` "conforme à la spécification"). Die vier Wörter aus D-v1.5-02 sind das Minimum; strenger sein ist Claude's Discretion, laxer nicht.

Messung des Ausgangszustands: `revisionssicher`, `ai-act`, `dsgvo`, `gdpr` kommen in `docs/*.md`, `README*.md`, `appinfo/info.xml` und `CHANGELOG.md` heute **nicht** vor; `siem` genau einmal, an der oben genannten Stelle.

### Anti-Patterns to Avoid

- **Eine `<url>` für den Leseweg deklarieren.** Der PHP-Proxy hängt gültige AppAPI-Kopfzeilen selbst an; eine deklarierte Route legte das Protokoll aller Nutzer dieser Instanz ins Internet (T-02-20, T-18-07). Der `<url>`-Zähltest steht auf 13 und muss auf 13 bleiben (`test_exapp_audit_verify.py:211`).
- **Einen Fehlerstatus zurückgeben.** `buildCommand` verwirft den Rumpf bei jedem Status ausser 200 und schreibt "command executeHandler failed". Die Antwort wäre weg.
- **Eine mehrwertige Option registrieren.** Siehe Muster 2: das bricht die occ-Kommandozeile der ganzen Instanz.
- **`sensitive: true` an einem Formularfeld.** AppAPI verschlüsselt den Wert mit dem Servergeheimnis, die ExApp liest einen Blob, den sie nicht öffnen kann; beim Audit-Schalter wäre die Folge, dass er nicht einmal als "aus" lesbar wäre (T-05-05, T-18-19).
- **Die Version in `appinfo/info.xml` anheben oder einen `v*`-Tag setzen.** `release.yml` triggert auf `v*`; Milestone-Tags heissen `milestone-v*`. Diese Phase liefert nichts aus (D-v1.5-03).
- **Backticks, Tabellen, Bilder, horizontale Linien oder HTML in einer `<description>`.** Die Instanzansicht sanitisiert auf `h1..h6, strong, p, a, ul, ol, li, em, del, blockquote`; was mit Backtick oder Tabelle geschrieben ist, verschwindet dort ersatzlos, und ein einzelner Zeilenumbruch erzeugt keinen Umbruch (`breaks: false`). Absätze brauchen eine Leerzeile [VERIFIED: `test_exapp_env_setup.py:1730-1791`].
- **Den 0.1.10- oder 0.1.11-Changelog-Eintrag umschreiben.** Ein Release-Eintrag ist ein Datum. Der neue Stand gehört in `[Unreleased]`.
- **Die Vorgabeformulierung "einziger automatischer Löscher" wörtlich übernehmen.** Siehe §Drei automatische Löscher.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Optionswert aus dem occ-Umschlag lesen | Eigenen Rumpf-Parser mit `request.json()` | `bounded_body(request, 4096)` plus die Umschlagslogik aus `audit_verify._payload`/`_set_in` | Ein chunked Request kündigt keine Länge an; beide Stellen, die früher nur den Header prüften, hatten dieses Loch (IN-01 der Phase-5-Nachprüfung) |
| Zahl aus einer Option | `int(value)` | die Form von `config._bounded_number` (`isascii()` **und** `isdigit()`, dann Grenzen) | `"²".isdigit()` ist True und `int("²")` wirft; genau diese Falle ist als R-18-08 offen und darf nicht ein zweites Mal entstehen |
| Kontoname druckbar machen | Neuen Reiniger schreiben | Den bestehenden aus `audit_verify._printable` verwenden oder, besser, die drei divergenten Reiniger auf einen ziehen (R-18-06/IN-02) | Es gibt heute schon drei Fassungen mit zwei verschiedenen Regeln; eine vierte macht die Lage messbar schlechter |
| Zeitfenster filtern | `at`-Vergleich frei bauen | Die Präfix-Semantik von `_EXPIRED_PREFIX` verstehen, bevor gefiltert wird | `at` ist die Wanduhr beim Schreiben und kann nicht-monoton sein (WR-02, reproduziert). Für einen **Lesefilter** ist das harmlos, aber die Ausgabe muss dann nach `seq` sortieren, nicht nach `at`, sonst liest die Zeitachse falsch |
| Zeilen zählen | `SELECT COUNT(*)` neu schreiben | `AuditStore.overview()` | Liefert schon Ketten, Einträge, Grabsteine, erklärte Einträge, `used_bytes` und `sweepable_entries` in einem Lauf |
| Prüfen, ob der Text ein verbotenes Wort trägt | Neues Gate-Modul | Zweite Liste im bestehenden Vokabular-Gate | Reichweite, Meldungsform, Ausnahme und Gegenprobe existieren; ein zweites Modul wäre eine zweite Wahrheit über dieselbe Regel |
| Doku-Aussagen prüfen | Auf Disziplin verlassen | Das Muster von `test_the_privacy_doc_describes_the_clients_table_as_it_is` | Ein Test, der einen Satz an ein Codefaktum bindet, ist der einzige Weg, mit dem eine Doku-Wahrheit die nächste Phase überlebt |

**Key insight:** Diese Phase hat fast keinen erfinderischen Anteil. Fast alles, was sie braucht, existiert im Repo als Muster, das mindestens einmal gegen eine laufende Nextcloud gemessen wurde. Die Fehler, die hier möglich sind, entstehen nicht aus Unkenntnis der Domäne, sondern aus dem Nachbauen statt Wiederverwenden.

---

## Runtime State Inventory

Diese Phase ändert **registrierten Zustand** in Nextcloud, nicht nur Dateien im Repo. Deshalb ist die Aufstellung hier Pflicht.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | `audit.sqlite3` im ExApp-Volume. Schema unverändert, `CANONICAL_FIELDS` ist ab 18-01 fest und darf nicht wandern (der Hash rechnet darüber). Es gibt **keine** Datenmigration in dieser Phase | Nur Codeergänzung (neue Lesemethode). Keine Migration. Ein Plan, der eine Spalte hinzufügt, bricht jede bestehende Kette |
| Live service config | Drei Dinge liegen in der Nextcloud-DB und in keinem git: (1) die registrierten occ-Kommandos (`insertOrUpdate` je (appid, name), Cache-Schlüssel `/ex_occ_commands`), (2) das Declarative-Settings-Formular mit seinen Beschriftungstexten, (3) der Admin-Wert `audit_log` in `oc_appconfig_ex` | Beide Registrierungen laufen im `enabled=1`-Zweig: eine bestehende Installation sieht das neue Kommando und die neue Beschriftung **erst nach einem Deaktivieren-Aktivieren-Zyklus**. Das gehört in die Verifikationsschritte und in den Changelog-Eintrag |
| OS-registered state | Keins. Verifiziert: die App registriert keinen Cron, keinen Timer, keinen Dienst; der Aufräumlauf hängt am Schreibpfad (D-11, `should_sweep`), nicht an einer Uhr | Nichts |
| Secrets/env vars | `NC_MCP_AUDIT_LOG`, `NC_MCP_AUDIT_RETENTION_DAYS`, `NC_MCP_AUDIT_MAX_BYTES` werden vom Code gelesen, sind aber in `appinfo/info.xml` **nicht** deklariert. Der Deploy-Daemon injiziert nur deklarierte Variablen, verwirft undeklarierte wortlos. Kein Geheimnis, keine Umbenennung | Discretion (siehe Offene Frage 2). Falls deklariert: `test_every_variable_the_code_reads_is_declared_in_the_manifest` prüft Mengengleichheit gegen sechs Namen und muss auf neun erweitert werden; jede Variable braucht `display-name` **und** `description`; ein leeres `<default>` kommt als String `Array` im Container an und lässt den Store-Upload mit 500 scheitern |
| Build artifacts | `scripts/build_store_release.sh` kopiert `appinfo/info.xml`, `CHANGELOG.md`, `LICENSE`, `README.md` ins Store-Archiv. In dieser Phase wird kein Archiv gebaut und nichts hochgeladen (D-v1.5-03). Das Docker-Image bleibt unberührt | Nichts. Kein `build_store_release.sh`-Lauf, kein Tag, kein Upload |

Der kanonische Satz dazu: nachdem jede Datei im Repo geändert ist, tragen die Nextcloud-DB dieser Instanz das alte Kommandoschema und den alten Beschriftungstext weiter, bis die App einmal ab- und wieder angeschaltet wurde.

---

## Common Pitfalls

### Pitfall 1: Ein ungültiges Kommandoschema legt die occ-Kommandozeile der ganzen Instanz still

**Was geht schief:** Kein `occ`-Aufruf funktioniert mehr, auch keiner, der nichts mit dieser App zu tun hat.
**Warum:** `appinfo/register_command.php` baut beim Start jedes occ-Aufrufs **alle** ExApp-Kommandos über `buildCommand` und fängt dabei nur `NotFoundExceptionInterface|ContainerExceptionInterface`. Eine `InvalidArgumentException` oder `LogicException` aus Symfonys `configure()` reisst den Prozess mit [VERIFIED: app_api v34.0.3, `appinfo/register_command.php`].
**Wie vermeiden:** Optionen nur mit `mode` aus `{required, optional, none}`. Nie `array`. Nie `negatable` mit Wert. Keine Argumente (und wenn doch: `required` nie nach `optional`, `array` nur als letztes, `default` immer mitgeben). Ein Test soll das Schema gegen eine Positivliste erlaubter Modi halten, damit die Regel im Repo steht und nicht in dieser Datei.
**Warnzeichen:** Nach dem Aktivieren antwortet `occ list` mit einer PHP-Ausnahme statt mit einer Liste.

### Pitfall 2: Status ungleich 200, Urteil verloren

**Was geht schief:** Der Administrator liest "command executeHandler failed" und nichts weiter.
**Warum:** `buildCommand` prüft den Status, bevor es den Rumpf liest, und gibt bei allem ausser 200 den Rückgabewert 1 zurück, ohne ein Byte des Rumpfs auszugeben [VERIFIED: `ExAppOccService.php`].
**Wie vermeiden:** Auch der Fehlerfall antwortet 200 und trägt seine Aussage im Rumpf, genau wie `audit_verify` es tut (`:161-166`).
**Warnzeichen:** Ein Testfall, der 4xx oder 5xx erwartet.

### Pitfall 3: Der Rückgabewert ist immer 0

**Was geht schief:** Ein Überwachungsskript hält ein leeres oder fehlerhaftes Ergebnis für Erfolg.
**Warum:** Folge von Pitfall 2: wenn jede Antwort 200 ist, ist der Rückgabewert immer 0.
**Wie vermeiden:** Wie im verify-Kommando eine maschinenlesbare Form anbieten, in der ein Schlüssel die Aussage trägt (dort `broken`), und diesen Preis im Docstring benennen, nicht verstecken.

### Pitfall 4: Das Kommando erscheint nicht

**Was geht schief:** `occ list | grep mcp_connector` zeigt das neue Kommando nicht.
**Warum:** Die Registrierung läuft im `enabled=1`-Zweig. Ohne Deaktivieren-Aktivieren-Zyklus passiert nichts. Ausserdem liest `getOccCommands()` einen verteilten Cache, den nur `resetCacheEnabled()` leert - was `registerCommand` selbst tut, aber eben nur bei einer erfolgreichen Registrierung.
**Wie vermeiden:** Den Zyklus in die Verifikationsschritte schreiben und in den Changelog-Eintrag. `occ list` ist die Messung, nicht das Log.
**Warnzeichen:** Ein Log ohne Fehler und ein `occ list` ohne Treffer.

### Pitfall 5: Ein umbenanntes Kommando bleibt als Zombie stehen

**Was geht schief:** Zwei Kommandos in `occ list`, eins davon antwortet 404.
**Warum:** `insertOrUpdate` keyed auf (appid, name). Ein anderer Name ist ein anderer Datensatz, und der alte bleibt bis `unregisterExAppOccCommands` (also bis zum Abmelden der App).
**Wie vermeiden:** Den Namen einmal festlegen. Der Namensraum ist vorbereitet: `mcp_connector:audit:verify` existiert, `mcp_connector:audit:read` ist die erwartete Ergänzung (der Kommentar in `occ.py:81-83` sagt das ausdrücklich).

### Pitfall 6: Der Optionswert kommt anders als erwartet

**Was geht schief:** Der Filter greift nicht, oder das Vorgabelimit gilt nie.
**Warum:** Bei `mode: none` liefert Symfony `false`, wenn die Flagge fehlt. Bei `optional`/`required` liefert es den deklarierten `default` oder `null`. Der Rumpf trägt immer alle deklarierten Optionen, auch die nicht gesetzten.
**Wie vermeiden:** Jeden Wert prüfen: `null` heisst "Vorgabe", `false` heisst "Flagge nicht gesetzt", eine Zeichenkette heisst Eingabe von aussen. `_is_set` deckt nur den `none`-Fall ab und ist für Wert-Optionen der falsche Leser.

### Pitfall 7: Der Export zieht 440.000 Zeilen in den Speicher

**Was geht schief:** Der Container wächst, im schlechten Fall bis zum OOM, und AppAPI wartet dabei geduldig (`timeout => 0`).
**Warum:** Kein Limit, und 100 MB Speicher sind rund 440.000 Zeilen (Messung 18-RESEARCH.md §8).
**Wie vermeiden:** Vorgabelimit im Code, Höchstlimit über `--limit` nicht überschreitbar, und die Abfrage batchweise. Streaming ist möglich, aber in diesem Projekt nicht belegt (siehe Offene Frage 1).

### Pitfall 8: `nc_user` geht ungeklammert in die Ausgabe

**Was geht schief:** Ein Kontoname mit Steuerzeichen fälscht eine Zeile der Ausgabe.
**Warum:** `client_name` wird beim Schreiben zweimal gereinigt (`record._clamped_client_name`, `store._clean_client_name`), `nc_user` **nicht**: er kommt aus `request.state` und wird unverändert geschrieben. In `verify` wird er nur mittelbar über die Kettenkennung geklammert (`_printable`).
**Wie vermeiden:** Dieselbe Klammerung unmittelbar vor der Textausgabe. Bei JSONL ist die Zeileninjektion durch das JSON-Escaping erledigt, das Bidi-Risiko aus R-18-06 bleibt aber in beiden Formen.

### Pitfall 9: Neue Beschriftungskonstante wird als toter Code gemeldet

**Was geht schief:** `uv run vulture src scripts vulture_whitelist.py` wird rot.
**Warum:** Das CI fährt vulture mit voller Zuversicht. `strings.py` meldet sich über `__all__` frei, und der Modul-Docstring sagt das ausdrücklich.
**Wie vermeiden:** Jede neue Konstante in `__all__`, alphabetisch einsortiert.

### Pitfall 10: `sensitive` am Formularfeld

Siehe Anti-Patterns. Ein Test prüft es heute über `json.dumps(field).lower()` (`test_exapp_admin_settings.py:310`), also in jeder Schreibweise.

### Pitfall 11: Eine Stufe oder ein Auswahlfeld einbauen

**Was geht schief:** Erfolgskriterium 3 fällt.
**Warum:** Declarative Settings kennen `select`, `radio`, `multi-select`. Die Versuchung, `keys` und `full` als Auswahl anzubieten, ist technisch machbar und ausdrücklich verboten.
**Wie vermeiden:** Checkbox bleibt Checkbox. Ein Test soll belegen, dass das Wort `full` in keinem Oberflächentext und in keinem Feldtyp vorkommt.

### Pitfall 12: Der Grenzsatz der Beschriftung weicht vom Grenzsatz des Kommandos ab

**Was geht schief:** Zwei Orte sagen unterschiedlich viel über dasselbe.
**Warum:** `audit_verify.LIMIT_SENTENCE` steht in jeder Antwort des Prüfkommandos. Wenn die Formularbeschreibung eine andere Grenze zieht, hat der Administrator zwei Aussagen.
**Wie vermeiden:** Inhaltlich gleich, in der Formulierung frei. Ein Test kann die tragenden Begriffe beider Sätze abgleichen.

### Pitfall 13: `[Unreleased]` befüllen wollen, wo keiner ist

**Was geht schief:** Der Eintrag landet unter `## [0.1.11]` oder erzeugt eine kaputte Reihenfolge.
**Warum:** `CHANGELOG.md` beginnt nach dem Kopf mit `## [0.1.11] - 2026-08-28` (Zeile 12). Phase 16 hat den Block nach 0.1.11 überführt.
**Wie vermeiden:** Block neu anlegen, über 0.1.11, in der Form von Keep a Changelog 1.1.0.

### Pitfall 14: Substring-Verbot statt Behauptungsverbot

Siehe Muster 5, Punkt 1 und 2. `docs/spike-opendesk.md:1707` macht ein nacktes `siem` rot; `compliant` und `conforme` kommen legitim vor.

### Pitfall 15: Das Wort "Audit-Log" mit entfernen

**Was geht schief:** Der Anspruch, den D-v1.5-02 ausdrücklich hält, verschwindet aus dem Text.
**Warum:** Wer die Verbotsliste zu breit zieht, streicht am Ende auch das Wort, das bleiben soll.
**Wie vermeiden:** D-v1.5-02 sagt es wörtlich: die Verbotsliste gilt, und das Wort "Audit-Log" bleibt im Text.

### Pitfall 16: Der neue Text ist wieder unvollständig

Siehe §Drei automatische Löscher. Der Plan muss die Obergrenze nennen.

### Pitfall 17: Nur eine der sechs Enterprise-Stellen ziehen

Siehe §Fundstellen-Karte. `appinfo/info.xml` ×3 und `README*.md` ×3. Ein Test, der die drei Manifestsprachen gegen die drei READMEs auf gemeinsame Marker prüft, wäre die haltbare Form (Präzedenz: `test_every_description_carries_the_answer_of_the_faq` mit einem Markertripel je Sprache).

### Pitfall 18: Ein Doku-Test bricht, weil eine Zeile umformuliert wurde

**Was geht schief:** `test_the_privacy_doc_describes_the_clients_table_as_it_is` prüft eine Zeile, die mit `| Client registrations` beginnt, und verlangt darin "hash" und "never in the clear".
**Warum:** Die Tabelle "What the app stores" wird in dieser Phase erweitert.
**Wie vermeiden:** Die Zeile zu `Client registrations` unverändert lassen und neue Zeilen daneben stellen; oder den Test bewusst mitziehen und die Begründung im Plan festhalten.

### Pitfall 19: Version oder Tag anfassen

Siehe Anti-Patterns. `appinfo/info.xml` Version bleibt, `pyproject.toml` bleibt bei 0.1.11, kein `v*`-Tag.

### Pitfall 20: Die Werkzeugfläche wächst

**Was geht schief:** `scripts/check_tool_budget.py` wird rot.
**Warum:** Das Budget-Gate steht bei 21 Werkzeugen und 15712 Byte (nachgemessen im Phase-18-Audit, T-18-24).
**Wie vermeiden:** Das Lesekommando ist ein occ-Kommando und **kein** MCP-Werkzeug. Nichts wird am MCP-Serverobjekt registriert; die Route wird als Fabrik ausgegeben und in `entry_exapp` angehängt (D-23).

---

## Code Examples

### 1. Drittes Kommando im Registrierungsschema, mit Wert-Optionen

```python
# src/mcp_connector/exapp/occ.py, in command_schemes()
# Modi: nur "none", "optional" oder "required". NIE "array": buildOptionMode macht
# kein explode und VALUE_IS_ARRAY allein wirft in Symfony, was jeden occ-Aufruf der
# Instanz mitnimmt (app_api v34.0.3 register_command.php faengt das nicht).
{
    "name": OCC_AUDIT_READ_COMMAND_NAME,          # "mcp_connector:audit:read"
    "description": OCC_AUDIT_READ_DESCRIPTION,
    "hidden": 0,
    "arguments": [],                               # keine: der default-Zugriff von
                                                   # AppAPI hat bei Argumenten kein ?? null
    "options": [
        {
            "name": USER_OPTION,                   # "user"
            "mode": "optional",
            "description": OCC_AUDIT_READ_USER_DESCRIPTION,
            "default": None,                       # bei Wert-Optionen liest AppAPI
                                                   # $option['default'] ?? null
        },
        {
            "name": LIMIT_OPTION,                  # "limit"
            "mode": "optional",
            "description": OCC_AUDIT_READ_LIMIT_DESCRIPTION,
            "default": None,
        },
        {
            "name": JSON_OPTION,                   # "json", dieselbe Flagge wie in verify
            "mode": "none",
            "description": OCC_AUDIT_READ_JSON_DESCRIPTION,
        },
    ],
    "usages": [
        OCC_AUDIT_READ_COMMAND_NAME,
        f"{OCC_AUDIT_READ_COMMAND_NAME} --{USER_OPTION}=alice --{LIMIT_OPTION}=200",
        f"{OCC_AUDIT_READ_COMMAND_NAME} --{JSON_OPTION}",
    ],
    "execute_handler": OCC_AUDIT_READ_HANDLER,     # aus der Pfadkonstante abgeleitet
}
```

Quelle der Modi und der `default`-Asymmetrie: app_api v34.0.3, `lib/Service/ExAppOccService.php:135-155` und `:239-256`.

### 2. Einen Optionswert aus dem occ-Umschlag lesen

```python
# Der Umschlag ist gemessen: {"occ": {"arguments": null, "options": {...}}}
# (app_api v34.0.3, ExAppOccService::buildCommand). Anders als bei der Flagge kann
# hier None ankommen, und None heisst "nicht gesetzt", nicht "gesetzt ohne Wert".
def _value(payload: Any, name: str) -> str | None:
    """Der Wert einer Wert-Option, oder None fuer die Vorgabe."""
    if not isinstance(payload, dict):
        return None
    options = payload.get("options")
    if not isinstance(options, dict):
        options = (payload.get(OCC_ENVELOPE) or {}).get("options")
    if not isinstance(options, dict):
        return None
    value = options.get(name)
    # false ist die Antwort einer nicht gesetzten none-Option, nicht ein Wert.
    if value is None or value is False:
        return None
    return value.strip() or None if isinstance(value, str) else None


def _bounded_limit(raw: str | None) -> int:
    """Die Zahl hinter --limit, mit der Unicode-Falle abgesichert (R-18-08).

    isascii() UND isdigit(): "²".isdigit() ist True und int() wirft dann.
    Genau diese Pruefung fuehrt config._bounded_number, und genau sie fehlt heute
    in audit_verify._payload.
    """
    if raw is None or not (raw.isascii() and raw.isdigit()):
        return DEFAULT_LIMIT
    return min(int(raw), MAX_LIMIT)
```

### 3. Die neue Lesemethode im Speicher

```python
# src/mcp_connector/audit/store.py
# Spaltenliste aus CANONICAL_FIELDS, nie handgeschrieben (store.py:288-291).
# seq und die zwei Hashes kommen mit, weil eine Ausgabe ohne Nummer nicht
# nachvollziehbar ist und eine Kette ohne Hash nicht nachgerechnet werden kann.
_READ_ROWS = (
    f"SELECT {_COLUMNS}, prev_hash, hash FROM entries "  # noqa: S608 - Namen dieses Moduls
    "WHERE (? IS NULL OR chain = ?) AND (? IS NULL OR at >= ?) AND (? IS NULL OR at <= ?) "
    "ORDER BY seq DESC LIMIT ?"
)

async def read_entries(
    self,
    *,
    chain: str | None = None,
    since: int | None = None,
    until: int | None = None,
    limit: int = READ_LIMIT_DEFAULT,
) -> list[tuple[Any, ...]]:
    """Zeilen heraus, neueste zuerst, hoechstens ``limit``.

    Die einzige Methode dieses Moduls, die Inhalt einer Zeile herausgibt. Sie
    veraendert nichts und laeuft ohne eigene Transaktion, wie jede andere Leseform
    hier. ``limit`` ist gedeckelt und nie unbegrenzt: 100 MB sind rund 440.000
    Zeilen, und ein Kommando, das die alle in den Speicher zieht, nimmt den
    Container mit.

    Sortiert wird nach ``seq`` und nicht nach ``at``: ``at`` ist die Wanduhr beim
    Schreiben und kann nach einem Zeitsprung nicht-monoton sein (WR-02), waehrend
    ``seq`` die Reihenfolge der Kette ist.
    """
    bounded = max(1, min(limit, READ_LIMIT_MAX))

    def work(conn: sqlite3.Connection) -> list[tuple[Any, ...]]:
        return conn.execute(
            _READ_ROWS,
            (chain, chain, since, since, until, until, bounded),
        ).fetchall()

    return await self._read(work)
```

### 4. Eine JSONL-Zeile, ausgabefertig

```python
def _line(row: tuple[Any, ...]) -> str:
    """Eine Zeile des Exports: dieselben Feldnamen wie die kanonische Form.

    Drei Dinge passieren hier und nirgends sonst: der Kontoname wird geklammert
    (er ist der eine Wert von aussen, den der Speicher nicht reinigt, siehe
    record.py fuer client_name und store.py fuer die zweite Stufe), die zwei
    Hashes werden gehext (BLOB ist nicht JSON-faehig), und params wird als Liste
    durchgereicht statt als der JSON-Text, der in der Spalte steht.
    """
    entry = _entry_of_row(row)
    payload = {
        "seq": row[0],
        "chain": _printable(entry.chain),
        "kind": entry.kind,
        "at": entry.at,
        "nc_user": _printable(entry.nc_user or ""),
        "tool": entry.tool,
        "client_id": entry.client_id,
        "auth_id": entry.auth_id,
        "client_name": entry.client_name,   # beim Schreiben schon gereinigt
        "outcome": entry.outcome,
        "reason": entry.reason,
        "duration_ms": entry.duration_ms,
        "params": list(entry.params),        # Namen, nie Werte (D-06, AUDIT-01)
        "prev_hash": row[-2].hex(),
        "hash": row[-1].hex(),
    }
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
```

### 5. Die Beschriftung, mit allem was sie schuldet

```python
# src/mcp_connector/exapp/ui/strings.py
# Neu in __all__ eintragen, sonst meldet vulture sie als toten Code.
ADMIN_FIELD_AUDIT_LOG_LABEL = "Keep a record of tool calls"

#: Die lange Fassung, die Phase 18 ausdruecklich dieser Phase ueberlassen hat
#: (AUDIT-05, D-v1.5-02, D-v1.5-04). Sechs Dinge, und keines davon ist optional:
#: was eine Zeile enthaelt, einschliesslich der drei Felder, die die kurze Fassung
#: verschwieg (Parameternamen, Ablehnungsgrund, Dauer, Review-Befund IN-06); was
#: nie darin steht; was das Protokoll nicht leistet; die Mitbestimmungsrelevanz;
#: wie lange und wovon es ueberlebt; der Aktivierungszyklus.
ADMIN_FIELD_AUDIT_LOG_DESCRIPTION = (
    "With this on, every tool call is written down: ..."
    # Text ist Sache des Plans. Fest steht, was vorkommen muss und was nicht:
    # kein Parameterwert, kein Ergebnisinhalt, keines der vier verbotenen Woerter,
    # kein "full", keine Stufe.
)
```

### 6. Das Vier-Wörter-Gate, an das bestehende angehängt

```python
# tests/unit/test_exapp_env_setup.py, neben FORBIDDEN_VOCABULARY.
#
# Verboten ist die Behauptung, nicht das Wort: ein Datenschutztext darf sagen, dass
# dieses Log keine SIEM-Anbindung hat und dass die DSGVO den Betreiber betrifft.
# Ein nacktes Substring-Verbot waere heute rot in docs/spike-opendesk.md:1707
# ("SIEM-Ausleitung" in einer offenen Verhandlungsfrage) und wuerde "specification
# compliant" in docs/oauth-setup.md sowie "conforme a la specification" in
# README.fr.md mitnehmen.
#
# Die vier Ansprueche aus D-v1.5-02, je Sprache. Strenger als die Liste zu sein ist
# erlaubt, laxer nicht.
FORBIDDEN_CLAIMS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("revisionssicher", re.compile(r"revisionssicher|tamper[\s-]*proof|audit[\s-]*proof|inviolable", re.I)),
    ("AI-Act-konform", re.compile(r"ai[\s-]*act[\s-]*(konform|compliant|conforme)", re.I)),
    ("DSGVO-konform", re.compile(r"(dsgvo|gdpr|rgpd)[\s-]*(konform|compliant|conforme)", re.I)),
    ("SIEM-zertifiziert", re.compile(r"siem[\s-]*(zertifiziert|certified|certifie)", re.I)),
)


def claim_findings(text: str, name: str) -> list[str]:
    """Eine Meldung je Zeile und Anspruch, Datei und Zeile zuerst.

    Dieselbe Form wie vocabulary_findings, damit eine Verletzung eine
    Einzeilenkorrektur ist und keine Suche durch den Baum.
    """
    return [
        f"{name}:{number}: {claim}: {line.strip()}"
        for number, line in enumerate(text.splitlines(), start=1)
        for claim, pattern in FORBIDDEN_CLAIMS
        if pattern.search(line)
    ]


def test_no_public_text_carries_a_forbidden_claim(manifest_root: etree._Element) -> None:
    """Dieselbe Reichweite wie das Vokabular-Gate, plus den Elementtext des Manifests."""
    findings = [
        finding
        for page in public_markdown_pages()
        for finding in claim_findings(
            page.read_text(encoding="utf-8"), page.relative_to(ROOT).as_posix()
        )
    ]
    findings += claim_findings(element_text_without_comments(manifest_root), "appinfo/info.xml")

    assert findings == [], "; ".join(findings)


def test_the_claim_gate_fires_on_a_constructed_line() -> None:
    """Gegenprobe: ohne sie beweist der gruene Lauf oben nichts ueber das Gate."""
    for claim, _ in FORBIDDEN_CLAIMS:
        assert claim_findings(f"This log is {claim}.\n", "probe.md"), claim
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Ein occ-Kommando je App, Schema als Modulkonstante | `command_schemes() -> list[dict]`, ein POST je Kommando, ein `try` je Kommando | Plan 18-08 | Ein drittes Kommando ist ein Listeneintrag, keine Umbauarbeit |
| `/purge` als einziger absichtlich abwesender Handlerpfad | Fünf abwesende Pfade, jeder im Manifest-Kommentar benannt, jeder mit Test gegen die `<url>`-Liste | Plan 18-08 | Der sechste erbt Kommentarplatz und Testform |
| `AuditStore` schreibt und prüft | `AuditStore` schreibt, prüft, zählt und räumt auf; **liest aber nicht** | Phase 18 komplett | Die Lesemethode ist der einzige echte Neubau dieser Phase |
| Kurze Formularbeschreibung, lange Fassung vertagt | Die lange Fassung ist AUDIT-05 und wird hier fällig | Entscheid in `strings.py:642-648` | Die Vertagung ist im Code dokumentiert, inklusive der Begründung |
| Vokabular-Gate nur über das Manifest | Reichweite über READMEs, CHANGELOG und `docs/**` rekursiv, mit einer benannten Ausnahme und Gegenproben | SEC-02c, UF-3, Plan 12-03, Review WR-05 | Das Vier-Wörter-Gate braucht keine neue Infrastruktur |
| Docker Socket Proxy als Deploy-Weg | HaRP ab NC 32 empfohlen, DSP deprecated | vor Phase 1 | Nur relevant, weil HaRP undeklarierte Pfade blockt und der PHP-Proxy nicht: die Abwesenheit im Manifest ist die Kontrolle |

**Veraltet oder ausgelaufen:**
- Nichts in dieser Phase. Alle berührten Fremdschnittstellen (occ-Registrierung, Declarative Settings, Store-Rendering) sind gegen app_api v34.0.3 gemessen und unverändert seit Phase 18.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Ein Starlette-`StreamingResponse` kommt durch HaRP und AppAPI unverändert auf die Konsole (weil `exAppRequest` mit `stream => true` und `timeout => 0` läuft und `buildCommand` in 1024-Byte-Stücken liest) | Alternatives Considered, Pitfall 7 | Ein Export ohne `Content-Length` käme leer an oder würde abgeschnitten. Deshalb ist die Empfehlung ein Vorgabelimit mit gewöhnlicher Antwort, und Streaming ist ausdrücklich nicht Teil der Empfehlung |
| A2 | `occ` hat keine globale Option, die mit `user`, `limit`, `since`, `until` oder `format` kollidiert (die globalen sind `-h`, `-q`, `-v/-vv/-vvv`, `-V`, `-n`, `--ansi/--no-ansi`, `--no-warnings`) | Muster 2, Code-Beispiel 1 | Eine Namenskollision wirft in Symfonys `InputDefinition` und fällt damit in Pitfall 1. Prüfbar in einer Minute an einer laufenden Instanz mit `occ list --help`; der Plan soll das als Verifikationsschritt führen. Ein `shortcut` wird gar nicht gesetzt, was die grösste Kollisionsquelle ausschliesst |
| A3 | 180 Tage und 100 MB sind die tatsächlich wirksamen Vorgabewerte einer Installation, die nichts setzt | Drei automatische Löscher, Muster 4 | Der Text nennte falsche Zahlen. Belegt in `config.py:99-100` und `store.py:93,98`, aber die Env-Variablen können sie mit Untergrenze überschreiben: der Text muss "Vorgabe" sagen, nicht "immer" |
| A4 | Die vier Verbotswörter kommen in EN/FR-Fassungen der Behauptung vor, wenn sie irgendwo vorkommen | Muster 5, Punkt 2 | Ein Gate, das nur die deutschen Formen kennt, wäre grün, während die englische Store-Beschreibung "GDPR compliant" trägt. Die Regex-Liste ist die Absicherung, nicht die Verbotsliste selbst |
| A5 | `docs/faq.md:114-122` gehört mit in den Textnachzug | Fundstellen-Karte | Wird es weggelassen, bleibt die kürzeste öffentliche Antwort auf "wie werde ich alle Daten los" unvollständig. CONTEXT nennt die Stelle nicht; der Owner soll das im Plan bestätigen können |

---

## Open Questions

1. **Ein Kommando mit `--format` oder zwei Kommandos `:read` und `:export`?**
   - Was wir wissen: `mcp_connector:audit:` ist ausdrücklich als Namensraum für zwei Kommandos gebaut (`occ.py:81-83`). Jede Registrierung ist ein eigener POST mit eigenem `try`. Die etablierte Form für "dasselbe für eine Maschine" ist im verify-Kommando `--json`.
   - Was unklar ist: ob "liest und exportiert" (AUDIT-04) als zwei Kommandos gelesen werden soll.
   - Empfehlung: **ein** Kommando `mcp_connector:audit:read` mit `--json` als Exportform. Das erfüllt beide Verben, hält die Registrierungsfläche klein und erbt die Leseform von `_wants_json`. CSV kann später ein `--format`-Wert werden.

2. **Die drei Env-Variablen im Manifest deklarieren?**
   - Was wir wissen: `NC_MCP_AUDIT_LOG`, `NC_MCP_AUDIT_RETENTION_DAYS`, `NC_MCP_AUDIT_MAX_BYTES` werden vom Code gelesen und sind nicht deklariert; der Deploy-Daemon injiziert nur deklarierte Variablen. Der Weg des Administrators ist das Admin-Formular (BL-06). Der Test `test_every_variable_the_code_reads_is_declared_in_the_manifest` prüft Mengengleichheit gegen **sechs handgepflegte Namen**, nicht gegen einen Scan des Codes: sein Name ist weiter als seine Prüfung, deshalb ist er heute grün.
   - Was unklar ist: ob die Bequemlichkeit für Hand-Installationen den Preis wert ist (drei `<variable>`-Blöcke mit `display-name` und `description` in einer Datei, die sonst in dieser Phase nur zwei Absätze und einen Kommentar ändert).
   - Empfehlung: **ja, aber als eigener Plan-Task**, mit den drei Testanpassungen im selben Task. Begründung: die Aufbewahrungsfrist und die Obergrenze werden durch diese Phase erstmals öffentlich beschrieben; eine beschriebene Grenze, die ein Administrator nicht setzen kann, weil der Deploy-Daemon die Variable verwirft, ist eine halbe Zusage. Wenn der Owner das anders sieht, bleibt es ein Deferred Item und der Text sagt "Vorgabe", ohne einen Setzweg zu versprechen.

3. **Werden R-18-06/07/08 hier mitgenommen?**
   - Was wir wissen: R-18-08 (`isdigit` ohne `isascii`) ist eine Einzeilenkorrektur genau in der Datei, deren Zwilling hier entsteht, und das neue Modul würde die Falle sonst kopieren. R-18-06 (drei divergente Reiniger) berührt die Ausgabe dieser Phase unmittelbar; ein vierter Reiniger im neuen Modul macht die Lage schlechter. R-18-07 (`note()` vs `CancelledError`) liegt im Schreibpfad und hat mit dieser Phase nichts zu tun.
   - Empfehlung: **R-18-08 und R-18-06 ja, R-18-07 nein.** R-18-06 als ein gemeinsamer Reiniger in einem Blattmodul (`audit/text.py`), von allen drei bestehenden Stellen und der neuen genutzt; das ist genau der Vorschlag des Reviews. R-18-07 bleibt im Accepted Risks Log.

4. **Sortierung und Standardausschnitt der Leseansicht.**
   - Was wir wissen: Ein Administrator, der ein Kommando eintippt, sucht meist das Letzte. Ein Export, der weiterverarbeitet wird, braucht die Kettenreihenfolge. `at` ist nicht garantiert monoton (WR-02), `seq` ist es.
   - Empfehlung: Textausgabe `ORDER BY seq DESC` mit Vorgabelimit, JSONL-Ausgabe `ORDER BY seq ASC`. Beides ausdrücklich im Docstring begründen, damit es nicht als Inkonsistenz gelesen wird.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| uv | Alle Läufe (`uv run ruff`, `uv run pytest`, `uv run pyright`, `uv run vulture`) | ja | 0.11.7 | keiner nötig; System-Python ist projektweit als unbrauchbar dokumentiert |
| Python | Laufzeit | ja | 3.13.1 | - |
| ruff | Lint und Format-Gate | ja | 0.16.3 | - |
| pytest | Einheits- und Vertragstests | ja (im Lock) | - | - |
| pyright | Typprüfung im CI | ja (im Lock) | - | - |
| vulture | Dead-Code-Gate im CI | ja (im Lock, >=2.16) | - | - |
| lxml | Manifest-Gates | ja (im Lock) | - | - |
| Laufende Test-Nextcloud mit AppAPI (Docker) | Nur für einen echten `occ`-Lauf: Registrierung sichtbar machen, Optionsdraht bestätigen, Assumption A2 prüfen | **nein** (Topologie nach 06-07 heruntergefahren, siehe STATE.md; lokale Linux-Docker-Engine laut pytest-Konfiguration nicht verfügbar) | - | Vollständig durch Einheitstests am Handler abdeckbar (`TestClient` gegen die Fabrik, wie in `test_exapp_audit_verify.py`). Der Optionsdraht ist an der Quelle gelesen statt geraten. Der echte `occ`-Lauf gehört als Owner-Schritt in die Verifikation, nicht in den Plan |
| slopcheck | Paketprüfung | nicht geprüft | - | Nicht nötig: diese Phase installiert kein Paket |

**Missing dependencies with no fallback:** keine.

**Missing dependencies with fallback:**
- Laufende Test-Nextcloud: Einheitstests plus Quellenlesung decken alles ab, was ohne Instanz messbar ist. Ein Owner-Schritt "`occ list | grep mcp_connector:audit`, dann das Kommando einmal mit und ohne Optionen ausführen" gehört in die Phasen-Verifikation, ausdrücklich als hergeleitet gekennzeichnet, solange er nicht gelaufen ist (Präzedenz: R-18-05).

---

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | nein | Kein neuer Anmeldeweg; der Handler ist nur über den AppAPI-Innenweg erreichbar |
| V3 Session Management | nein | Kein Sitzungszustand; das Kommando läuft im App-Kontext mit leerer Nutzer-Id |
| V4 Access Control | **ja** | Kein `<url>` im Manifest (HaRP blockt undeklarierte Pfade, der PHP-Proxy nicht), Doppelprüfung `x-origin-ip` (404) dann `require_appapi` (401), ohne Auskunft welche Prüfung ablehnte. Der `<url>`-Zähltest bleibt bei 13 |
| V5 Input Validation | **ja** | Optionswerte sind Eingabe von aussen: `bounded_body(4096)`, `isascii()` + `isdigit()` vor jedem `int()`, jeder Wert als SQL-Platzhalter, Limit gedeckelt, Kontoname geklammert vor der Ausgabe |
| V6 Cryptography | nein | Keine neue Krypto. Die Kette bleibt SHA-256 über `CANONICAL_FIELDS`; nichts in dieser Phase rechnet oder ändert einen Hash |
| V7 Error Handling und Logging | **ja** | Nur `type(exc).__name__` ins Nextcloud-Log, nie die Meldung und nie ein Pfad (T-18-10). Antwort immer 200, Aussage im Rumpf |
| V8 Data Protection | **ja** | Die Ausgabe ist personenbezogen: Kontoname, Werkzeug, Client, Parameternamen. `Cache-Control: no-store` an jeder Antwort (der PHP-Proxy cachet sonst 3600 Sekunden). Kein Parameterwert, kein Ergebnisinhalt, keine IP, kein User-Agent |
| V14 Configuration | **ja** | Schalter ab Werk aus als positive Zugehörigkeitsprüfung (ein Tippfehler bleibt aus), Formularfeld `"default": False`, kein `sensitive` in irgendeiner Schreibweise |

### Known Threat Patterns for diesen Stapel

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Deklarierte Route stellt das Protokoll aller Nutzer ins Internet | Information Disclosure | Abwesenheit im Manifest ist die Kontrolle, plus Doppelprüfung im Handler, plus Test gegen die `<url>`-Liste (T-18-07, hier fortzuschreiben) |
| Kontoname mit Steuer- oder Bidi-Zeichen fälscht eine Ausgabezeile | Tampering | Klammerung unmittelbar vor der Ausgabe; die verbleibende In-Zeile-Grenze wird benannt und `--json` ist der Maschinenweg (T-18-08, Restrisiko R-18-06) |
| Unbegrenzter Export erschöpft den Speicher des Containers | Denial of Service | Vorgabelimit im Code, Höchstlimit über die Option nicht überschreitbar, batchweise Abfrage. AppAPI wartet mit `timeout => 0` beliebig lange, also schützt kein Zeitlimit von aussen |
| Ungültiges Kommandoschema legt die occ-Kommandozeile still | Denial of Service | Nur Modi aus einer Positivliste, keine Argumente, ein Test der das Schema gegen diese Liste hält |
| Rückgabewert 0 verdeckt ein Problem | Repudiation | Aussage im Rumpf, maschinenlesbarer Schlüssel, Preis im Docstring benannt (T-18-20) |
| Gefälschter Grabstein ist von einem echten nicht unterscheidbar | Spoofing | Akzeptiert und ausgeschrieben (D-v1.5-02, R-18-01). Die Grenzbeschreibung der Beschriftung muss inhaltlich dieselbe Grenze ziehen wie `audit_verify.LIMIT_SENTENCE` |
| Neue Datenerhebung ohne Zustimmung bei bestehenden Installationen | Compliance und Mitbestimmung | Ab Werk aus, ohne Schalter kein Rekorder, ohne Schalter und ohne bestehende Datei keine Datei; die Beschriftung nennt die Mitbestimmungsrelevanz (T-18-11, D-v1.5-04) |
| Öffentlicher Text behauptet mehr als der Code hält | Repudiation | Wörter-Gate mit Gegenprobe, plus Tests, die einzelne Doku-Sätze an Codefakten binden (Präzedenz `test_the_privacy_doc_describes_the_clients_table_as_it_is`) |

---

## Project Constraints (from CLAUDE.md)

| Direktive | Konsequenz für diese Phase |
|-----------|-----------------------------|
| Code und README auf Englisch, Projektkommunikation Deutsch | Neue Konstanten, Docstrings, Kommentare und Nutzertexte auf Englisch; Planungsartefakte deutsch |
| Keine Em-Dashes, echte Umlaute in deutschen Texten | Gilt für die DE-Fassungen von info.xml und README.de.md und für jedes Planungsdokument |
| Python 3.13 + uv als Toolchain (lokales System-Python defekt) | Jeder Lauf über `uv run` |
| MCP-SDK bleibt `mcp[cli]>=2.0,<3` | Unberührt: diese Phase fügt kein Werkzeug hinzu |
| AGPL-3.0, Repo public auf GitHub street1983nk (nicht Akara-GitLab) | Der Enterprise-Absatz darf kein exklusives Merkmal versprechen, das die AGPL nicht halten kann (offene Frage 3 aus `docs/spike-opendesk.md`) |
| Solo-Betrieb, Wartungsaufwand je Feature zählt | Ein Kommando statt zwei, eine Wortliste statt zweier Gate-Module, keine neue Abhängigkeit |
| Der MCP darf nie mehr sehen als der angemeldete Nutzer; keine destruktiven Writes in v1 | Das Lesekommando ist kein MCP-Werkzeug und läuft nicht im Nutzerkontext, sondern über occ; der Vertragstest gegen destruktive Aufrufe bleibt unberührt |
| GSD-Workflow: Änderungen über einen GSD-Befehl, nicht direkt am Repo | Diese Recherche schreibt genau eine Datei: `19-RESEARCH.md` |
| Keine Emojis | Gilt für alle Texte dieser Phase |
| Keine Claude-Attribution in Commits | Gilt für den Commit dieser Datei |

Zusätzlich, aus dem Projektgedächtnis und in dieser Phase ausdrücklich relevant:
- Milestone-Tags heissen `milestone-v*`, **nie** `v*` (release.yml triggert auf `v*`).
- Werkzeugoberfläche eingefroren: 21 Werkzeuge, 15712 Byte.
- Vokabular-Gate: das Wort "archiv" ist in öffentlichen Artefakten verboten, `CHANGELOG.md` eingeschlossen. Das Gate vor dem Push lokal laufen lassen.
- Doku-Seite mitziehen: nach einer Verhaltens- oder Textänderung die betroffenen Nutzertexte nachziehen.
- Nach jedem Edit committen.

---

## Sources

### Primary (HIGH confidence)

**Fremdkomponenten, an der Quelle gelesen (2026-08-31):**
- `nextcloud/app_api` v34.0.3, `lib/Service/ExAppOccService.php` - `registerCommand` (insertOrUpdate je appid+name), `getOccCommands` (Cache `/ex_occ_commands`), `buildCommand` (Umschlag `params.occ.arguments/options`, `stream => true`, `timeout => 0`, Statusprüfung vor dem Rumpf, 1024-Byte-Stücke, `is_resource`-Prüfung), `buildArgumentMode` (explode, Fallback `optional`), `buildOptionMode` (kein explode, Fallback `none`), `default`-Asymmetrie zwischen Argument und Option, `unregisterExAppOccCommands`
- `nextcloud/app_api` v34.0.3, `lib/Controller/OccCommandController.php` - Signatur `registerCommand`, keine Validierung der Modi
- `nextcloud/app_api` v34.0.3, `lib/Db/Console/ExAppOccCommand.php` - Entity, `json`-Typen, keine Pflichtschlüsselprüfung
- `nextcloud/app_api` v34.0.3, `appinfo/register_command.php` - baut alle ExApp-Kommandos beim occ-Start, fängt nur `NotFoundExceptionInterface|ContainerExceptionInterface`
- `symfony/console` 7.3, `Input/InputOption.php:102,113,116` - `Option mode "%s" is not valid`, `Impossible to have an option mode VALUE_IS_ARRAY if the option does not accept a value`, `VALUE_NEGATABLE`-Ausschluss
- `nextcloud/app_api` v34.0.3, `master`-Zweig derselben Dateien (Gegenprobe: Modi und Umschlag unverändert)

**Repo-Belege, Datei und Zeile:**
- `src/mcp_connector/exapp/audit_verify.py` (ganz) - Muster für Handler, Guard, Statuswahl, Klammerung, Optionsleseform
- `src/mcp_connector/exapp/occ.py` (ganz) - Registrierungsmuster, Namensraum, Ableitung des Handlernamens
- `src/mcp_connector/audit/store.py:84-134, 185-380, 383-473, 991-1134` - Konstanten, Schema, `CANONICAL_FIELDS`, Statements, Datenklassen, Lesemethoden, Verbindungspragmas
- `src/mcp_connector/audit/record.py:95-125, 200-290` - Sanitizer, `note`, `note_switch`
- `src/mcp_connector/exapp/admin_settings.py` (ganz) - sieben Felder, `sensitive`-Falle, kein Button-Typ
- `src/mcp_connector/exapp/ui/strings.py:1-27, 595-654` - Katalogregel, `__all__`, heutige Audit-Beschriftung samt Vertagungsbegründung
- `src/mcp_connector/entry_exapp.py:185-233, 288-350` - Routenaufzählung, Startlauf des Logs
- `src/mcp_connector/config.py:52-54, 96-111, 384-430` - Env-Namen, Vorgaben, Untergrenzen
- `appinfo/info.xml:1-40, 77-79, 119-124, 165-171, 260-300` - Rendering-Regeln, drei Enterprise-Absätze, Kommentar der abwesenden Pfade
- `docs/privacy.md:27-49, 155-191`, `docs/uninstall.md:1, 12-49, 79-155, 220-312`, `docs/faq.md:105-122` - die umzuschreibenden Aussagen
- `README.md:512-516`, `README.de.md:527-531`, `README.fr.md:545-549` - Enterprise-Absätze
- `CHANGELOG.md:1-60` - kein `[Unreleased]`, Format der bestehenden Einträge
- `tests/unit/test_exapp_env_setup.py:1670-1830, 1940-2084, 2157-2215` - Manifest-Gate, Vokabular-Gate mit Reichweite und Gegenproben, Env-Variablen-Mengengleichheit
- `tests/unit/test_exapp_audit_verify.py:1-142, 205-235` - Testmuster, `<url>`-Zähltest auf 13
- `tests/unit/test_exapp_admin_settings.py:284-360` - Zusagen an das Audit-Feld, bestehende Vier-Wörter-Prüfung
- `tests/unit/test_oauth_store.py:1490-1509` - Muster, eine Doku-Aussage an ein Codefaktum zu binden
- `.github/workflows/ci.yml:12-46`, `pyproject.toml:36-95` - Gate-Kette, Testpfade, vulture, ruff, pyright
- `scripts/build_store_release.sh:43-46` - Archivmitglieder

**Planungsartefakte:**
- `.planning/phases/18-audit-log-kern/18-CONTEXT.md` (D-01 bis D-18)
- `.planning/phases/18-audit-log-kern/18-SECURITY.md` (T-18-01 bis T-18-SC, R-18-01 bis R-18-08)
- `.planning/phases/18-audit-log-kern/18-REVIEW.md` (WR-01/02/03 gefixt, IN-01 bis IN-07 offen)
- `.planning/phases/18-audit-log-kern/18-RESEARCH.md:675-780` (Messung von `buildCommand`, Folgerungen)
- `.planning/phases/18-audit-log-kern/deferred-items.md` (Env-Variablen, flakiger Test)
- `.planning/REQUIREMENTS.md:12-17, 35-48, 86-91`, `.planning/ROADMAP.md:182, 214-228`, `.planning/STATE.md:670-700`

### Secondary (MEDIUM confidence)

- Messung des Ausgangszustands per grep in diesem Baum: die vier Verbotswörter kommen in den öffentlichen Texten nicht vor, `siem` genau einmal in `docs/spike-opendesk.md:1707`; `compliant`/`conforme` legitim in `docs/oauth-setup.md:204` und `README.fr.md:68`. Reproduzierbar, aber ein grep und kein Test
- Werkzeugstände lokal gemessen: `uv 0.11.7`, `Python 3.13.1`, `ruff 0.16.3`

### Tertiary (LOW confidence)

- Assumption A1 (StreamingResponse durch HaRP): hergeleitet aus `stream => true` und der Stückweise-Ausgabe, in diesem Projekt nicht gemessen. Die Empfehlung umgeht die Annahme statt sich auf sie zu stützen
- Assumption A2 (keine Kollision mit globalen occ-Optionen): aus Kenntnis der Nextcloud-CLI, in diesem Lauf nicht an einer Instanz geprüft. Als Verifikationsschritt vorgemerkt

---

## Metadata

**Confidence breakdown:**
- occ-Kommando, Modi, Draht-Form: **HIGH** - die drei entscheidenden PHP-Dateien von app_api v34.0.3 und `InputOption.php` von symfony/console sind gelesen, nicht erinnert
- Speicher und Lesemethode: **HIGH** - `store.py` vollständig durchgesehen; die Abwesenheit einer Lesemethode ist eine Messung, keine Vermutung
- Admin-Beschriftung: **HIGH** - Formular, Katalog, Zusagetests und der Vertagungsvermerk im Code gelesen
- Textnachzug und Fundstellen: **HIGH** - jede Fundstelle mit Datei und Zeile geprüft; der Widerspruch um die drei automatischen Löscher ist am Code belegt
- Wörter-Gate: **HIGH** für Muster und Reichweite (Gate gelesen), **MEDIUM** für den Zuschnitt der Regex-Liste (eine Entscheidung, die der Plan trifft)
- Grosse Exporte und Streaming: **LOW** - siehe A1, deshalb die Empfehlung mit Limit
- Kollisionsfreiheit der Optionsnamen: **LOW** - siehe A2, deshalb als Verifikationsschritt

**Nyquist-Validierung:** In `.planning/config.json` ist `workflow.nyquist_validation` auf `false` gesetzt, deshalb enthält dieses Dokument keine Validation-Architecture-Sektion. Die Gate-Kette des CI (`ruff check .`, `ruff format --check .`, `pyright`, `vulture`, `pytest tests/unit tests/contract`, `check_tool_budget.py`, `pytest -m matrix`) ist die Messlatte dieser Phase.

**Research date:** 2026-08-31
**Valid until:** 2026-09-30 (30 Tage: die gelesenen Fremdstände sind gepinnte Releases, app_api v34.0.3 und symfony/console 7.3; die Repo-Belege altern nur mit eigenen Commits)
