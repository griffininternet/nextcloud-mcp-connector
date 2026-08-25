---
phase: 13-cimd-nachmessung-und-release-0-1-9
plan: 02
subsystem: docs
tags: [fake-door, enterprise, store-description, readme, i18n, changelog, validation]

# Dependency graph
requires:
  - phase: 13
    plan: 01
    provides: "die Version 0.1.9 an sechs Stellen und den Changelog-Block ab Zeile 12, dessen Rubrik ### Added absichtlich frei blieb; die drei READMEs und die drei description-Bloecke waren unberuehrt"
  - phase: ideation-isv-monetarisierung-2026-08-25
    provides: "den Schnitt Connector Enterprise (Audit, Governance, Identity) aus concept-brief-1 und die Fake-Door-Methode samt Go-Kriterium aus validation-plan.md"
provides:
  - "vier Fake-Door-Fassungen desselben Textes: Abschnitt ## Enterprise in README.md, README.de.md und README.fr.md plus eine Kurzfassung in den drei description-Bloecken von appinfo/info.xml"
  - "die drei Bausteine als Vorhaben benannt und nicht als Feature: Audit-Log, Gruppen-Policies und SSO vor der OAuth-Anmeldung, je Fassung mit einem eigenen Satz, dass heute keiner davon existiert"
  - "k.cherif@outlook.de als Signal-Adresse in allen vier Fassungen; kein Preis, keine Waehrung, kein Datum, keine Versionszusage in keiner"
  - "docs/contrib/enterprise-signals-issue.md: der Issue-Entwurf als Datei, nicht veroeffentlicht, mit dem Go-Kriterium im Metadatenkopf"
  - "die Rubrik ### Added im 0.1.9-Block von CHANGELOG.md, eine Zeile, ueber ### Changed"
affects: [13-05-release-runbook, 13-06]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Fake-Door-Text in vier Fassungen: dieselbe Aussage in drei Sprachen plus eine Kurzfassung im Manifest, jede mit einem eigenen Ehrlichkeitssatz statt einer gemeinsamen Fussnote"
    - "Entwurf im Repo statt veroeffentlichter Fremdplattform-Text: Metadatenkopf als HTML-Kommentar, darin die Nichtveroeffentlichung als Owner-Entscheidung und das Go-Kriterium, damit der Zweck des Entwurfs spaeter messbar bleibt"

key-files:
  created:
    - docs/contrib/enterprise-signals-issue.md
    - .planning/phases/13-cimd-nachmessung-und-release-0-1-9/13-02-SUMMARY.md
  modified:
    - README.md
    - README.de.md
    - README.fr.md
    - appinfo/info.xml
    - CHANGELOG.md

key-decisions:
  - "Die Ueberschrift heisst in allen drei READMEs `## Enterprise`, unuebersetzt. Das Wort ist in allen drei Sprachen dasselbe, und eine uebersetzte Ueberschrift haette die strukturelle Deckungsgleichheit der drei Dateien an genau der Stelle gebrochen, an der ein Leser zwischen den Fassungen springt."
  - "Der Ehrlichkeitssatz steht in jeder Fassung als eigener, fett gesetzter Satz und nicht als Nebensatz: 'Keines der drei existiert heute in dieser App, in keiner Version und hinter keiner Einstellung.' Die Nennung von Version UND Einstellung ist Absicht, weil ein Leser sonst hinter einem Schalter sucht."
  - "Die Kurzfassung im Manifest sagt dasselbe in zwei Absaetzen statt in drei plus Liste. Grund ist nicht Platz, sondern das Rendering: die Instanz-Ansicht sanitisiert auf Ueberschriften, Fett, Links und Listen, und ein vierter Abschnitt in einer Beschreibung, die ohnehin fuenf hat, verschiebt den Link-Abschnitt aus dem Sichtfeld."
  - "Das Wort kostenlos beziehungsweise free kommt in keiner Fassung vor. Der Plan verbietet es als Preis-Abgrenzung, und die weichere Variante ('der freie Kern') waere dieselbe Abgrenzung mit anderer Wortwahl gewesen."
  - "Das Go-Kriterium steht im Metadatenkopf des Entwurfs und nicht im Body. Im Body waere es eine Ansage an die Antwortenden ('ab fuenf baue ich'), im Kopf ist es die Messvorschrift fuer den Owner, und der Kopf ist der Teil, den GitHub nie sieht."
  - "Der Body des Entwurfs endet mit einem Abschnitt 'What this issue is not'. Ein Fake-Door-Issue ohne diesen Abschnitt liest sich wie eine Ankuendigung, und die 200-Cloner-Basis besteht ueberwiegend aus Selfhostern, fuer die die richtige Auskunft lautet, dass die App, die sie haben, die ganze App ist."
  - "Die Changelog-Zeile nennt ausdruecklich, warum der Text mit 0.1.9 mitfaehrt (der Store liest das Manifest beim Upload) und nennt 0.1.5 und 0.1.6 als die zwei Versionen, die das gekostet hat. Ohne diesen Halbsatz waere die Zeile eine Marketing-Zeile im Changelog."

