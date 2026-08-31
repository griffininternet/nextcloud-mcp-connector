---
phase: 19-audit-log-bedienung-und-textnachzug
plan: 08
subsystem: docs-manifest
tags: [audit-log, enterprise, i18n, manifest, readme, audit-06, t-19-31, marker-test]

# Dependency graph
requires:
  - phase: 19
    plan: 03
    provides: "FORBIDDEN_CLAIMS mit den vier Anspruchsmustern in EN/DE/FR, gegen die die sechs neuen Absätze geschrieben sind"
  - phase: 19
    plan: 07
    provides: "appinfo/info.xml mit dem sechsten abwesenden Pfad und den drei Audit-Umgebungsvariablen; 13 url-Einträge, Version 0.1.11 unberührt"
  - phase: 19
    plan: 02
    provides: "ADMIN_FIELD_AUDIT_LOG_DESCRIPTION, die Formularbeschriftung, hinter die der Enterprise-Absatz inhaltlich nicht zurückfällt und über die er nicht hinausgeht"
  - phase: 18
    plan: 08
    provides: "occ mcp_connector:audit:verify, das Prüfkommando, das der Absatz namentlich nennt"
provides:
  - "Der Enterprise-Absatz an allen sechs Stellen in zwei Absätzen: das Protokoll gehört zu dieser App, geplant sind nur noch Gruppen-Policies und SSO"
  - "ENTERPRISE_MARKERS in tests/unit/test_exapp_env_setup.py: je Sprache ein Markertripel, die zugehörige README und die Wortformen für geplant"
  - "enterprise_section(text, name) und enterprise_places(manifest_root): der Abschnitt statt der ganzen Seite, sechs Stellen in einer Liste"
  - "test_the_enterprise_paragraph_carries_its_markers_at_all_six_places"
  - "test_no_place_calls_the_audit_log_planned"
affects: [19-09]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Eine öffentliche Textaussage, die eine Phase falsch machen kann, wird als Test geschrieben und nicht als Merksatz: ein verbotenes Wortpaar in einer Zeile"
    - "Ein Markertest liest den Abschnitt unter seiner Überschrift und nicht die ganze Seite, sonst kann ein Vorkommen anderswo für den Absatz einstehen"
    - "Marker werden gegen den auf einfache Leerzeichen geglätteten Abschnitt geprüft, weil eine README ihre Zeilen umbricht"
    - "Die Trennung zweier Aussagen wird zeilenweise geprüft, weil zwei Absätze genau dann wieder zu einem Anspruch werden, wenn jemand sie zu einem Satz zusammenzieht"

key-files:
  created: []
  modified:
    - appinfo/info.xml
    - README.md
    - README.de.md
    - README.fr.md
    - tests/unit/test_exapp_env_setup.py

key-decisions:
  - "Der Absatz wird an allen sechs Stellen zu ZWEI Absätzen: das Protokoll in den einen, das Geplante in den anderen. Das ist nicht Typografie, sondern die Bedingung, unter der der zweite Test zeilenweise messen kann"
  - "Die Markertripel bleiben die aus dem Plan vorgeschlagenen, mit einer Anpassung an die tatsächliche Schreibung: EN und FR tragen ihren Audit-Marker klein, DE gross"
  - "Die englische Fassung sagt 'Two things are planned as a commercial add-on: group policies, and sign in ...' statt 'Group policies and ... are planned', damit der Marker group policies in der Schreibung des Satzes klein steht und nicht am Satzanfang gross"
  - "Kein Wort über Exklusivität: der Absatz verspricht Begleitung bei Einführung und Betrieb, nicht Zugang zu einem Merkmal, das die AGPL ohnehin offen hält (T-19-33)"
  - "Die drei Beschreibungen nennen die occ-Kommandos ohne Backtick und ohne Tabelle, weil die Instanzansicht beides verschwinden lässt; die drei READMEs setzen dieselben Kommandos in Backticks, weil Markdown das trägt"
  - "Der Manifestweg des Tests geht über die description mit ihrem lang-Attribut und nicht über element_text_without_comments: hier ist die Sprache die Unterscheidung"

