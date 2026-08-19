---
phase: 05-hardening-und-store-einreichung
plan: 09
subsystem: docs
tags: [faq, store-description, manifest, i18n, gate, vokabular, deferred-item]

# Dependency graph
requires:
  - phase: 04-per-user-verwaltung-und-prepare-context
    provides: "der Schalter pro Konto auf /connections und das Trennen je Verbindung mit Rueckgabe des App-Passworts (D-47, D-48, live belegt in 04-04)"
  - phase: 05-hardening-und-store-einreichung
    provides: "05-02 die Durchsetzung des Schalters an den drei Punkten, an denen eine Verbindung entsteht (E9 PAUSED); 05-06 das occ-Kommando mcp_connector:purge und die korrigierte Loeschzusage in docs/privacy.md"
provides:
  - "docs/faq.md: die kanonische, englische FAQ mit der Nutzerfrage als erstem Eintrag und einem Administrator-Abschnitt, der weitere Fragen aufnimmt"
  - "ein kurzer ## FAQ-Abschnitt in README.md, README.de.md und README.fr.md, an derselben Position der Abschnittsfolge"
  - "ein Status-Abschnitt in drei Sprachen, der den heutigen Stand nennt statt phase 1 (server core)"
  - "drei Store-Beschreibungen auf dem kleineren gemeinsamen Nenner der Instanz-Ansicht, mit der FAQ-Antwort im Text selbst"
  - "description_problems(): Gate auf Backticks, Tabellen, Bilder, horizontale Linien, HTML, Absatztrennung, summary-Laenge und das Vokabular-Verbot"
  - "variable_problems(): Gate gegen ein leeres <default> im Manifest"
affects: [05-10, appinfo/info.xml, README, docs/faq.md]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ein Textgate liest den geparsten Baum und ueberspringt Kommentarknoten, damit die erklaerenden Kommentare des Manifests das Gate nicht selbst ausloesen"
    - "Kanonische Fassung in einer Sprache plus dreisprachige Kurzform mit Link, statt drei vollstaendiger Uebersetzungen einer wachsenden FAQ"
    - "Die Antwort steht im Store-Text selbst und wird zusaetzlich verlinkt, weil der Store-Text der einzige Ort ohne Repository-Besuch ist"

key-files:
  created:
    - docs/faq.md
  modified:
    - README.md
    - README.de.md
    - README.fr.md
    - appinfo/info.xml
    - tests/unit/test_exapp_env_setup.py

key-decisions:
  - "Die FAQ ist einsprachig kanonisch (Englisch) und dreisprachig kurz zitiert: bei fuenf Fragen kostet jede Aenderung sonst sechs Textstellen (05-RESEARCH Open Question 2, Empfehlung uebernommen)"
  - "Die Store-Beschreibung traegt die Antwort selbst und verlinkt nur zusaetzlich; ein Link allein waere fuer den einen Ort, den ein Nutzer ohne Repository sieht, keine Antwort"
  - "Das Tabellen-Gate verbietet jedes Pipe-Zeichen statt nur die Trennzeile: eine Trennzeile ohne Zeilen daneben gibt es nicht, und eine Zeile mit Pipe ist im Beschreibungstext immer eine Tabelle"
  - "Das Vokabular-Gate liest den geparsten Baum ohne Kommentarknoten, nicht die Datei: das Manifest erklaert in Kommentaren genau die Faelle, die ein grep als Verstoss lesen wuerde"
  - "Das Variablen-Gate verbietet nicht das Element <default>, sondern nur das leere: ein befuellter Default ist erlaubt, und ein Test haelt diese Haelfte fest, damit die Regel nicht ueberschiessend wird"
  - "Der Status-Abschnitt nennt vier Fakten mit Fundstelle statt einer Phasennummer: eine Phasennummer veraltet mit jedem Plan, eine Fundstelle nicht"
  - "Version, image-tag und dependencies in appinfo/info.xml blieben unberuehrt; sie gehoeren zu Plan 05-10"
  - "CHANGELOG.md wurde nicht angefasst: der Eintrag zu diesen Texten gehoert in den Release-Schritt, damit er die Version traegt, unter der sie ausgeliefert werden (05-10)"

