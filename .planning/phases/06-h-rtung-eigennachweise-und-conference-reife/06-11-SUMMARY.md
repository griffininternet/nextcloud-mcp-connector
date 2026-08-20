---
phase: 06-h-rtung-eigennachweise-und-conference-reife
plan: 11
subsystem: error-pages-and-decision-record
tags: [client-04, bl-14, d-35, error-page, e5, requirements, roadmap, docs, gap-closure]

# Dependency graph
requires:
  - phase: 06-08
    provides: "die Messung, auf der die Entscheidung beruht: Cursor 3.2.16 registriert sich mit 201 und wird an /authorize mit 400 abgewiesen, Ursache clientseitig belegt"
  - phase: 06-09
    provides: "die Loopback-Portregel, die diesen Fall nachweislich nicht trifft"
provides:
  - "ERROR_REDIRECT_BODY (E5) nennt den funktionierenden Weg (App-Passwort aus den Nextcloud-Sicherheitseinstellungen) und verraet weiterhin nicht, welche der vier Pruefungen fiel"
  - "ein Test, der beide Haelften haelt: der Weg wird genannt, kein Client-Scheme und keine Adresse stehen auf der Seite"
  - "BL-14 geschlossen: gewaehlte Option, Datum, Urheber, Messverweis und der Rohbeleg der SDK-Grenze fuer das bewusst nicht Getane"
  - "CLIENT-04 im Wortlaut des Gemessenen, als Owner-genehmigte Aenderung gekennzeichnet, abgehakt, Traceability Complete"
  - "ROADMAP Success Criterion 3 sagt dasselbe wie CLIENT-04; die Loopback-Haelfte ist Wort fuer Wort unangetastet"
  - "docs/client-setup.md mit dem D-35-Grund und dem Ausweichweg, docs/oauth-setup.md mit der getroffenen statt der offenen Entscheidung"
affects: [CLIENT-04, BL-14, D-35, 06-VERIFICATION]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Eine Absageseite darf einen Ausweg nennen, solange der Satz fuer alle Aufrufstellen derselben Seite gleich wahr ist: sonst ist er die Auskunft darueber, welche Pruefung fiel"
    - "Ein Ausweg auf einer Fehlerseite steht in Worten und nie als Link, weil der eine ausgehende Link dieser App die Anmeldeadresse ist, die Nextcloud selbst liefert"
    - "Eine offene Teilfrage einer Entscheidung wird vor dem Schreiben mit einem Kommando beantwortet, und das Ergebnis kommt als Rohbeleg in die Schliessung, nicht als Behauptung"
    - "Eine Requirement-Umformulierung wird nicht still gemacht: Datum, Urheber, gewaehlte Option und der Grund fuer die Aenderung stehen an jeder Stelle, die den Anspruch traegt"

key-files:
  created:
    - .planning/phases/06-h-rtung-eigennachweise-und-conference-reife/06-11-SUMMARY.md
  modified:
    - src/mcp_connector/exapp/ui/strings.py
    - tests/unit/test_oauth_ui.py
    - CHANGELOG.md
    - .planning/BACKLOG.md
    - .planning/REQUIREMENTS.md
    - .planning/ROADMAP.md
    - docs/client-setup.md
    - docs/oauth-setup.md

key-decisions:
  - "Der neue E5-Satz nennt kein Client-Scheme, keine Adresse und keinen Protokollwert und gilt fuer alle vier Aufrufstellen in consent.py gleich: ein Satz, der nur fuer eine davon wahr waere, ist genau die Auskunft, die T-03-24 verbietet"
  - "Der Ausweg steht in Worten und ohne URL, nach dem E8-Muster derselben Datei: ein erfundener Link waere die Phishing-Form, vor der der Fusstext jeder Seite warnt"
  - "Der Test prueft 'cursor' im Dokument OHNE Stylesheet: das CSS jeder Seite traegt eine cursor: pointer-Deklaration, die kein Nutzer liest und die nichts ueber einen Client sagt. Ohne diese Trennung waere der Test aus einem Grund rot, der nichts mit der Aussage zu tun hat"
  - "Das Zusatzfeld in der Registrierungsantwort wurde nicht gebaut, und der Grund ist gemessen und nicht geraten: OAuthClientInformationFull lehnt ein nicht deklariertes Attribut ab (ValueError) und model_validate verwirft einen unbekannten Schluessel still (mcp 2.0.0). Der Rohbeleg steht in BL-14"
  - "D-35, der Auth-Pfad und PROJECT.md sind unberuehrt: der Plan aendert keine Regel, keine Route, kein Schema und keinen Statuscode, belegt durch leere Diffs auf src/mcp_connector/oauth/ und .planning/PROJECT.md"
  - "Die drei READMEs und der Store-Text blieben unangetastet: ihre Cursor-Zeilen nennen die stdio-Konfiguration mit App-Passwort, also genau den Weg, der weiterhin funktioniert; damit entfaellt der EN/DE/FR-Nachzug"

