---
phase: 14-doku-reste-und-gate-entscheid
plan: 01
subsystem: docs
tags: [readme, changelog, info.xml, i18n, store-text]

# Dependency graph
requires:
  - phase: 13-cimd-nachmessung-und-release-0-1-9
    provides: "13-REVIEW.md mit den Befunden IN-03, IN-05 und IN-06; Commit 55a5822 (gekürzter Enterprise-Abschnitt in allen drei READMEs und in info.xml)"
provides:
  - "README.fr.md mit französischer Hauptüberschrift und ohne das Scheinwort confidemment"
  - "README.de.md mit MCP Server in der Schreibweise der deutschen Store-Summary"
  - "CHANGELOG.md ohne Linkdefinition ohne Abschnitt"
  - "appinfo/info.xml mit einem Spendenkommentar, der den heutigen Zustand der beiden Adressen beschreibt"
  - "Grep-Beleg, dass DOC-01a keine weitere offene Stelle hat"
affects: [15-release-0-1-10, store-einreichung]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "CRLF-Dateien (README.de.md, README.fr.md, appinfo/info.xml) byte-exakt per Python rb/wb patchen, damit kein Massen-Diff aus Zeilenenden entsteht"
    - "Linkdefinition und Abschnitt im Changelog als Paar: eine Definition entsteht erst wieder mit dem Abschnitt, der sie referenziert"

key-files:
  created:
    - .planning/phases/14-doku-reste-und-gate-entscheid/14-01-SUMMARY.md
  modified:
    - README.fr.md
    - README.de.md
    - CHANGELOG.md
    - appinfo/info.xml

key-decisions:
  - "DOC-01b per Entfernung gelöst statt per neuem Unreleased-Abschnitt: die Datei führt keinen solchen Abschnitt, und ein leerer wäre Prosa, die Phase 15 wieder aufräumen müsste"
  - "Regel für Phase 15: eine [Unreleased]-Linkdefinition entsteht erst wieder zusammen mit einem Abschnitt, der sie referenziert; die nutzersichtbaren Änderungen dieser Phase gehören in den Block [0.1.10]"
  - "Der Ampersand-Kommentar in info.xml beschreibt jetzt den Zustand (keine der beiden Adressen trägt einen Ampersand) plus die Regel für eine künftige Adresse, statt eine Behauptung über eine Adresse aufzustellen, die es nicht gibt"
  - "confidemment wird an beiden Fundstellen identisch durch 'fausse mais assurée' ersetzt, damit die Datei einen Begriff und nicht zwei trägt"

patterns-established:
  - "Übersetzungskorrektur als Wortersetzung: git diff --numstat muss für jede Datei gleich viele hinzugefügte wie entfernte Zeilen nennen, sonst wurde ein Absatz umformuliert"

requirements-completed: [DOC-01]

# Metrics
duration: 3min
completed: 2026-08-27
---

# Phase 14 Plan 01: Doku-Reste aus 13-REVIEW.md Summary

**Vier Wortstellen in den Store-Dateien korrigiert: zwei französische Reste, eine deutsche Kleinschreibung, eine hängende Changelog-Linkdefinition und ein Kommentar, der einen Ampersand behauptete, den keine der beiden Spendenadressen enthält.**

## Performance

- **Duration:** 3 min
- **Started:** 2026-08-27T22:27:56Z
- **Completed:** 2026-08-27T22:30:23Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- README.fr.md ist an den drei benannten Stellen echtes Französisch, ohne dass ein Absatz umformuliert wurde (3 hinzugefügte, 3 entfernte Zeilen)
- README.de.md schreibt den Produktbegriff so, wie die deutsche Store-Summary in appinfo/info.xml ihn schreibt
- CHANGELOG.md trägt nur noch Linkdefinitionen, zu denen ein Abschnitt existiert (10 Definitionen, 10 Abschnitte, identische Versionsmengen)
- Der Spendenkommentar in appinfo/info.xml beschreibt den heutigen Zustand, ohne eine URL oder die durch info.xsd bindende Elementfolge anzufassen
- Grep-Beleg, dass DOC-01a keine Restposten hat, samt Beleg, dass der Enterprise-Wortlaut aus IN-05 schon vor dieser Phase erledigt war

## Die vier ersetzten Wortstellen

| Datei | Zeile | vorher | nachher |
|-------|-------|--------|---------|
| README.fr.md | 5 | `# MCP Connector for Nextcloud` | `# MCP Connector pour Nextcloud` |
| README.fr.md | 274 (Prosa) | `produit une réponse confidemment fausse` | `produit une réponse fausse mais assurée` |
| README.fr.md | 528 (Tabellenzelle) | `Un fuseau deviné est une réponse confidemment fausse` | `Un fuseau deviné est une réponse fausse mais assurée` |
| README.de.md | 7 und 22 | `MCP server` | `MCP Server` |