patterns-established:
  - "Oeffentlicher Text bekommt ein maschinelles Gate mit Gegenprobe, nicht nur eine Review-Notiz"
  - "Ein Gate, das Text zaehlt, liest Elementtext und nie die Rohdatei, solange die Datei Kommentare fuehrt, die dieselben Worte nennen"

requirements-completed: []  # EXAPP-04 bleibt Pending (Store-Einreichung, Plan 05-10); EXAPP-05 war seit 05-07 Complete

# Metrics
duration: 15min
completed: 2026-08-19
---

# Phase 05 Plan 09: FAQ und Store-Text Summary

**Die Frage, ob ein Nutzer die App fuer sich abschalten kann, ist jetzt dort beantwortet, wo er sie stellt: kanonisch in `docs/faq.md`, kurz in drei READMEs und im Wortlaut in allen drei Store-Beschreibungen, die dafuer so umgeschrieben wurden, dass die Filterliste der Instanz-Ansicht nichts davon wegwirft.**

## Performance

- **Duration:** 15 min
- **Started:** 2026-08-19T19:07:00Z
- **Completed:** 2026-08-19T19:22:00Z
- **Tasks:** 2 von 2
- **Files modified:** 6 (1 neu, 5 geaendert)

## Accomplishments

- **`docs/faq.md` existiert und beantwortet die Owner-Frage aus belegten Fakten.** Drei Fakten und eine Grenze: der Connector handelt nur auf Anfrage (kein Cron, keine Indizierung, keine Telemetrie), es gibt einen Schalter pro Konto auf der Verbindungsseite, die Nextcloud unter Einstellungen, Sicherheit, MCP Connector verlinkt, und jede Verbindung ist einzeln trennbar mit Rueckgabe des Nextcloud-App-Passworts. Die Grenze nennt den Anbieter der Assistenz und verweist auf `docs/privacy.md`; der Administrator-Teil verweist auf `docs/uninstall.md` und sagt woertlich, dass der Remove-Knopf auf Nextcloud 34 nur deaktiviert.
- **Die Datei hat eine Struktur, die waechst, ohne umgebaut zu werden.** Zwei Ebenen (`## For users`, `## For administrators`), jede Frage eine `###`-Ueberschrift. Der Administrator-Abschnitt traegt schon zwei Fragen (die Pflichtvariable und der vollstaendige Purge in der richtigen Reihenfolge), beide als Verweis auf die Datei, die die Substanz haelt, nicht als zweite Wahrheit daneben.
- **Drei READMEs haben an derselben Position einen `## FAQ`-Abschnitt.** Direkt nach dem OAuth-2.1-Unterabschnitt und vor dem Schnellstart, also im oberen Drittel: Frage in Fettschrift, Kurzantwort in einem Absatz, Link auf die kanonische Fassung. `README.de.md` mit echten Umlauten, `README.fr.md` mit Accents und Cedille, kein Em-Dash in einer der vier Dateien.
- **Der Status-Abschnitt sagt nicht mehr "phase 1 (server core)".** Nach vier Phasen und einem Release stand das in der ersten Zeile, die ein Besucher liest, und in allen drei Sprachen. Der neue Text nennt vier nachpruefbare Fakten mit Fundstelle: 16 Werkzeuge (Contract-Test gegen die laufende Registry), OAuth 2.1 gegen Claude.ai und ChatGPT belegt (`docs/oauth-setup.md`), Verwaltung pro Konto, `prepare_context`. Keine Zahl ohne Quelle im Repo, kein Werbeversprechen.
- **Der Nebenbefund aus 05-07 ist mit erledigt.** `deferred-items.md` notierte "15 tools" an zwei Stellen im README; korrekt sind 16, seit `prepare_context` in Phase 4 dazukam. Behoben in allen drei Sprachfassungen. Die beiden datierten Messprotokoll-Zeilen in `docs/oauth-setup.md` und `docs/spike-discovery.md` bleiben bewusst unberuehrt, so wie der Eintrag es begruendet.
- **Die drei Store-Beschreibungen ueberleben die Instanz-Ansicht.** Vorher vier Saetze mit einfachen Zeilenumbruechen, was bei `breaks: false` ein einziger Klumpen ist. Jetzt fuenf durch Leerzeilen getrennte Absaetze je Sprache, ohne Backtick, Tabelle, Bild, horizontale Linie oder HTML, mit der FAQ-Antwort in drei Saetzen im dritten Absatz und zwei Markdown-Links im letzten. `summary` bleibt in allen drei Sprachen deutlich unter 128 Zeichen (72, 76, 73).
- **Zwei Gates halten beides fest, jedes mit Gegenprobe.** `description_problems()` prueft je Sprachfassung Backtick, Pipe, Bild, horizontale Linie, HTML, mindestens zwei durch Leerzeile getrennte Absaetze, die `summary`-Laenge und das Vokabular-Verbot; `variable_problems()` verbietet ein leeres `<default>`. Sechs Gegenproben belegen, dass die Gates ausloesen: Backtick und Tabelle, einfache Zeilenumbrueche, HTML plus Bild plus Linie, eine zu lange `summary`, das verbotene Wort, und das leere `<default>`. Ein siebter Test belegt die andere Haelfte der Variablenregel, naemlich dass ein befuellter Default erlaubt bleibt.
- **Ein dritter Test prueft, dass die Antwort wirklich in jeder Sprache steht.** Je Sprachfassung drei Marker, einer pro Fakt (`background`/`Hintergrund`/`arrière-plan`, `switch`/`Schalter`/`interrupteur`, `disconnect`/`trenn`/`déconnect`). Damit kann eine Uebersetzung nicht still einen der drei Fakten verlieren.