patterns-established:
  - "Vier Fassungen in zwei Commits, getrennt nach Rendering-Regime: die drei Markdown-Fassungen in einem Commit, die drei Manifest-Fassungen in einem zweiten, weil nur der zweite unter description_problems steht"
  - "Byte-exakte Einfuegung ueber einen eindeutigen Folgeanker: der Text wird VOR die naechste Ueberschrift gesetzt, deren Trefferzahl vorher gegen 1 geprueft wird, plus eine Vorab-Pruefung des einzufuegenden Blocks gegen Em-Dash, En-Dash und das verbotene Wort"

requirements-completed: []  # EXAPP-09 bleibt Pending: geteilt mit 13-01, 13-04, 13-05 und 13-06, und sein Wortlaut verlangt das Release im Store

# Metrics
duration: 8min
completed: 2026-08-25
---

# Phase 13 Plan 02: Der Enterprise-Fake-Door Summary

**Vier Fassungen desselben Textes nennen Audit-Log, Gruppen-Policies und SSO als geplantes kommerzielles Add-on und sagen in jeder Sprache in einem eigenen Satz, dass heute keiner der drei Bausteine existiert; der Issue-Entwurf liegt als Datei im Repo und ist nicht veroeffentlicht.**

## Performance

- **Duration:** 8 min
- **Started:** 2026-08-25T17:12:00Z
- **Completed:** 2026-08-25T17:20:00Z
- **Tasks:** 3
- **Files created:** 1
- **Files modified:** 5

## Accomplishments

- Der Fake-Door steht an der einzigen Stelle, an der er wirken kann. Der Store liest das Manifest ausschliesslich beim Release-Upload, und weil der Text jetzt im Kandidaten 0.1.9 liegt, wird er mit diesem Release sichtbar statt unsichtbar zu bleiben, wie es die Beschreibungsaenderungen von 0.1.5 und 0.1.6 waren.
- Die Aussage ist viermal dieselbe. Drei READMEs tragen die Langfassung (Absatz, drei Bausteine als Liste, Ehrlichkeitssatz, Kontaktabsatz), die drei Manifest-Beschreibungen die Kurzfassung in zwei Absaetzen. Kein Baustein wird in einer Fassung genannt und in einer anderen weggelassen.
- Kein Versprechen wurde gemacht. `grep -cE '(EUR|€|\$|USD|/month|pro Monat|par mois)'` gibt in allen drei READMEs 0, das Manifest nennt weder Preis noch Datum, und keine Fassung enthaelt eine Zukunftsform, die mehr behauptet als ein Vorhaben.
- D-08 ist gewahrt: es wurde kein Audit-Log, keine Policy und kein SSO gebaut. Der Diff dieses Plans ist 167 hinzugefuegte Zeilen in sechs Dateien, davon keine unter `src/`.
- Nichts wurde veroeffentlicht. Der Issue-Entwurf ist eine Datei, sein Kopf nennt die Veroeffentlichung ausdruecklich als Owner-Entscheidung, und in dieser Phase lief kein `gh issue create` und kein `gh api`.