Der Produktname "MCP Connector" bleibt unverändert, nur die englische Präposition wurde übersetzt, genau wie README.de.md es mit "für" tut. "confidemment" ist kein französisches Wort; die englische maßgebliche Fassung sagt an denselben zwei Stellen "confidently wrong answer" (README.md:260 und README.md:497), die Bedeutung ist also erhalten.

## Grep-Beleg für die Restfreiheit von DOC-01a

Alle Läufe nach den Korrekturen, jeder mit dem erwarteten Ergebnis:

| Prüfung | Ergebnis |
|---------|----------|
| `grep -n "confidemment" README.fr.md appinfo/info.xml` | keine Zeile (rc=1) |
| `grep -c "réponse fausse mais assurée" README.fr.md` | 2 |
| `grep -n "^# MCP Connector pour Nextcloud" README.fr.md` | Zeile 5 |
| `grep -nE "^#.* (for\|with\|and\|the) " README.fr.md` | keine Zeile (rc=1), 24 Überschriften geprüft |
| `grep -n "MCP server" README.de.md` | keine Zeile (rc=1) |
| `grep -c "MCP Server" README.de.md` | 2 |
| `grep -n "—\|–" README.fr.md README.de.md` | keine Zeile (rc=1), keine Em- oder En-Dashes |
| `git diff --numstat README.fr.md README.de.md` | `3 3 README.fr.md`, `2 2 README.de.md`, also nur Ersetzungen |

Die französische Summary in appinfo/info.xml (Zeile 20) und die französische Description (ab Zeile 136) sind nach heutigem Stand sauber: der Grep nach "confidemment" über appinfo/info.xml bleibt leer, deshalb wurde die Datei für DOC-01a nicht angefasst.

## Der Enterprise-Wortlaut aus IN-05 war schon erledigt

Der in IN-05 gemeinte Enterprise-Abschnitt ist durch Commit 55a5822 ("docs: shorten enterprise section, contact admin@infranode.dev (owner wording)") bereits französisch und gekürzt; jener Commit berührte README.md, README.de.md, README.fr.md und appinfo/info.xml. Beleg für diese Phase:

- `sed -n '545,550p' README.fr.md | grep -nE "\b(audit log|group polic|available to your organi|planned as)\b"` gibt keine Zeile aus (rc=1), der Abschnitt trägt also keinen englischen Rest mehr
- `git diff -U0 README.fr.md README.de.md | grep "admin@infranode.dev"` gibt keine Zeile aus (rc=1), die Kontaktzeile steht nicht im Diff dieser Phase

Damit ist T-14-02 aus dem Threat Register belegt: die Nutzlast von Release 0.1.10 wurde nicht angefasst.

## DOC-01b: gewählter Weg und Regel für Phase 15

DOC-01b ließ zwei Wege zu, entfernen oder wieder referenzieren. **Gewählt: entfernen.** Die Datei führt heute keinen `## [Unreleased]`-Abschnitt, sie beginnt nach dem Kopf sofort mit `## [0.1.9]`. Ein neu angelegter leerer Abschnitt wäre Prosa ohne Inhalt, die Phase 15 beim Schreiben des 0.1.10-Blocks wieder aufräumen müsste.

Entfernt wurde genau eine Zeile:

```
[Unreleased]: https://github.com/street1983nk/nextcloud-mcp-connector/compare/v0.1.9...HEAD
```

Die Definition `[0.1.9]: .../compare/v0.1.8...v0.1.9` und alle neun älteren stehen unverändert (`git diff --numstat` nennt `0 1 CHANGELOG.md`, also keine hinzugefügte Zeile).

**Regel für Phase 15:** eine `[Unreleased]`-Definition entsteht erst wieder zusammen mit einem Abschnitt, der sie referenziert. Die nutzersichtbaren Änderungen dieser Phase gehören in den Block `## [0.1.10]`, den Phase 15 schreibt, samt der zugehörigen Definition `[0.1.10]: .../compare/v0.1.9...v0.1.10`.

Paarungsbeleg (T-14-03): die Menge der Versionen aus `^\[([0-9.]+)\]:` und die Menge aus `^## \[([0-9.]+)\]` sind nach der Änderung identisch, 10 gegen 10, `diff` der beiden sortierten Listen ist leer.

## Die neue Formulierung des Ampersand-Kommentars

Vorher (appinfo/info.xml, Zeilen 222 bis 224, IN-03):

```
	  -
	  - The ampersand of the PayPal address is written as an entity because this is XML: a
	  - bare one is a parse error, and the store never sees the file.
```

Nachher:

```
	  -
	  - Neither of the two addresses carries an ampersand today. Should a future one carry
	  - it, it has to be written as the entity &amp;, because this is XML: a bare ampersand
	  - here is a parse error, and the store would then never see the file.
```