## Task Commits

| Task | Name | Commit | Dateien |
|------|------|--------|---------|
| 1 | Die kanonische FAQ und die drei READMEs | `698db7a` | `docs/faq.md` (neu), `README.md`, `README.de.md`, `README.fr.md` |
| 2 (RED) | Die beiden Gates, zuerst rot | `1e9bcef` | `tests/unit/test_exapp_env_setup.py` |
| 2 (GREEN) | Die dreisprachige Store-Beschreibung | `d323315` | `appinfo/info.xml` |

## TDD Gate Compliance

Task 2 lief als vollstaendiger RED/GREEN-Zyklus. RED (`1e9bcef`) liess genau zwei Tests fehlschlagen, und beide waren die neue Aussage: `test_the_manifest_text_passes_its_own_gate` fand drei Absatzverstoesse (eine Sprachfassung je ein Klumpen) und `test_every_description_carries_the_answer_of_the_faq` fand keinen der Marker. Alle sechs Gegenproben und das Variablen-Gate waren im RED-Lauf schon gruen, und das ist die richtige Farbe: das Manifest fuehrte nie ein `<default>`, das war der dokumentierte sichere Zustand, und dieses Gate friert ihn ein statt ihn herzustellen. GREEN (`d323315`) machte beide rot gewesenen Tests gruen, ohne eine Zeile eines Gates zu aendern. Ein REFACTOR-Schritt war nicht noetig.

## Verification

```
uv run --no-sync pytest tests/unit/test_exapp_env_setup.py -q   132 passed
uv run --no-sync pytest -q                                      alle gruen (100%)
uv run --no-sync ruff check .                                   All checks passed
uv run --no-sync ruff format --check .                          165 files already formatted
```

Zusaetzlich geprueft:

| Kriterium | Befund |
|-----------|--------|
| `grep -c 'phase 1 (server core)'` in den drei READMEs | 0, 0, 0 |
| `## FAQ` je README | 1, 1, 1 |
| Em-Dash oder En-Dash in den vier Textdateien | 0 |
| Umlaute im neuen DE-Abschnitt, Accents im neuen FR-Abschnitt | 6 bzw. 9 Zeilen mit Treffern |
| `15 tools` / `15 Tools` / `15 outils` in den READMEs | keine mehr |
| Wort `archiv` in `appinfo/info.xml`, case-insensitiv | 0 |
| Absaetze je Beschreibung, Backticks, Pipes | 5 / 0 / 0 in allen drei Sprachen |
| `summary`-Laenge en, de, fr | 72, 76, 73 von 128 erlaubten |
| `version` und `image-tag` in `appinfo/info.xml` | 0.1.0 und 0.1.0, unveraendert |
| Routen-Gate mit dreizehn Routen | unveraendert gruen |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Fehlende kritische Korrektheit] Die veraltete Werkzeugzahl in allen drei READMEs**

- **Found during:** Task 1
- **Issue:** `deferred-items.md` notierte den Fund aus 05-07: `README.md` nannte zweimal "15 tools", waehrend die laufende Registry und `tests/contract/test_tool_surface.py` 16 kennen. Die beiden Uebersetzungen trugen dieselbe Zahl.
- **Fix:** In allen drei Sprachfassungen auf 16 korrigiert, einmal im Einleitungsabsatz und einmal im neuen Status-Abschnitt. Der Auftrag dieses Plans deckt es: `README.md`, `README.de.md` und `README.fr.md` stehen in `files_modified`, und der Eintrag in `deferred-items.md` nennt 05-09 als den Ort, an den der Fund gehoert.
- **Files modified:** `README.md`, `README.de.md`, `README.fr.md`
- **Commit:** `698db7a`

### Bewusste Auslegungen

- **Der Verweis auf `docs/uninstall.md` steht, obwohl die Datei noch fehlt.** Plan 05-08 legt sie an und laeuft in derselben Wave; der Plan sieht diesen Fall vor und schreibt vor, den Verweis trotzdem zu fuehren. Die Runbook-Beschreibung in der FAQ stammt deshalb aus `05-RESEARCH.md` und aus `docs/privacy.md`, nicht aus einer Datei, die es noch nicht gibt. **Fuer 05-10 heisst das: `docs/faq.md` traegt zwei Links auf `docs/uninstall.md`, die vor dem Release erreichbar sein muessen.**
- **Das Tabellen-Gate ist strenger als der Plan verlangt.** Der Plan nennt "keine Zeile mit einem Tabellentrenner"; das Gate verbietet jedes Pipe-Zeichen. Eine Trennzeile ohne Zeilen daneben gibt es nicht, und ein Pipe in einem Beschreibungssatz ist immer der Anfang einer Tabelle. Die Gegenprobe schreibt eine vollstaendige Tabelle und belegt beides.
- **Der Absatz zum Vokabular-Gate sitzt im Beschreibungs-Gate, prueft aber den ganzen Manifest-Text.** Der Plan verlangt das Wort-Verbot als Teil von Gate eins. Umgesetzt ist es dort, aber gegen den gesamten Elementtext des Manifests statt nur gegen die drei Beschreibungen, weil das Verbot fuer das ganze oeffentliche Artefakt gilt. Kommentarknoten sind ausgenommen, sonst wuerde die Erklaerung im Manifest das Gate ausloesen.

## Threat Flags

Die vier Eintraege des Threat-Registers dieses Plans, mit ihrem Zustand nach der Ausfuehrung. Keine neue Angriffsflaeche: dieser Plan hat keine Route, kein Schema und keinen Datenpfad angefasst, nur Text und Tests.