patterns-established:
  - "Sechs Fundstellen einer Aussage werden nicht durch Sorgfalt zusammengehalten, sondern durch eine Liste, über die ein Test läuft und die jede Lücke auf einmal nennt"

requirements-completed: []
# AUDIT-06 bleibt Pending: der Enterprise-Absatz ist die dritte von vier Hälften. Gate (19-03),
# docs/privacy.md und docs/uninstall.md (19-05) und dieser Absatz stehen; der [Unreleased]-Block,
# der sie zusammenführt, ist 19-09.
requirements-advanced: [AUDIT-06]

# Metrics
duration: 17min
completed: 2026-08-31
---

# Phase 19 Plan 08: Der Enterprise-Absatz sagt die Wahrheit Summary

**An allen sechs Stellen in drei Sprachen steht das Audit-Log jetzt als Teil dieser App und nicht mehr als geplantes Add-on: ein erster Absatz sagt, was eine Zeile enthält, dass das Protokoll ab Werk aus ist, wie es eingeschaltet und mit `occ mcp_connector:audit:read` gelesen wird und dass `occ mcp_connector:audit:verify` die Hash-Kette prüft, ein zweiter Absatz behält das Wort "geplant" für Gruppen-Policies und die Anmeldung über den Identitätsanbieter, und zwei neue Tests halten die sechs Stellen an drei Markertripeln zusammen und verbieten das Wort für "geplant" in jeder Zeile, die das Wort für das Audit-Log trägt.**

## Performance

- **Duration:** 17 min
- **Started:** 2026-08-31T15:58:00Z
- **Completed:** 2026-08-31T16:15:00Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Sechs Absätze, drei Sprachen, ein Inhalt, in einem Commit gezogen: `appinfo/info.xml` (EN, DE, FR) und `README.md`, `README.de.md`, `README.fr.md`. 40 Einfügungen, 10 Löschungen, keine andere Zeile berührt.
- Jede der sechs Stellen sagt in ihrer Sprache dieselben drei Dinge: (1) das Protokoll gehört zu dieser App und nicht zu einem Add-on, es hält Konto, Werkzeug, Zeit, aufrufende App und Ergebnis fest und nie einen Parameterwert oder einen Teil eines Ergebnisses, es ist ab Werk aus, wird in den Admin-Einstellungen eingeschaltet, mit `occ mcp_connector:audit:read` gelesen, und jeder Eintrag ist hash-verkettet, was `occ mcp_connector:audit:verify` prüft; (2) geplant als kommerzielles Add-on sind nur noch Gruppen-Policies und die Anmeldung über den Identitätsanbieter der Organisation; (3) das Angebot zur Begleitung bei Einführung und Betrieb, samt `admin@infranode.dev`.
- Zwei Tests statt eines Merksatzes: `test_the_enterprise_paragraph_carries_its_markers_at_all_six_places` sammelt jede Lücke, bevor es behauptet, und nennt in einer roten Zeile alle fehlenden Marker mit Datei; `test_no_place_calls_the_audit_log_planned` verbietet zeilenweise die Nähe von Audit-Log-Wort und Geplant-Wort.
- Beide Gegenproben von Hand gefahren und zurückgenommen (siehe "Verification"): ein entfernter Marker in `README.fr.md` macht den ersten Test rot mit Datei und Marker, ein wieder zusammengezogener Satz den zweiten mit Datei, Zeilennummer und Zeile.
- Version `0.1.11`, `image-tag`, `CHANGELOG.md`, `pyproject.toml` und `uv.lock` unberührt, kein Tag, kein Store-Archiv, 13 `<url>`-Einträge unverändert.

## Die drei Manifestabsätze, wortgetreu

Für Plan 19-09, damit der `[Unreleased]`-Eintrag daraus geschrieben werden kann, ohne das
Manifest zu lesen. Je Sprache zwei Absätze, getrennt durch eine Leerzeile, ohne Backtick und
ohne Tabelle.

**EN (`appinfo/info.xml`, `description` ohne `lang`):**