patterns-established:
  - "Der Zustand einer geschlossenen Backlog-Frage steht im Titel UND in der STATUS-Zeile, und die Optionsliste bleibt vollstaendig stehen: sie ist das Protokoll, aus dem entschieden wurde"

requirements-completed: [CLIENT-04]

# Metrics
duration: 30min
completed: 2026-08-20
---

# Phase 06 Plan 11: CLIENT-04 Gap-Closure Summary

**Der eine Gap der Phase-6-Verifikation ist auf dem Weg geschlossen, den der Owner am
2026-08-20 entschieden hat: die Absageseite `E5` nennt jetzt den Weg, der funktioniert (ein
App-Passwort aus den Nextcloud-Sicherheitseinstellungen), ohne einen Protokollwert, eine
Adresse oder die gefallene Pruefung zu verraten; BL-14 ist mit gewaehlter Option, Datum,
Messverweis und dem Rohbeleg der SDK-Grenze geschlossen; CLIENT-04 und ROADMAP Success
Criterion 3 sagen beide das Gemessene und sind als Owner-genehmigte Aenderung gekennzeichnet;
beide Doku-Sektionen tragen den D-35-Grund, den Ausweichweg und die getroffene Entscheidung.
Keine Regel, keine Route, kein Schema, kein Statuscode wurde angefasst.**

## Performance

- **Duration:** 30 min
- **Tasks:** 3 von 3, Task 1 nach RED/GREEN
- **Files modified:** 8 (1 Modul, 1 Testdatei, CHANGELOG, 3 Planungsdateien, 2 Doku-Seiten)

## Task Commits

| Task | Name | Commit |
|------|------|--------|
| 1 RED | Der failing Test fuer den Ausweg auf der Absageseite | `710c44b` |
| 1 GREEN | E5 nennt den App-Passwort-Weg, plus CHANGELOG | `91a42ca` |
| 2 | BL-14 geschlossen, CLIENT-04 und ROADMAP SC3 auf das Gemessene | `4e26732` |
| 3 | Die zwei Doku-Sektionen: Grund, Ausweg, Entscheidung | `ffe4069` |

## Der neue Satz, woertlich

```
The address {client} asked us to return to does not match its registration. For your safety
nothing was shared. Start the connection again in your assistant app, and tell your
administrator if it keeps happening. Some assistant apps cannot use this sign in at all, and
for those the way in is an app password from your Nextcloud security settings.
```

Die drei alten Saetze stehen woertlich, inklusive "Start the connection again in your
assistant app", weil die Seiten-Tabelle in `tests/unit/test_oauth_ui.py` diesen Teilsatz
festnagelt. Was der neue Satz nicht enthaelt, geprueft und nicht behauptet: kein
Ausrufezeichen, kein `://`, kein Parametername, kein OAuth-Fehlercode, kein Client-Name und
kein Scheme. Die drei bestehenden parametrisierten Gates (`FORBIDDEN_ON_ERROR_PAGES`,
`FORBIDDEN_IN_ERROR_TEXT`, Status und genau ein `h1`) laufen unveraendert ueber `E5`.

## Die Messung vor dem Schreiben