Die vorangehenden Sätze über Reihenfolge, secure-url und Provision stehen Wort für Wort unverändert. Die Einrückung mit Tab plus `  - ` je Zeile ist beibehalten, und der Kommentar enthält keine Sequenz aus zwei Bindestrichen (`grep -n -- "--" appinfo/info.xml` ohne die Begrenzer `<!--` und `-->` bleibt leer), sonst wäre die Datei nach XML nicht wohlgeformt.

## Task Commits

1. **Task 1: Die drei Übersetzungsreste aus IN-05, geprüft gegen den Stand nach 55a5822** - `75f1da2` (docs)
2. **Task 2: Hängende Linkdefinition und veralteter Ampersand-Kommentar** - `ef1cacf` (docs)

## Files Created/Modified

- `README.fr.md` - französische Hauptüberschrift, zwei Fundstellen des Scheinworts ersetzt
- `README.de.md` - "MCP Server" groß an beiden Fundstellen, wie die deutsche Store-Summary
- `CHANGELOG.md` - `[Unreleased]`-Linkdefinition entfernt, alle Versionsdefinitionen unverändert
- `appinfo/info.xml` - Spendenkommentar beschreibt den heutigen Zustand der beiden Adressen

## Decisions Made

- DOC-01b per Entfernung statt per neuem Abschnitt (Begründung oben), plus die verbindliche Regel für Phase 15
- Beide Fundstellen von "confidemment" bekommen dieselbe Ersetzung, damit die Datei einen Begriff trägt und nicht zwei
- appinfo/info.xml wird für DOC-01a nicht angefasst; die Sauberkeit der französischen Store-Texte ist mit dem Grep-Ergebnis belegt statt mit einer Änderung

## Deviations from Plan

None - plan executed exactly as written.

Keine Paketinstallation, kein Versions-Bump, kein Tag: `<version>` (Zeile 183) und `<image-tag>` (Zeile 258) in appinfo/info.xml sowie `version` in pyproject.toml stehen weiter auf 0.1.9, und `git diff appinfo/info.xml` enthält keine Zeile mit 0.1.9. `git tag --list v0.1.10` ist leer. T-14-SC ist damit erfüllt: alle Prüfungen liefen mit `uv run --no-sync`.

## Verification

| Kriterium | Ergebnis |
|-----------|----------|
| `grep -n "Unreleased" CHANGELOG.md` | keine Zeile (rc=1) |
| `grep -c "^\[0\.1\.9\]: .../compare/v0.1.8...v0.1.9$" CHANGELOG.md` | 1 |
| Linkdefinitionen mit Abschnitt | 10 zu 10, `diff` der sortierten Listen leer |
| `grep -n "ampersand" appinfo/info.xml` | genau eine Zeilengruppe (223 bis 224), keine Behauptung über eine der Adressen |
| `grep -n -- "--" appinfo/info.xml` außer den Begrenzern | keine Zeile (rc=1) |
| `grep -c "paypalme/KhaledCherifDev"` / `grep -c "buy.stripe.com"` | 1 / 1 |
| `xml.etree.ElementTree.parse("appinfo/info.xml")` | parst ohne Fehler |
| `uv run --no-sync pytest tests/unit/test_exapp_env_setup.py -q` | 152 passed, Exit 0 |
| Versionsstellen | unverändert 0.1.9, kein Tag v0.1.10 |
| `git diff --diff-filter=D` je Commit | keine Löschung einer verfolgten Datei |

## Issues Encountered

Beim Staging von CHANGELOG.md warnt git "LF will be replaced by CRLF the next time Git touches it". Das ist die vorhandene Zeilenenden-Konfiguration des Repos und keine Folge dieser Änderung: CHANGELOG.md liegt im Working Copy mit LF (490 LF, 0 CRLF, vor und nach der Änderung), und der Commit nennt 0 hinzugefügte und 1 entfernte Zeile, also entstand kein Massen-Diff. Die drei CRLF-Dateien wurden byte-exakt per Python rb/wb gepatcht, deshalb tauchen dort ebenfalls nur die tatsächlich geänderten Zeilen im Diff auf.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Die vier Store-Dateien sind bereit für das Asset von Release 0.1.10: DOC-01a bis DOC-01c sind geschlossen
- Offen in dieser Phase: der Gate-Entscheid (DOC-02, SEC-03) in Plan 14-02
- Für Phase 15 (EXAPP-10) gilt die oben festgehaltene Changelog-Regel; der Versions-Bump auf 0.1.10 an allen sechs Stellen und der Tag v0.1.10 nach Owner-Freigabe stehen dort weiterhin aus

## Self-Check: PASSED

- Alle vier geänderten Dateien existieren auf der Platte
- Beide Task-Commits liegen im Log: `75f1da2`, `ef1cacf`
- Kein ASCII-Ersatz für Umlaute in dieser Datei; der einzige Treffer für Em- und En-Dashes ist das zitierte Grep-Muster in der Prüftabelle, also das Suchmuster selbst und keine Prosa

---
*Phase: 14-doku-reste-und-gate-entscheid*
*Completed: 2026-08-27*