| Threat ID | Kategorie | Disposition | Zustand nach diesem Plan |
|-----------|-----------|-------------|--------------------------|
| T-05-41 | Spoofing (eine Zusage, die technisch nicht durchgesetzt ist) | mitigate | **Gehalten.** Die FAQ nennt drei Fakten, und jeder hat eine Quelle: der Schalter pro Konto ist live belegt (04-04), seine Durchsetzung an den drei Entstehungspunkten einer Verbindung ist Plan 05-02, und das Trennen mit Rueckgabe des App-Passworts steht in `docs/privacy.md` in der von 05-06 korrigierten Fassung. Kein Satz behauptet eine Loeschung, die nur der occ-Weg leistet; der Remove-Knopf ist woertlich als "deaktiviert nur" beschrieben. |
| T-05-42 | Tampering (Text verliert in der Instanz-Ansicht seinen Inhalt) | mitigate | **Gehalten und maschinell gesichert.** Alle drei Beschreibungen sind auf dem kleineren gemeinsamen Nenner geschrieben, Absaetze durch Leerzeilen. `description_problems()` prueft es, fuenf Gegenproben belegen, dass es ausloest. |
| T-05-43 | Denial of Service (leeres `<default>` bricht Deploy-Umgebung oder Store-Upload) | mitigate | **Gehalten und eingefroren.** `variable_problems()` verbietet das leere Element und nennt im Docstring den Grund mit Quelle (AppAPI 34.0.3 filtert nur gegen den leeren String, `ExAppEnvVarsHelper::toString()` existiert dort nicht, der Store antwortet mit 500, Fix b0ac128). Zwei Tests: die Gegenprobe und die Gegen-Gegenprobe, dass ein befuellter Default erlaubt bleibt. |
| T-05-44 | Information Disclosure (interner Hostname, Testadresse oder Credential im oeffentlichen Text) | mitigate | **Gehalten.** Die neuen Texte nennen genau zwei Adressen, und beide zeigen auf das oeffentliche Repository, dessen URL das Manifest schon fuehrte: `docs/faq.md` und `docs/privacy.md` auf `github.com/street1983nk/nextcloud-mcp-connector`. Kein interner Host, kein Port, kein Beispiel-Credential, keine Testinstanz. |
| T-05-SC | Tampering (Paketinstallationen) | accept | **Nichts installiert.** `uv.lock` und `pyproject.toml` unberuehrt. |

## Fuer 05-10

Was beim Release mitwandert, und was dabei gruen bleiben muss.

**Textstellen, die die Version tragen oder mit ihr wandern:**

1. **Die drei `<description>`-Bloecke in `appinfo/info.xml`.** Sie sind der Text, der beim Release-Upload in den Store geht. Sie enthalten keine Version und keine Zahl, die 05-10 anfassen muesste, aber sie sind der Grund, warum der Upload ueberhaupt einen neuen Store-Text zeigt. Wer sie beim Release anfasst, laesst die beiden Gates zuerst laufen.
2. **`<version>` und `<image-tag>` in `appinfo/info.xml`.** Von diesem Plan bewusst nicht angefasst, beide stehen auf `0.1.0`. `manifest_problems()` verlangt, dass `version` die Paketversion ist und `image-tag` ihr folgt: eine Anhebung ist also immer eine Anhebung an drei Stellen (`pyproject.toml` beziehungsweise `__version__`, `version`, `image-tag`), sonst faellt das Gate.
3. **Der `## Status`-Abschnitt der drei READMEs.** Er nennt jetzt "Version 0.1.0" woertlich, in drei Sprachen an derselben Position. Bei einer neuen Version sind das drei Stellen, und die englische ist die massgebliche (beide Uebersetzungen sagen das in ihrer Kopfzeile).
4. **`CHANGELOG.md`.** In diesem Plan bewusst nicht angefasst, damit der Eintrag die Version traegt, unter der diese Texte ausgeliefert werden. Fuer `[Unreleased]` beziehungsweise die neue Version gehoeren hinein: die FAQ (`docs/faq.md`) als neues Dokument, die dreisprachige Store-Beschreibung mit der Antwort auf die Abschalt-Frage, und die korrigierte Werkzeugzahl. Das Vokabular-Verbot gilt fuer `CHANGELOG.md` genauso wie fuer das Manifest.
5. **`docs/faq.md` verweist zweimal auf `docs/uninstall.md`.** Diese Datei entsteht in Plan 05-08. Vor dem Release muss der Link ein Ziel haben, sonst zeigt das oeffentlichste Nutzerdokument auf ein 404.