Die offene Teilfrage des Owner-Entscheids ("koennte die Registrierungsantwort die verworfenen
Adressen benennen, erlaubt RFC 7591 das") wurde mit einem Kommando beantwortet, ohne Netz,
ohne Instanz, ohne Container. Ergebnis gegen `mcp 2.0.0`, identisch zur Erwartung aus dem
Planen:

```
SET REFUSED: ValueError "OAuthClientInformationFull" object has no field "dropped_redirect_uris"
EXTRA IN ANSWER: False
SDK model_config: {'url_preserve_empty_path': True}
```

RFC 7591 3.2.1 verlangt die registrierten Metadaten in der Antwort und verbietet
Erweiterungsfelder nicht, aber das Antwortmodell des SDK traegt kein Zusatzfeld. Der einzige
Weg dorthin waere ein Eingriff in die Registrierungsantwort auf dem Auth-Pfad, fuer ein Feld,
das kein gemessener Client liest. Das steht als Rohbeleg in der Schliessung von BL-14 und
nicht als Meinung.

## Abweichungen vom Plan

### 1. [Rule 3 - Blockierend] Das CSS jeder Seite traegt das Wort "cursor"

- **Gefunden in:** Task 1, beim ersten roten Lauf
- **Problem:** Der behavior-Block verlangt woertlich, dass das Wort "cursor" "im gesamten
  Dokument" nicht vorkommt. `src/mcp_connector/exapp/ui/layout.py:200` enthaelt
  `cursor: pointer;`, und das Stylesheet steht inline in jeder Seite. Der Test waere aus einem
  Grund rot gewesen, der nichts mit der Aussage zu tun hat, und ein Test, der aus dem falschen
  Grund faellt, schuetzt nichts.
- **Loesung:** Der Test prueft das Dokument ohne seinen `<style>`-Block, also weiterhin Markup
  und Attribute mit (ein Leck in einem Attribut bleibt ein Leck), und zusaetzlich direkt
  `strings.ERROR_REDIRECT_BODY`. Der Grund steht im Docstring des Tests, damit die naechste
  Aenderung ihn nicht fuer eine Schwaechung haelt.
- **Dateien:** `tests/unit/test_oauth_ui.py`
- **Commit:** `710c44b`

### 2. [Rule 2 - Owner-Regel] Zwei Em-Dashes in REQUIREMENTS.md

- **Gefunden in:** Task 2, beim Akzeptanzkriterium "keine Em-Dashes"
- **Problem:** Die Zeilen 1 und 5 von `.planning/REQUIREMENTS.md` trugen je ein `—` aus der
  Requirement-Definition vom 2026-08-20, also aus einer Aenderung vor diesem Plan. Das
  Kriterium verlangt 0 fuer die ganze Datei, und die Owner-Regel verbietet Em-Dashes
  ausnahmslos.
- **Loesung:** Beide durch Komma ersetzt, sonst kein Wort geaendert.
- **Dateien:** `.planning/REQUIREMENTS.md`
- **Commit:** `4e26732`

### 3. [Ausnahme, nicht behoben] Zwei Grep-Kriterien treffen Bestand aus fremden Aenderungen

- **Gefunden in:** Task 2 und Task 3
- **Problem und Befund:** Zwei Akzeptanzkriterien verlangen 0, treffen aber Zeilen, die
  dieser Plan nicht geschrieben hat und die nichts mit ihm zu tun haben:
  `grep -in "archiv" .planning/ROADMAP.md` trifft die Fusszeile "v1.0 archived: 2026-08-20"
  (das englische Wort, im Repo durchgehend so benutzt: `scripts/build_store_release.sh`,
  `.github/workflows/release.yml`), und
  `grep -inE "Bearer [A-Za-z0-9._-]{10,}" docs/client-setup.md` trifft Zeile 157 mit dem
  Platzhalter `Authorization: Bearer a-long-random-string`, also kein Credential.
- **Loesung:** Nicht angefasst, sondern benannt. Die von diesem Plan geschriebenen Zeilen
  sind in beiden Faellen sauber, belegt mit `git diff | grep "^+"`. Das Vokabular-Gate des
  Owners richtet sich gegen "Archiv" in deutschen oeffentlichen Artefakten, nicht gegen das
  englische "archive" in der Release-Werkzeugkette.
- **Dateien:** keine
- **Commit:** keiner

## Verifikation

| Kriterium | Beleg |
|-----------|-------|
| `'app password' in ERROR_REDIRECT_BODY`, `'Start the connection again'` erhalten, kein `!`, kein `://` | Kommando aus dem Plan, Rueckgabewert 0, voller Text ausgegeben |
| Kein Protokollwert im E5-Text (`redirect_uri`, `invalid_request`, `code_verifier`, `code_challenge`, `client_secret`, `cursor`) | Kommando gibt `clean` |
| Genau ein neuer Test | `grep -c "def test_the_return_address_page_names_the_way_that_works"` liefert 1 |
| Die drei bestehenden Gates laufen unveraendert ueber E5 | `grep -c '"E5", 400, strings.ERROR_REDIRECT_TITLE'` liefert 1; kein `FORBIDDEN`-Diff |
| Keine neue Konstante, `errors.py` und `vulture_whitelist.py` unberuehrt | `git diff --stat` leer, kein `+__all__`- und kein `+    "ERROR_`-Treffer |
| Auth-Pfad unberuehrt | `git diff --stat src/mcp_connector/oauth/` leer |
| CHANGELOG unter Unreleased | 9 neue Zeilen, `app password` im Unreleased-Block 2x |
| Alter Anspruch nirgends mehr | `grep -c "Autorisierung und Tool-Aufruf laufen durch"` liefert 0 in REQUIREMENTS.md und ROADMAP.md |
| CLIENT-04 abgehakt und gekennzeichnet | `grep -c "^- \[x\] \*\*CLIENT-04\*\*"` liefert 1, Zeile traegt "Owner-Freigabe" und "D-35" |
| Traceability | `| CLIENT-04 | Phase 6 | Complete |` 1x, `Pending` 0x; Coverage-Zeile und "Last updated" nachgezogen |
| Falsche Out-of-Scope-Aussage weg | `grep -c "Cursor kommt über die Teilregistrierung herein"` liefert 0; die Zeile nennt jetzt das App-Passwort |
| ROADMAP SC3 | "Owner-Freigabe" 1x; Loopback-Haelfte woertlich erhalten (`grep -c "RFC-8252-7.3-Ausnahme umgesetzt oder als benanntes Risiko akzeptiert"` liefert 1); Planliste abgehakt |
| BL-14 geschlossen | Titel traegt `CLOSED 2026-08-20`, STATUS-Block mit Datum (3 Treffer), `06-08-MEASUREMENTS.md` 2x, `OAuthClientInformationFull` 3x, Code-Block vorhanden, die vier Optionen unveraendert (4 Treffer) |
| Doku: keine offene Entscheidung mehr | `grep -c "is an open decision" docs/oauth-setup.md` liefert 0; `2026-08-20` 6x; `BL-14` 1x |
| Doku: D-35-Grund auf der Client-Seite | `grep -c "owns a scheme exclusively" docs/client-setup.md` liefert 1 |
| Seite und Doku benennen denselben Weg | Konsistenz-Kommando gibt `consistent`; `app password` 25x in client-setup.md, 12x in oauth-setup.md |
| Gemessene Rohwerte unangetastet | `grep -c "15:26:39  POST 201  /register" docs/oauth-setup.md` liefert 1; `06-08-MEASUREMENTS.md` in client-setup.md 1x |
| Dreisprachiges, Store-Text, Abhaengigkeiten, D-35 | `git diff --stat README.md README.de.md README.fr.md appinfo/info.xml pyproject.toml uv.lock .planning/PROJECT.md src/mcp_connector/oauth/` leer |
| Tests | `uv run --no-sync pytest tests/unit` 2165 passed; `tests/contract` gruen (Tool-Surface und Destruktiv-Gate) |
| Lint | `ruff check .` und `ruff format --check .` sauber, 173 Dateien |
| Em-Dashes in allen geaenderten Dateien | 0 |

## Was dieser Plan nicht tut

- **Keine Aenderung an D-35.** Private-use Schemes bleiben unregistrierbar, `.planning/PROJECT.md` ist unberuehrt.
- **Kein Eingriff in den Auth-Pfad.** Keine Route, kein Schema, kein Statuscode, keine neue Konstante; `src/mcp_connector/oauth/` hat einen leeren Diff.
- **Kein Zusatzfeld in der Registrierungsantwort.** Gemessen begruendet und in BL-14 protokolliert, nicht stillschweigend weggelassen.
- **Kein Release.** Ein 0.1.3 traegt diesen Text erst, wenn der Owner es freigibt (CONTEXT.md, Deferred Ideas).
- **Keine Aenderung an den drei READMEs und am Store-Text.** Ihre Cursor-Zeilen nennen die stdio-Konfiguration mit App-Passwort, und das ist weiterhin der Weg, der funktioniert.

## Known Stubs

Keine.

## Threat Flags

Keine neue Angriffsflaeche. Die vier Register-Einträge des Plans sind eingehalten:

- **T-06-60 (Information Disclosure, E5-Text):** der neue Satz nennt keinen Protokollwert, keinen Parameternamen, keine Adresse und kein Scheme und ist fuer alle vier Aufrufstellen in `consent.py` gleich wahr; die bestehenden Gates plus ein neuer Test halten das.
- **T-06-61 (Spoofing, dieselbe Seite):** kein Link, keine URL, kein erfundener Klickpfad; der Weg steht in Worten.
- **T-06-62 (Tampering, Auth-Pfad):** leerer Diff auf `src/mcp_connector/oauth/`.
- **T-06-63 (Repudiation, Planungsdateien):** Datum, Urheber, gewaehlte Option und der Grund der Wortlaut-Aenderung stehen in BL-14, in REQUIREMENTS.md und in ROADMAP.md; die vier Optionen von BL-14 bleiben als Protokoll stehen.
- **T-06-64 (Information Disclosure, oeffentliche Planungsdateien):** der Rohbeleg enthaelt kein Credential und keine Instanzadresse.
- **T-06-SC (Supply Chain):** kein Paket installiert, `pyproject.toml` und `uv.lock` unveraendert.

## Requirements

- **CLIENT-04 abgehakt**, im Wortlaut des Gemessenen und als Owner-genehmigte Aenderung gekennzeichnet: DCR mit Cursors Drei-URI-Body wird 201 mit den zwei zulaessigen Adressen; die Anmeldung scheitert an Cursors eigener private-use-Adresse; die Ursache ist clientseitig belegt; der funktionierende Ausweichweg ist dokumentiert und wird auf der Absageseite genannt.

## Self-Check: PASSED

- `06-11-SUMMARY.md` liegt auf der Platte.
- Die vier Commits `710c44b`, `91a42ca`, `4e26732` und `ffe4069` sind in `git log`.
</content>
</invoke>