> The audit log is part of this app and not of an add-on. With it on, every tool call is written down with the account it ran for, the tool, the time, the calling app and the outcome, and never a parameter value or any part of a result. It is off by default, an administrator switches it on in the admin settings of this app, and the entries are read with the command occ mcp_connector:audit:read. Every entry is hash chained to the one before it, and occ mcp_connector:audit:verify walks the chains and names the first place one of them is broken.
>
> Two things are planned as a commercial add-on for organisations: group policies, and sign in through the identity provider your organisation already runs. Want to run this app in your organisation? Talk to us: admin@infranode.dev

**DE (`description lang="de"`):**

> Das Audit-Log gehört zu dieser App und nicht zu einem Add-on. Eingeschaltet hält es jeden Werkzeugaufruf fest: das Konto, für das er lief, das Werkzeug, die Zeit, die aufrufende App und das Ergebnis, nie einen Parameterwert und nie einen Teil eines Ergebnisses. Es ist ab Werk aus, die Administration schaltet es in den Admin-Einstellungen dieser App ein, und gelesen wird es mit dem Kommando occ mcp_connector:audit:read. Jeder Eintrag ist mit dem vorigen hash-verkettet, und occ mcp_connector:audit:verify prüft die Ketten und nennt die erste Stelle, an der eine gebrochen ist.
>
> Zwei Dinge sind als kommerzielles Add-on für Organisationen geplant: Gruppen-Policies und die Anmeldung über den Identitätsanbieter Ihrer Organisation. Sie möchten die App in Ihrer Organisation einsetzen? Sprechen Sie uns an: admin@infranode.dev

**FR (`description lang="fr"`):**

> Le journal d'audit fait partie de cette application et non d'un module complémentaire. Activé, il consigne chaque appel d'outil : le compte pour lequel il s'est exécuté, l'outil, l'heure, l'application appelante et le résultat, jamais une valeur de paramètre ni une partie d'un résultat. Il est désactivé par défaut, un administrateur l'active dans les paramètres d'administration de cette application, et il se lit avec la commande occ mcp_connector:audit:read. Chaque entrée est chaînée par empreinte à la précédente, et occ mcp_connector:audit:verify parcourt les chaînes et indique le premier endroit où l'une d'elles est rompue.
>
> Deux choses sont prévues comme module commercial pour les organisations : les politiques de groupe et l'authentification via le fournisseur d'identité de votre organisation. Vous souhaitez déployer l'application dans votre organisation ? Contactez-nous : admin@infranode.dev