**Gates, die beim Release gruen bleiben muessen:**

| Gate | Was es haelt |
|------|--------------|
| `test_the_manifest_text_passes_its_own_gate` | Kein Backtick, keine Tabelle, kein Bild, keine horizontale Linie, kein HTML, mindestens zwei Absaetze je Sprache, `summary` unter 128 Zeichen, kein verbotenes Wort |
| `test_every_description_carries_the_answer_of_the_faq` | Jede Sprachfassung traegt die drei Fakten, an je einem Marker gemessen |
| `test_no_declared_variable_carries_an_empty_default` | Keine Variable bekommt ein leeres `<default>`, auch nicht "zur Dokumentation" |
| `test_the_manifest_passes_its_own_gate` | Das Routen-Gate: dreizehn Routen, Zugriffsstufen, Endanker, Header-Ausschluss, und `version` gleich Paketversion gleich `image-tag` |
| `tests/contract/test_tool_surface.py` | Die Werkzeugtabelle im README gegen die laufende Registry. Sie ist der Grund, warum "16" keine handgepflegte Zahl ist |

## Files Changed

**Neu:**

- `docs/faq.md` (85 Zeilen): die kanonische FAQ, Englisch, zwei Ebenen, drei Fragen.

**Geaendert:**

- `README.md`: Werkzeugzahl, neuer `## Status`-Abschnitt mit vier belegten Fakten, neuer `## FAQ`-Abschnitt.
- `README.de.md`: dasselbe, mit echten Umlauten.
- `README.fr.md`: dasselbe, mit Accents und Cedille.
- `appinfo/info.xml`: drei `<description>`-Bloecke umgeschrieben, plus ein Kommentar, der die zwei Renderer und die Absatzregel festhaelt. `version`, `image-tag`, `dependencies`, Routen und Variablen unberuehrt.
- `tests/unit/test_exapp_env_setup.py`: `+276` Zeilen, zwei Gate-Funktionen, zehn Tests (drei Zusicherungen, sechs Gegenproben, eine Gegen-Gegenprobe).

## Known Stubs

Keine. Dieser Plan hat keinen Codepfad angelegt und keine Datenquelle offen gelassen; die einzige nicht erfuellbare Referenz ist der Link auf `docs/uninstall.md`, und der ist oben unter "Fuer 05-10" als Punkt 5 vermerkt, weil Plan 05-08 die Datei anlegt.

## Requirements

- **EXAPP-04** bleibt **Pending**. Der Anforderungstext ist "App ist im Nextcloud App Store eingereicht (Zertifikat via CSR-PR, Signatur, `info.xml`-Validierung, Datenweitergabe-Disclosure)". Dieser Plan liefert die Datenweitergabe-Disclosure im Beschreibungstext und die maschinelle `info.xml`-Textvalidierung; Zertifikat, Signatur und der Upload selbst sind Plan 05-10.
- **EXAPP-05** war seit Plan 05-07 **Complete** und bleibt es. Die FAQ ergaenzt die Client-Doku, ersetzt sie nicht.

## Self-Check: PASSED

Geprueft nach dem Schreiben dieses Dokuments:

- `docs/faq.md` vorhanden.
- `README.md`, `README.de.md`, `README.fr.md`, `appinfo/info.xml`, `tests/unit/test_exapp_env_setup.py` vorhanden und geaendert.
- Commits `698db7a`, `1e9bcef`, `d323315` im Log gefunden.