## Task Commits

Each task was committed atomically:

1. **Task 1: Abschnitt Enterprise in den drei READMEs** - `53b922a` (docs), 85 Zeilen hinzugefuegt, 0 entfernt
2. **Task 2: Enterprise-Kurzfassung in den drei description-Bloecken** - `bb07df0` (docs), 18 Zeilen hinzugefuegt, 0 entfernt
3. **Task 3: Issue-Entwurf als Datei und die Changelog-Zeile** - `06d522b` (docs), 64 Zeilen hinzugefuegt, 0 entfernt

## Files Created/Modified

- `README.md` - neuer Abschnitt `## Enterprise` auf Zeile 512, zwischen `## Known limitations` (481) und `## Development` (539). Langfassung mit `planned`, den drei Bausteinen als Liste, dem eigenen Ehrlichkeitssatz und `k.cherif@outlook.de`. Die Statuszeile 27 und die Zahl 21 in den Werkzeug-Formulierungen sind unberuehrt
- `README.de.md` - `## Enterprise` auf Zeile 527, zwischen `## Bekannte Einschränkungen` (495) und `## Entwicklung` (556). `geplant`, echte Umlaute, keine Em-Dashes
- `README.fr.md` - `## Enterprise` auf Zeile 545, zwischen `## Limitations connues` (511) und `## Développement` (574). `prévus` mit Accent, Leerzeichen vor dem Doppelpunkt wie in den Nachbarabschnitten
- `appinfo/info.xml` - je sechs Zeilen in den drei `<description>`-Bloecken, eingefuegt vor `### Resources` (jetzt Zeile 77 ff.), vor `### Weiterführendes` (124 ff.) und vor `### Pour aller plus loin` (173 ff.). `<summary>`, `<version>`, `<image-tag>` und `<environment-variables>` sind unberuehrt: der Diff ist 18 Hinzufuegungen und keine Entfernung
- `docs/contrib/enterprise-signals-issue.md` **NEU** - 55 Zeilen. Metadatenkopf als HTML-Kommentar nach dem Muster von `227-pr-body.md`, darin Zielrepo, Titel, das Go-Kriterium und die Zeile `Not published. Publishing this issue is an owner decision (D-07).` Darunter der Body auf Englisch: warum der Issue existiert, die drei Bausteine als Ausgangspunkt, vier Fragen, und ein Abschnitt, der sagt, was der Issue nicht ist
- `CHANGELOG.md` - neue Rubrik `### Added` auf Zeile 19, im 0.1.9-Block (12 bis 47) und ueber `### Changed` (28), mit genau einem Eintrag. Keep-a-Changelog-Reihenfolge ist damit hergestellt, ohne den bestehenden Text anzufassen

## Verification Results