Die drei READMEs sagen dasselbe, mit den zwei occ-Kommandos in Backticks und mit dem
Angebotssatz, den diese Dateien schon vorher trugen ("Happy to support your organisation with
evaluation and deployment", "Für Evaluierung und Einsatz in Ihrer Organisation stehen wir zur
Verfügung", "Nous nous tenons à la disposition de votre organisation pour l'évaluation et le
déploiement").

## Die endgültigen Markertripel

Unverändert gegenüber dem Vorschlag des Plans, bis auf die Schreibung, die dem Satz folgt:

| Sprache | Marker 1 (Audit-Log-Wort) | Marker 2 | Marker 3 | Wort für "geplant" |
|---------|---------------------------|----------|----------|--------------------|
| EN | `audit log` | `off by default` | `group policies` | `planned` |
| DE | `Audit-Log` | `ab Werk aus` | `Gruppen-Policies` | `geplant` |
| FR | `journal d'audit` | `désactivé par défaut` | `politiques de groupe` | `prévu`, `prevu` |

Marker 1 ist zugleich das Wort, das der zweite Test gegen das Wort für "geplant" hält. Die
Prüfung der Marker ist gross-/kleinschreibungsgenau und läuft über den auf einfache Leerzeichen
geglätteten Abschnitt; die Trennungsprüfung ignoriert Gross- und Kleinschreibung und läuft
zeilenweise über den rohen Abschnitt.

Die französische Zeile trägt zwei Wortformen für "geplant", die akzentuierte und die nackte,
damit die Regel hält, welche von beiden eine spätere Hand schreibt. Die Marker selbst sind
akzentuiert, weil das die Hausregel für den Text ist.

## Task Commits

1. **Task 1: Sechs Absätze in drei Sprachen** - `e981eef` (docs)
2. **Task 2: Ein Test hält die sechs Stellen zusammen** - `13a2291` (test)

## Files Created/Modified

- `appinfo/info.xml` - der Enterprise-Absatz aller drei Beschreibungen ist zwei Absätze; 6 Einfügungen, 3 Löschungen, keine Versionszeile, kein `image-tag`, kein `<url>`
- `README.md`, `README.de.md`, `README.fr.md` - derselbe Inhalt in Markdown, je zwei Absätze unter `## Enterprise`
- `tests/unit/test_exapp_env_setup.py` - neuer Abschnitt am Dateiende mit `ENTERPRISE_MARKERS`, `ENTERPRISE_HEADING`, `enterprise_section`, `enterprise_places` und den zwei Tests; 152 Einfügungen, keine bestehende Zeile geändert

## Decisions Made

- **Zwei Absätze statt einem, an allen sechs Stellen.** Der alte Text war ein Satz, der drei Dinge in eine Aufzählung nahm ("Audit log, group policies and SSO ... are planned"). Genau diese Bauart hat den Satz mit Phase 18 falsch gemacht: ein Glied der Aufzählung stimmte nicht mehr, und der Satz war nur als Ganzes zu retten. Zwei Absätze trennen die zwei Aussagen so, dass die eine altern kann, ohne die andere mitzunehmen, und erst diese Trennung macht die zeilenweise Prüfung des zweiten Tests möglich.
- **Der Absatz nennt die zwei occ-Kommandos beim Namen.** Ein Leser der Store-Beschreibung entscheidet über eine Installation und will wissen, wie er an das Protokoll kommt. Der Preis ist, dass zwei Kommandonamen jetzt auch im Manifesttext stehen; sie stehen dort ohne Backtick, weil die Instanzansicht Backticks nicht abschwächt, sondern verschwinden lässt.
- **Kein exklusives Merkmal.** Der Code liegt unter AGPL-3.0 offen, das Protokoll ist Teil davon, und ein Absatz, der es hinter eine Bezahlschranke stellte, wäre eine Zusage, die die Lizenz nicht hält (T-19-33). Der Absatz verspricht deshalb Leistung: Begleitung bei Einführung und Betrieb. Die grössere Frage, was eine Enterprise-Positionierung unter AGPL überhaupt tragen kann, ist OD-03 und gehört auf die Fragenliste des ISV-Calls, nicht in diesen Text.
- **Der Absatz bleibt hinter der Formularbeschriftung.** `ADMIN_FIELD_AUDIT_LOG_DESCRIPTION` (19-02) nennt zusätzlich die Parameternamen, den Ablehnungsgrund, die Dauer, den Mitbestimmungshinweis, die drei Löschwege und den Grenzsatz. Der Store-Absatz nennt davon die Kurzform und verspricht nichts, was das Formular nicht auch sagt: er steht vor der Installation, das Formular vor dem Einschalten.
- **Der Test liest den Abschnitt, nicht die Seite.** Ein Marker wie "group policies" könnte irgendwo sonst in einer 540-Zeilen-README stehen und für den Absatz einstehen, der ihn verloren hat. `enterprise_section` schneidet an der Überschrift und an der nächsten Überschrift, und behauptet dabei, dass es genau eine Enterprise-Überschrift gibt und dass der Abschnitt nicht leer ist.
- **Marker gegen den geglätteten Abschnitt, Trennung gegen die rohen Zeilen.** Die READMEs brechen ihre Zeilen um; ein Marker, der über einen Umbruch fällt, steht im Text, den ein Leser sieht, also darf ein Umbruch den Test nicht rot machen. Die Trennungsregel dagegen ist eine Regel über Zeilen: sie soll rot werden, sobald jemand die zwei Absätze zu einem Satz zusammenzieht.
- **Die Zahl der Sprachen steht als erste Behauptung im Markertest.** Dieselbe Lehre wie in 19-03: eine Schleife über eine geleerte Liste besteht, ohne etwas anzusehen.

## Deviations from Plan

### Abweichung im Wortlaut eines Akzeptanzkriteriums

**`grep -c "Audit" appinfo/info.xml` ergibt 1 statt der geforderten mindestens 4.**

- **Gefunden bei:** Task 1, bei der Abnahme
- **Befund:** Das Kriterium rechnet "drei Absätze plus der Kommentar zum abwesenden Pfad aus Plan 19-07". Diese Rechnung geht case-sensitiv nicht auf, und sie ging schon vor diesem Plan nicht auf: am Ausgangsstand ergab `grep -c "Audit" appinfo/info.xml` **2** (die Zeilen 79 und 124), nicht 4. Der Kommentar aus 19-07 schreibt "audit log" und "/audit-read" klein, die drei Variablennamen schreiben `NC_MCP_AUDIT_LOG` ganz gross, und das französische Wort ist "journal d'audit" mit kleinem a. Nach diesem Plan trägt nur noch die deutsche Fassung ein grosses "Audit", weil die englische Fassung mit "The audit log ..." beginnt statt mit "Audit log, ...".
- **Warum nicht am Text gedreht wurde:** Ein grosses "Audit" liesse sich im Englischen nur erzwingen, indem der Absatz mit "Audit log" statt mit einem Satz beginnt, und im Französischen gar nicht. Der Sinn des Kriteriums ist, dass alle drei Fassungen das Protokoll benennen und der Kommentar es weiter tut. Das ist gemessen: `grep -c -i "audit" appinfo/info.xml` ergibt **11**, verteilt auf die drei Beschreibungen (3), den Kommentarblock der abwesenden Pfade (4), den Kommentar über den Umgebungsvariablen (1) und die drei Variablennamen (3). Der Markertest hält die drei Fassungen zusätzlich fest, was ein `grep` nie getan hätte.
- **Files modified:** keine zusätzlichen
- **Committed in:** `e981eef`

### Klarstellungen im Wortlaut

- **Der englische Satz ist umgestellt.** Der Plan schlägt "group policies" als Marker vor. In der natürlichen Reihenfolge ("Group policies and sign in ... are planned as a commercial add-on") stünde er am Satzanfang und damit gross. Statt den Marker zu ändern, ist der Satz umgestellt: "Two things are planned as a commercial add-on for organisations: group policies, and sign in ...". Der Plan erlaubt ausdrücklich, den Marker zu ändern statt den Satz zu verbiegen; hier war die Umstellung die kleinere Änderung und liest sich besser als die Aufzählung, die sie ersetzt. Deutsch und Französisch folgen derselben Bauart ("Zwei Dinge sind ... geplant:", "Deux choses sont prévues ... :"), damit die drei Fassungen auch im Satzbau eine Fassung sind.
- **Zwei Gegenproben statt einer.** Das Akzeptanzkriterium verlangt die Gegenprobe für den Markertest. Der zweite Test hat seine eigene bekommen, weil eine grüne Trennungsregel über einen Text, der die Regel ohnehin erfüllt, nichts über die Regel sagt.
- **Kein RED-Commit.** Task 2 trägt `tdd="true"`, aber sein Prüfgegenstand ist der Text aus Task 1, der zum Zeitpunkt des Tests schon steht. Ein künstlich roter erster Lauf hätte bedeutet, den frisch korrigierten Text wieder falsch zu machen. Die Rotphase ist stattdessen als zwei ausgeführte und zurückgenommene Gegenproben belegt, mit der Fehlerausgabe unten.
- **Der neue Abschnitt steht am Dateiende**, nach den Gates zu den Umgebungsvariablen, und nicht zwischen dem Anspruchs-Gate und ihnen. Grund: keine bestehende Zeile anfassen, damit der Diff des Plans 152 Einfügungen und null Löschungen ist.

---

**Total deviations:** 0 auto-fixed, 1 Kriterienwortlaut präzisiert, 4 Klarstellungen
**Impact on plan:** Kein erweiterter Auftrag, keine Zusage des Plans geändert.

## Issues Encountered

- Alle vier Textdateien tragen CRLF (`core.autocrlf=true`). Die sechs Ersetzungen liefen über ein Python-Skript im `rb`/`wb`-Modus, das das Zeilenende aus der Datei nimmt; Ergebnis ist ein Diff von 40 Einfügungen und 10 Löschungen statt eines Massen-Diffs.
- Die Testsuite gibt in diesem Repo keine Summenzeile aus (`addopts` enthält `-q`), also sind die Zahlen mit `--collect-only` gezählt.

## Anforderungen

**AUDIT-06 bleibt in `REQUIREMENTS.md` Pending und wurde nicht abgehakt.** Die Anforderung hat
vier Hälften: das Wörter-Gate (19-03), die neue Wahrheit in `docs/privacy.md`,
`docs/uninstall.md` und `docs/faq.md` (19-05), der Enterprise-Absatz in drei Sprachen (dieser
Plan) und der `[Unreleased]`-Block, der alles zusammenführt (19-09). Der Haken gehört an das
Ende von 19-09.

AUDIT-04 und AUDIT-05 unverändert Complete.

## Threat Flags

Keine neue Fläche: keine Route, kein Netzzugang, keine Berechtigung, kein Paket, kein neuer
Manifesteintrag, keine Versionszeichenkette, keine Produktionsdatei ausser dem Manifesttext.
Die sechs Fäden des Registers dieses Plans:

- **T-19-31** (Repudiation, hoch): alle sechs Stellen in einem Commit gezogen, drei Markertripel per Test gehalten, zweiter Test verbietet die Nähe von Audit-Log-Wort und Geplant-Wort in einer Zeile. Beide Gegenproben gefahren und zurückgenommen.
- **T-19-32** (Tampering, mittel): die drei Beschreibungen tragen keinen Backtick und kein `|`, gemessen über `lxml`; `description_problems` ist leer, die Absätze sind durch Leerzeilen getrennt, die drei Textlängen sind 3595, 4013 und 4256 Zeichen und keine ist 0.
- **T-19-33** (Repudiation, mittel, accept): der Absatz verspricht Leistung und nicht Zugang. Das Protokoll ist als Teil der offenen App benannt, geplant bleiben Gruppen-Policies und SSO. Die Lizenzfrage bleibt OD-03.
- **T-19-34** (Tampering, hoch): `git diff 4baacbd HEAD -- appinfo/info.xml` enthält keine Zeile mit `<version>` und keine mit `image-tag`; `git tag --points-at HEAD` ist leer; kein Lauf von `scripts/build_store_release.sh`, kein `.tar.gz` im Baum, kein Upload.
- **T-19-35** (Repudiation, gering): `git diff --stat 4baacbd HEAD -- CHANGELOG.md` ist leer. Der Eintrag zu 0.1.10, der über die drei Dinge "exist in this version in no form" sagt, bleibt wörtlich stehen: ein Release-Eintrag ist ein Datum.
- **T-19-SC** (Supply Chain, gering): `git diff --stat 4baacbd HEAD -- pyproject.toml uv.lock` ist leer.

Das Anspruchs-Gate aus 19-03 und das Vokabular-Gate laufen über die vier geänderten Dateien
und sind still: kein "revisionssicher", kein "tamper proof", keine Konformitätsbehauptung, keine
Zertifizierung, kein verbotenes Wort, keine Em-Dashes, keine Emojis.

## User Setup Required

None. Der geänderte Store-Text erreicht apps.nextcloud.com erst mit dem nächsten Upload
(EXAPP-12); bis dahin bleibt der veröffentlichte Text der von 0.1.11.

## Next Phase Readiness

- Plan 19-09 findet den vollen Wortlaut der drei Manifestabsätze und die drei Markertripel oben und kann den `[Unreleased]`-Eintrag daraus schreiben, ohne das Manifest zu lesen. Der Punkt für den Changelog lautet inhaltlich: der Enterprise-Absatz nennt das Protokoll der Werkzeugaufrufe nicht mehr als geplant, weil es seit Phase 18 Teil dieser App ist, und "geplant" bezieht sich nur noch auf Gruppen-Policies und die Anmeldung über den Identitätsanbieter.
- Der Haken an AUDIT-06 in `REQUIREMENTS.md` gehört an das Ende von 19-09.
- Offener Hinweis aus 19-03, hier nicht angefasst: `tests/unit/test_exapp_admin_settings.py` trägt weiterhin eine eigene, kleinere `FORBIDDEN_CLAIMS`-Fassung für die Formularfläche. Ob die Formularprüfung auf die Liste aus `test_exapp_env_setup.py` zeigen soll, ist weiter eine Frage für 19-09.

## Verification

- `uv run pytest tests/unit tests/contract -q`: Exitcode 0, 3095 gesammelte Fälle (19-07 stand auf 3093).
- `uv run pytest tests/unit/test_exapp_env_setup.py -q`: grün, 167 Fälle (vorher 165).
- `uv run pytest tests/unit/test_exapp_env_setup.py -k "enterprise or marker or planned" -q`: 2 Fälle grün.
- `uv run ruff check .`: All checks passed. `uv run ruff format --check .`: 221 files already formatted.
- `uv run pyright`: 0 errors, 0 warnings, 0 informations.
- `uv run vulture src scripts vulture_whitelist.py`: still.
- `uv run python scripts/check_tool_budget.py`: `tools/list: 15712 bytes, 21 tools, budget 18000`, unverändert.
- Manifest über `lxml`: drei Beschreibungslängen `[3595, 4013, 4256]`, kein Backtick und kein `|` in ihrer Summe, 13 `<url>`-Einträge, `version` 0.1.11.
- `grep -ci "planned as a commercial add-on" README.md`: 1, und die Zeile lautet "Two things are planned as a commercial add-on: group policies, and sign in through the identity" , sie nennt das Audit-Log nicht.
- `grep -c "admin@infranode.dev"`: README.md 1, README.de.md 1, README.fr.md 1, appinfo/info.xml 4.
- `grep -c -i "audit" appinfo/info.xml`: 11 (siehe "Deviations" zum case-sensitiven Kriterium).
- `git diff --name-only 84da475 HEAD`: `README.de.md`, `README.fr.md`, `README.md`, `appinfo/info.xml`, `tests/unit/test_exapp_env_setup.py`, sonst nichts.
- `git diff 4baacbd HEAD -- appinfo/info.xml | grep -c "^[-+].*<version>"`: 0. Dasselbe für `image-tag`: 0.
- `git diff --stat 4baacbd HEAD -- CHANGELOG.md`: leer. `git diff --stat 4baacbd HEAD -- pyproject.toml uv.lock`: leer. `git tag --points-at HEAD`: leer. `git status --short`: kein `.tar.gz`.
- Kein Em-Dash und kein En-Dash in den vier Textdateien, gemessen zeichenweise: je 0.
- **Gegenprobe 1 (vom Plan gefordert), von Hand:** In `README.fr.md` wurde "Il est désactivé par défaut, un administrateur" zu "Un administrateur" gekürzt, also der zweite französische Marker entfernt. Ergebnis: `FAILED tests/unit/test_exapp_env_setup.py::test_the_enterprise_paragraph_carries_its_markers_at_all_six_places` mit der Meldung `the Enterprise paragraph lost a statement at one of its six places: README.fr.md: 'désactivé par défaut'`, also Datei und Marker. Zurückgenommen mit `git checkout -- README.fr.md`.
- **Gegenprobe 2, von Hand:** Der erste französische Satz wurde zu "Le journal d'audit et les politiques de groupe sont prévus comme module commercial." zusammengezogen, also die alte Behauptung wiederhergestellt. Ergebnis: `FAILED ... ::test_no_place_calls_the_audit_log_planned` mit `a place calls the audit log planned, which it has not been since phase 18: README.fr.md:1: Le journal d'audit et les politiques de groupe sont prévus comme module commercial. Activé, il`, also Datei, Zeilennummer und Zeile. Zurückgenommen mit `git checkout -- README.fr.md`, `git status --short` danach leer.

## Self-Check: PASSED

Die fünf geänderten Dateien liegen auf der Platte, beide Task-Commits stehen im Log (`e981eef`,
`13a2291`), und die zwei neuen Tests laufen am Baum auf der Platte grün, während beide
Gegenproben sie rot gemacht haben.

---
*Phase: 19-audit-log-bedienung-und-textnachzug*
*Completed: 2026-08-31*