| Prueffrage | Ergebnis |
|-----------|----------|
| `grep -c '^## Enterprise' README.md README.de.md README.fr.md` | 1 / 1 / 1 |
| Reihenfolge der Ueberschriften je Datei | 481 Grenzen, 512 Enterprise, 539 Entwicklung (EN); 495 / 527 / 556 (DE); 511 / 545 / 574 (FR) |
| `grep -c 'k.cherif@outlook.de'` in den drei READMEs | 1 / 1 / 1 |
| `planned` in README.md, `geplant` in README.de.md, `prévu` in README.fr.md | je 1 |
| Die drei Bausteine je Fassung | EN `An audit log` / `Group policies` / `**SSO**` je 1; DE `Ein Audit-Log` / `Gruppen-Policies` / `**SSO**` je 1; FR `journal d'audit` / `politiques de groupe` / `Le SSO` je 1 |
| `grep -cE '(EUR\|€\|\$\|USD\|/month\|pro Monat\|par mois)'` in den drei READMEs | 0 / 0 / 0 |
| Em-Dash und En-Dash in den drei READMEs | 0 / 0 |
| `grep -c 'Version 0\.1\.9\.'` in den drei READMEs | 1 / 1 / 1, unveraendert |
| `git diff --numstat` der drei READMEs | 27/0, 29/0, 29/0, keine Entfernung |
| `grep -c 'k.cherif@outlook.de' appinfo/info.xml` | 4 (drei Beschreibungen plus `<author mail=...>`) |
| `grep -o '<version>[^<]*'` / `<image-tag>` | `<version>0.1.9` / `<image-tag>0.1.9`, unveraendert |
| `git diff --numstat appinfo/info.xml` | `18 0`, und die drei Hunks liegen auf 77, 124 und 173, also innerhalb der CDATA-Bloecke |
| Backtick, senkrechter Strich, `<`, `>`, Bindestrich-Linie im neuen Manifest-Text | je 0, vorab im Einfuege-Skript geprueft und abbrechend |
| `grep -ic 'archiv' appinfo/info.xml` | 0 |
| `test -f docs/contrib/enterprise-signals-issue.md` | wahr, 55 Zeilen |
| Titelzeile im Entwurf | 1 Treffer, wortgleich mit der Vorgabe |
| `Not published` und `owner decision` | 1 Treffer, dieselbe Zeile 11 |
| Go-Kriterium: `five qualified` / `more than 100 users` / `within six weeks` | 1 / 1 / 1 |
| `git status --short docs/contrib/227-pr-body.md` | leer, Datei unberuehrt |
| `grep -n '^### Added'` in CHANGELOG.md | erster Treffer 19, im 0.1.9-Block, oberhalb von `## [0.1.8]` (48) |
| Waehrung, Em-Dash, `archiv` in CHANGELOG.md | 0 / 0 / 0 |
| `git log --oneline -1 --grep='gh issue create'` | leer |
| `uv run --no-sync pytest tests/unit/test_exapp_env_setup.py -q` | Exit 0, 152 Tests (nach Task 2 und nach Task 3) |
| `uv run --no-sync pytest tests/unit/test_exapp_env_setup.py tests/contract/test_tool_surface.py -q` | Exit 0, 178 Tests (nach Task 1 und am Planende) |
| `git tag --list v0.1.9` | leer |
| `git diff --stat e311d5e..HEAD` | genau die sechs Dateien dieses Plans, 167 Hinzufuegungen, 0 Entfernungen |
| Loeschungen in den drei Commits | keine, `git diff --diff-filter=D` je leer |

## Decisions Made

- **Die Ueberschrift bleibt unuebersetzt.** `## Enterprise` in allen drei Fassungen: das Wort ist in allen drei Sprachen dasselbe, der Plan verlangt es ausdruecklich, und die drei READMEs bleiben damit an dieser Stelle strukturell deckungsgleich.
- **Der Ehrlichkeitssatz ist ein eigener, fett gesetzter Satz.** Er nennt Version und Einstellung getrennt ("in keiner Version und hinter keiner Einstellung"), weil ein Leser, der nur "existiert noch nicht" liest, als naechstes nach einem Schalter sucht. Das ist das Ehrlichkeits-Pattern des Grenzen-Abschnitts, uebertragen auf ein Vorhaben.
- **Kein `free` und kein `kostenlos`.** Auch nicht in der weichen Form "der freie Kern". Der Plan verbietet die Abgrenzung zu einem Preis, und eine Umschreibung derselben Abgrenzung waere dieselbe Aussage gewesen.
- **Das Go-Kriterium steht im Kopf, nicht im Body.** Im Body waere es eine Ansage an die Antwortenden; im HTML-Kommentar ist es die Messvorschrift, und GitHub rendert den Kommentar nie.
- **Der Body sagt, was der Issue nicht ist.** Ein letzter Abschnitt nennt ausdruecklich, dass nichts implementiert ist, kein Branch existiert und kein Satz eine Version oder einen Tag verspricht. Ohne ihn liest ein Selfhoster das Issue als Ankuendigung eines Umbaus.
- **Die Changelog-Zeile nennt ihren eigenen Grund.** Sie sagt, warum der Text mit diesem Release mitfaehrt (der Store liest das Manifest beim Upload) und nennt 0.1.5 und 0.1.6 als Praezedenz. Ohne diesen Halbsatz waere eine Marketing-Aussage im Changelog gelandet.

## Deviations from Plan

Keine. Der Plan lief woertlich wie geschrieben: drei Tasks, drei Commits, keine Auto-Fix-Regel wurde ausgeloest, kein Blocker, kein Checkpoint.

**Total deviations:** 0
**Impact on plan:** keiner

## Known Stubs

Keine. Dieser Plan hat keine Zeile Code angefasst; alle sechs Dateien sind Text, und keine Fassung nennt ein Feature, das hinter einem Platzhalter steckt. Der Enterprise-Text ist ausdruecklich kein Stub, sondern die Beschreibung eines Vorhabens: er behauptet an keiner Stelle, dass etwas gebaut ist, und genau dieser Satz steht in jeder der vier Fassungen.

## Issues Encountered

- Git warnt beim Stagen von `CHANGELOG.md` und `docs/contrib/enterprise-signals-issue.md` mit "LF will be replaced by CRLF the next time Git touches it". Das ist `text=auto` aus `.gitattributes` in Verbindung mit der Windows-Einstellung dieses Arbeitsplatzes und keine Folge dieses Plans: die neue Datei wurde bewusst im LF angelegt, weil `docs/contrib/227-pr-body.md` im LF liegt. Keine Aktion.

## Requirements

`EXAPP-09` bleibt **Pending** und wurde nicht abgehakt, obwohl die Frontmatter dieses Plans die Anforderung nennt. Ihr Wortlaut verlangt das Release im Store; dieser Plan liefert einen Text, keinen Store-Eintrag. Dieselbe Anforderung beanspruchen 13-01, 13-04, 13-05 und 13-06. Der Haken gehoert in den letzten Plan der Kette, nach dem Store-Nachweis, genau wie 13-01 es entschieden und begruendet hat.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **Fuer Plan 13-05 (Release-Runbook):** die vier Fake-Door-Fassungen sind Teil des Kandidaten 0.1.9. Runbook-Schritt 3 muss die sechs Gates ueber diesen Stand fahren; die zwei Text-Gates (`description_problems` und das Vokabular-Gate) sind bereits gruen, der Vollauf steht noch aus. Die Beschreibungsaenderung ist der Grund, warum ein Release ueberhaupt noetig ist, um sie sichtbar zu machen: ein Abbruch vor Schritt 7 laesst den Text im Katalog unsichtbar.
- **Fuer den Owner, ausserhalb der Phase:** `docs/contrib/enterprise-signals-issue.md` ist absendefertig. Die Veroeffentlichung ist eine Owner-Entscheidung (D-07), und der Metadatenkopf nennt das Go-Kriterium, gegen das die Antworten sechs Wochen spaeter gezaehlt werden.
- **Fuer die naechste Uebersetzungsaenderung:** der Enterprise-Abschnitt existiert jetzt siebenmal (dreimal README, dreimal Manifest, einmal als Entwurf). Wer eine Fassung anfasst, zieht die anderen nach; das ist dieselbe Regel, unter der die Store-Beschreibung schon steht.
- **Kein Blocker.** Kein Tag, kein Push, kein veroeffentlichter Issue.

## Self-Check: PASSED

Alle sechs Dateien existieren auf der Platte, `docs/contrib/enterprise-signals-issue.md` ist neu und traegt 55 Zeilen, und die drei Task-Commits (`53b922a`, `bb07df0`, `06d522b`) sind in `git log` auffindbar. Keiner der drei Commits enthaelt eine Loeschung, `git diff --diff-filter=D` ist je leer.

---
*Phase: 13-cimd-nachmessung-und-release-0-1-9*
*Completed: 2026-08-25*
