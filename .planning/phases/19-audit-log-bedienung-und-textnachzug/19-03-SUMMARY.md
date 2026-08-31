---
phase: 19-audit-log-bedienung-und-textnachzug
plan: 03
subsystem: tests-gates
tags: [audit-log, gate, claims, d-v1.5-02, audit-06, i18n, counter-probe]

# Dependency graph
requires:
  - phase: 12
    plan: 03
    provides: "Das Vokabular-Gate mit Reichweite, Meldungsform, Ausnahme und Gegenprobe in tests/unit/test_exapp_env_setup.py"
  - phase: 5
    plan: 9
    provides: "element_text_without_comments und description_problems als der Manifestweg ohne Kommentartext"
  - phase: 19
    plan: 02
    provides: "FORBIDDEN_CLAIMS in tests/unit/test_exapp_admin_settings.py als die erste Fassung der vier Muster, gemessen gegen die Formularfläche"
provides:
  - "FORBIDDEN_CLAIMS in tests/unit/test_exapp_env_setup.py: vier Ansprüche als Muster in EN, DE und FR, wortgetreu unten zitiert"
  - "claim_findings(text, name): eine Meldung je Zeile und Anspruch, Datei, Zeile und Anspruchsname zuerst"
  - "test_no_public_text_carries_a_forbidden_claim: das Gate über public_markdown_pages() plus den Manifesttext"
  - "Zwei Gegenproben: eine gebaute Zeile je Anspruch und eine Anspruchszeile im Manifesttext im Speicher"
  - "Die gemessene Ausgangslage der sechs Anspruchswörter über die ganze öffentliche Fläche"
affects: [19-05, 19-07, 19-08, 19-09]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ein Anspruchsverbot wird als Muster je Sprache geführt, nicht als nackter Substring: verboten ist die Behauptung, nicht das Wort"
    - "Die Reichweite eines zweiten Gates wird aus der Funktion des ersten gelesen, damit eine neue Seite von beiden Regeln erfasst wird oder von keiner"
    - "Eine Gegenprobe, die über eine Liste schleift, nennt die Länge der Liste als erste Behauptung, sonst besteht sie eine geleerte Liste kommentarlos"
    - "Ein bekanntes legitimes Vorkommen wird als eigener Negativfall festgeschrieben und nicht als Ausnahme eingetragen"

key-files:
  created: []
  modified:
    - tests/unit/test_exapp_env_setup.py

key-decisions:
  - "Kein zweites Gate-Modul und keine zweite Datei: die Liste steht neben FORBIDDEN_VOCABULARY, weil der Kommentar des bestehenden Gates zwei Orte mit derselben Aufgabe als zwei Wahrheiten benennt (IN-03)"
  - "Die Reichweite kommt aus public_markdown_pages() und element_text_without_comments(), nicht aus einer eigenen Aufzählung: eine neue Seite unter docs/ ist damit von beiden Regeln erfasst"
  - "Die Ausnahme docs/store-submission.md gilt weiter, weil sie in public_markdown_pages() steckt: ein Release-Protokoll ist ein Datum und kein Anspruch für heute"
  - "Die drei bekannten legitimen Fundstellen sind Negativfälle und keine Ausnahmen: eine Ausnahme hätte die Seite ganz freigestellt, ein Negativfall hält genau die Wortform frei"
  - "Die französische Wortstellung steht als zweite Alternative im DSGVO-Muster (conforme au RGPD), weil die deutsche Reihenfolge sie nicht erfasst"
  - "Die Zahl der Ansprüche steht als Behauptung in der ersten Gegenprobe: ohne sie ist eine Schleife über eine geleerte Liste grün, und genau das hat die Messung gezeigt"
  - "Die deutschen Probezeilen tragen echte Umlaute statt der ASCII-Ersatzform aus dem Plantext (Projektregel); an der Trefferlage ändert das nichts"

patterns-established:
  - "Ein Gate erbt Reichweite und Meldungsform vom Nachbargate und bringt nur seine eigene Regel mit"
  - "Neun Fälle als neun Tests statt als eine Schleife: eine rote Zeile sagt, welcher Fall gebrochen ist"

requirements-completed: []
# AUDIT-06 bleibt Pending: die Anforderung verlangt neben dem Wörter-Gate die neuen Sätze in
# docs/privacy.md und docs/uninstall.md sowie den Enterprise-Absatz in drei Sprachen. Das Gate
# steht, die Texte entstehen in 19-05, 19-08 und 19-09.
requirements-advanced: [AUDIT-06]

# Metrics
duration: 24min
completed: 2026-08-31
---

# Phase 19 Plan 03: Das Vier-Wörter-Gate als Anspruchsliste Summary

**Die vier Ansprüche aus D-v1.5-02 stehen als vier Muster in EN, DE und FR neben dem bestehenden Vokabular-Gate, prüfen dieselbe Fläche (drei READMEs, Changelog, `docs/**/*.md` rekursiv ohne die Ausnahme, plus den Manifesttext ohne Kommentare) und melden Datei, Zeile und Anspruchsnamen; verboten ist die Behauptung und nicht das Wort, weshalb "SIEM-Ausleitung", "specification compliant" und "conforme à la spécification" als eigene Negativfälle festgeschrieben sind, und zwei Gegenproben werden rot, sobald die Liste leer ist.**

## Performance

- **Duration:** 24 min
- **Started:** 2026-08-31T14:41:00Z
- **Completed:** 2026-08-31T15:05:00Z
- **Tasks:** 2 (Task 1 nach RED/GREEN)
- **Files modified:** 1

## Accomplishments

- `FORBIDDEN_CLAIMS` steht unmittelbar neben `FORBIDDEN_VOCABULARY` (`tests/unit/test_exapp_env_setup.py:1686`), Kommentar ab `:1688`, Liste `:1707-1725`, mit vier Einträgen, je einem sprechenden Anspruchsnamen und einem Muster mit `re.I`. Kein zweites Gate-Modul, keine zweite Datei.
- Der Kommentar über der Liste nennt die drei legitimen Fundstellen namentlich (`docs/spike-opendesk.md`, `docs/oauth-setup.md:204`, `README.fr.md:68`) und begründet, warum ein nacktes Substring-Verbot an ihnen heute rot wäre und warum ein Datenschutztext sagen darf, dass dieses Log keine SIEM-Anbindung hat.
- `claim_findings(text, name)` hat die Form von `vocabulary_findings` und trägt zusätzlich den Anspruchsnamen in der Meldung: `f"{name}:{number}: {claim}: {line.strip()}"`. Text und Name bleiben Parameter, damit dieselbe Funktion auf eine echte Seite und auf eine gebaute Zeile zeigen kann.
- `test_no_public_text_carries_a_forbidden_claim` liest die Reichweite aus `public_markdown_pages()` und ergänzt `element_text_without_comments(manifest_root)`. Die Meldung ist `"; ".join(findings)`, also eine Einzeilenkorrektur und keine Suche durch den Baum.
- Die neun Fälle aus `<behavior>` sind neun Tests, nicht eine Schleife. Fünf müssen melden (deutsche Zusammensetzung, "GDPR compliant", "AI Act compliant", "conforme au RGPD", "SIEM certified"), vier müssen still bleiben ("Audit-Log mit SIEM-Ausleitung", "specification compliant client", "conforme a la specification" samt der akzentuierten Realform aus `README.fr.md:68`, und ein gewöhnlicher Satz über das Audit-Log).
- Die Wendung "Audit-Log" bleibt ausdrücklich erlaubt und ist als eigener Fall belegt: die Phase schreibt sie in `docs/privacy.md`, `docs/uninstall.md` und den Enterprise-Absatz.
- Zwei Gegenproben: eine gebaute Zeile je Anspruch mit einer Behauptung über den Anspruchsnamen in der Meldung, und eine `description` ohne `lang` im `manifest_root`-Baum im Speicher, ohne die Datei auf der Platte zu berühren.
- Von Hand gemessen und zurückgenommen: ein geleertes `FORBIDDEN_CLAIMS` macht **beide** Gegenproben rot (siehe "Verification" und "Deviations").
- Die Testzahl der Datei steigt von 153 auf 165, die der Suite von 3015 auf 3027. `git diff --name-only a4e82c3 HEAD` nennt genau eine Datei.

## Die vier Anspruchsmuster, wortgetreu

Für die Pläne 19-05, 19-08 und 19-09, damit sie ihre Texte dagegen schreiben können, ohne die
Testdatei zu lesen:

```python
FORBIDDEN_CLAIMS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "revisionssicher",
        re.compile(r"revisionssicher|tamper[\s-]*proof|audit[\s-]*proof|inviolable", re.I),
    ),
    ("AI-Act-konform", re.compile(r"ai[\s-]*act[\s-]*(?:konform|compliant|conformes?)", re.I)),
    (
        "DSGVO-konform",
        re.compile(
            r"(?:dsgvo|gdpr|rgpd)[\s-]*(?:konform|compliant|conformes?)"
            r"|conformes?[\s-]*(?:au|aux|a la|à la)?[\s-]*(?:rgpd|gdpr|dsgvo)",
            re.I,
        ),
    ),
    (
        "SIEM-zertifiziert",
        re.compile(r"siem[\s-]*(?:zertifiziert|certified|certifi[eé]e?s?)", re.I),
    ),
)
```

Was das für einen neuen Satz bedeutet, in einem Satz je Anspruch:

| Anspruch | Rot wird | Grün bleibt |
|----------|----------|-------------|
| revisionssicher | `revisionssicher`, `tamper proof`, `tamper-proof`, `audit proof`, `inviolable` | "hash-verkettet", "the chain of the record", "changed or removed unnoticed" |
| AI-Act-konform | `AI Act compliant`, `AI-Act-konform`, `AI act conforme` | eine Nennung des AI Act ohne das Wort konform/compliant/conforme dahinter |
| DSGVO-konform | `DSGVO-konform`, `GDPR compliant`, `RGPD conforme`, `conforme au RGPD`, `conforme aux RGPD` | "die DSGVO betrifft den Betreiber", "specification compliant", "conforme à la spécification" |
| SIEM-zertifiziert | `SIEM zertifiziert`, `SIEM certified`, `SIEM certifié`, `SIEM-certifiees` | "SIEM-Ausleitung", "dieses Log hat keine SIEM-Anbindung" |

Reichweite: `README.md`, `README.de.md`, `README.fr.md`, `CHANGELOG.md`, alles unter `docs/`
rekursiv ausser `docs/store-submission.md`, plus der Elementtext von `appinfo/info.xml` ohne
Kommentare. Nicht in der Reichweite: `.planning/`, `src/`, `tests/`, `scripts/`.

## Die gemessene Ausgangslage

Kommando (Task 2 fordert die Messung schriftlich, nicht als Test):

```bash
for w in revisionssicher dsgvo gdpr rgpd "ai act" siem; do
  rg -n -i -- "$w" README.md README.de.md README.fr.md CHANGELOG.md appinfo/info.xml docs/
done
```

| Wort | Treffer | Datei und Zeile | Urteil |
|------|---------|-----------------|--------|
| revisionssicher | 0 | - | - |
| dsgvo | 0 | - | - |
| gdpr | 0 | - | - |
| rgpd | 0 | - | - |
| ai act | 0 | - | - |
| siem | 1 | `docs/spike-opendesk.md:1707` "Audit-Log mit SIEM-Ausleitung als bezahltes Add-on vor, und ein Audit-Log in einem" | **legitim**, nicht zu korrigieren: das ist die Wiedergabe einer offenen Verhandlungsfrage über ein Angebot Dritter, kein Anspruch dieses Projekts. Als Negativfall festgeschrieben in `test_the_siem_readout_question_of_the_spike_is_no_claim` |

Zweite Messung über die Wortformen, die die Muster brauchen, weil ein Anspruch ohne die sechs
Wörter oben nicht auskommt, ein legitimer Satz aber schon:

| Wort | Treffer in der Reichweite | Urteil |
|------|---------------------------|--------|
| compliant | `docs/oauth-setup.md:204` "specification compliant client", `docs/conference-talk.md:84` "spec compliant server" | **legitim**: kein Regelwerk davor, die Muster verlangen `dsgvo`/`gdpr`/`rgpd`/`ai act` unmittelbar vor dem Wort |
| conforme | `README.fr.md:68` "conforme à la spécification d'autorisation MCP" | **legitim**: `(?:au\|aux\|a la\|à la)?` steht vor `rgpd\|gdpr\|dsgvo` und nicht vor einem beliebigen Wort |
| certifi* | 51 Zeilen in fünf Dateien (`docs/store-submission.md` 23, `docs/staging-setup.md` 8, `docs/exapp-install.md` 9, `docs/app-id-freeze.md` 8, `docs/dependency-audit.md` 3), alle über TLS-, Store- und Abhängigkeitszertifikate | **legitim**: die Muster verlangen `siem` unmittelbar davor |

Erwartung der Recherche (kein Anspruchsmuster trifft heute) bestätigt: der Gate-Test war beim
ersten Lauf über den unveränderten Baum grün, ohne eine einzige Textkorrektur.

## Task Commits

1. **Task 1: Anspruchsliste und Gate über Markdown und Manifest** - `faacde7` (test, RED: zehn Fälle mit `NameError`), `f54de5e` (feat, GREEN)
2. **Task 2: Gegenprobe und gemessene Ausgangslage** - `086d562` (test, beide Gegenproben samt der Längenbehauptung)

## Files Created/Modified

- `tests/unit/test_exapp_env_setup.py` - `FORBIDDEN_CLAIMS` neben `FORBIDDEN_VOCABULARY` mit einem dreiteiligen `#:`-Kommentar (was verboten ist, warum es Muster und keine Substrings sind, wie die Muster gebaut sind); ein neuer Abschnittskopf im Stil der beiden bestehenden Gate-Abschnitte; `claim_findings`; `test_no_public_text_carries_a_forbidden_claim`; neun Fälle; zwei Gegenproben. Keine bestehende Zeile geändert, keine bestehende Behauptung abgeschwächt.

## Decisions Made

- **Die Liste bleibt in dieser Datei.** Der Kommentar des bestehenden Vokabular-Gates (`:1953-1961`) sagt selbst, zwei Orte mit derselben Aufgabe wären zwei Wahrheiten, und ein neues Modul hätte ein grünes Sicherheitsgate an einen zweiten Ort gebaut, ohne die Regel besser zu machen. Der Preis ist derselbe wie dort: ein Dateiname, der thematisch weiter ist als sein Inhalt.
- **Reichweite lesen statt aufzählen.** Das Gate ruft `public_markdown_pages()` und `element_text_without_comments()`, also genau die zwei Wege des Nachbargates. Eine eigene Aufzählung hätte die nächste neue Seite unter `docs/` nur einer der beiden Regeln unterworfen.
- **Negativfälle statt Ausnahmen.** Eine zweite Ausnahmedatei (`docs/spike-opendesk.md`) hätte die ganze Seite freigestellt, auch für einen echten Anspruch, der später dort landet. Drei Negativfälle halten genau die drei Wortformen frei und lassen die Seiten im Gate.
- **Die französische Wortstellung als zweite Alternative.** `conforme au RGPD` ist die Form, in der Französisch diesen Anspruch schreibt; das deutsche Muster `(dsgvo|gdpr|rgpd)` davor hätte sie nicht erfasst. Geprüft ist, dass die Erweiterung `conforme à la spécification` weiter frei lässt: die optionale Gruppe steht vor `rgpd|gdpr|dsgvo` und nicht vor einem beliebigen Wort.
- **Nicht-fangende Gruppen.** Die Muster verwenden `(?:...)` statt `(...)`, weil keine Gruppe ausgelesen wird und `search()` ohnehin nur die Trefferfrage beantwortet. Der Codebeispiel-Entwurf der Recherche schrieb fangende Gruppen; das ist ohne Verhaltensunterschied, aber die Absicht ist so lesbar.
- **Echte Umlaute in den Probezeilen.** Der Plan schreibt die deutsche Negativzeile als "Das Audit-Log haelt seine Eintraege hash-verkettet"; im Test steht sie mit `ä` (Projektregel, und in `tests/unit/` sind Umlaute der Normalfall). An der Trefferlage ändert das nichts, weil kein Muster ein Umlautzeichen enthält.
- **Strenger als die Liste, wo es nichts kostet.** `certifi[eé]e?s?` und `conformes?` fassen die gebeugten Formen mit; die Muster bleiben trotzdem an ihr Regelwerk gebunden, also erzeugt die Strenge kein neues Falsch-Positiv. Die Recherche erlaubt strenger ausdrücklich und laxer nicht.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Die erste Gegenprobe war grün, obwohl `FORBIDDEN_CLAIMS` leer war**

- **Found during:** Task 2 (bei der vom Plan geforderten Messung mit geleerter Liste)
- **Issue:** `<behavior>` von Task 2 verlangt, dass **beide** Gegenproben rot werden, wenn die Liste leer ist. Die Bauart aus dem Recherche-Codebeispiel ist eine Schleife über `FORBIDDEN_CLAIMS`; mit einer leeren Liste läuft der Schleifenkörper nie, der Test besteht ohne eine einzige Behauptung, und die Gegenprobe hätte genau den Fall verschwiegen, für den sie existiert. Gemessen: nur `test_the_claim_gate_fires_on_the_manifest_text` wurde rot.
- **Fix:** `assert len(FORBIDDEN_CLAIMS) == 4, FORBIDDEN_CLAIMS` als erste Zeile der Schleifen-Gegenprobe, mit dem Grund im Docstring und dem Verweis auf `test_the_vocabulary_gate_reads_a_list_that_is_not_empty`, das für die Reichweite dasselbe tut. Eine fünfte Anspruchszeile macht diese Zahl einmal rot, also sichtbar, statt eine leere Messung zu bestehen.
- **Files modified:** tests/unit/test_exapp_env_setup.py
- **Verification:** Mit geleerter Liste sind jetzt beide Gegenproben rot (Ausgabe unter "Verification"); mit der Liste sind beide grün.
- **Committed in:** `086d562`

### Abweichung im Wortlaut eines Akzeptanzkriteriums

Verifikationsschritt 3 des Plans erwartet, dass `git diff --name-only 4baacbd HEAD` ausser
Planungsartefakten allein `tests/unit/test_exapp_env_setup.py` nennt. Gemessen sind zusätzlich
die neun Dateien der Pläne 19-01 und 19-02, die vor diesem Plan auf demselben Ausgangspunkt
gelaufen sind. Der Sinn des Schritts, dass **dieser** Plan nur eine Datei anfasst, ist gegen
den Vorgängerstand geprüft: `git diff --name-only a4e82c3 HEAD` nennt genau
`tests/unit/test_exapp_env_setup.py`. Die Schritte 4 und 5 (kein Produktionstext, kein Paket)
sind unverändert gegen `4baacbd` gelaufen und leer.

Task 1 erwartet `grep -c "FORBIDDEN_CLAIMS"` mindestens 2 und `grep -c "spike-opendesk"`
mindestens 1; gemessen sind 3 und 2, also über der Untergrenze.

### Zum RED-Lauf und zu ruff

Der RED-Commit `faacde7` trägt zehn Tests, die mit `NameError: name 'claim_findings' is not
defined` fallen, und ist deshalb der einzige Commit dieses Plans, an dem `ruff check` nicht
still ist (zwölf mal `F821`, undefinierter Name). Das ist der Preis einer echten Rotphase in
einer Datei, in der Test und Gate zusammenliegen; ab `f54de5e` ist die Datei wieder still, und
kein Zwischenstand wurde gepusht.

### Ein selbst verursachter Rückschritt, offengelegt

Die erste Fassung der zwei Gegenproben war noch nicht committet, als die Messung mit der
geleerten Liste lief; das Zurücknehmen der Messung per `git checkout -- <datei>` hat sie
mitgenommen, und sie wurden neu geschrieben (mit der Längenbehauptung, siehe Abweichung 1).
Kein Verlust an Inhalt, aber die Lehre gehört ins Protokoll: eine Messung, die eine Datei
verändert, wird erst nach dem Commit der Arbeit gefahren.

---

**Total deviations:** 1 auto-fixed (Rule 1), 2 Kriterienwortlaute präzisiert, 1 Arbeitsfehler offengelegt
**Impact on plan:** Kein erweiterter Auftrag. Abweichung 1 stellt genau die Eigenschaft her, die `<behavior>` von Task 2 verlangt.

## Issues Encountered

- Der Arbeitsbaum trägt CRLF (`core.autocrlf=true`), also lief die Messung mit der geleerten Liste über ein Python-Skript, das die Datei binär liest und schreibt und das Zeilenende aus der Datei nimmt. Ein erster Versuch mit `\n` als Suchmuster fand die Stelle nicht; mit `\r\n` schon. Nach dem Zurücknehmen war `git status --short` leer.
- Die Testsuite gibt in diesem Repo keine Summenzeile aus (`addopts` enthält `-q`), also sind die Zahlen mit `--collect-only` gezählt.

## Anforderungen

**AUDIT-06 bleibt in `REQUIREMENTS.md` Pending und wurde nicht abgehakt.** Die Anforderung hat
drei Hälften: das Wörter-Gate (dieser Plan), die neue Wahrheit in `docs/privacy.md` und
`docs/uninstall.md` (19-05) und der Enterprise-Absatz in drei Sprachen (19-08), zusammengeführt
im `[Unreleased]`-Block von 19-09. Ein Haken hier wäre dieselbe Art von Aussage, die Phase 18
bei AUDIT-01 bis AUDIT-03 bewusst zurückgehalten hat.

AUDIT-04 unverändert Pending, AUDIT-05 seit 19-02 Complete.

## Threat Flags

Keine neue Fläche: keine Route, kein Netzzugang, keine Berechtigung, kein Paket, kein
Manifesteintrag, keine Versionszeichenkette, keine Produktionsdatei. Die vier Fäden des
Bedrohungsmodells dieses Plans:

- **T-19-08** (Repudiation, hoch): Vier Anspruchsmuster in EN, DE und FR über die Reichweite des bestehenden Vokabular-Gates, Meldung mit Datei, Zeile und Anspruchsnamen. Fünf Positivfälle belegen, dass die Muster die Behauptung in allen drei Sprachen fassen.
- **T-19-09** (Tampering, mittel): Zwei Gegenproben, eine über gebaute Zeilen je Anspruch, eine über den Manifesttext im Speicher. Ein geleertes `FORBIDDEN_CLAIMS` macht **beide** rot, gemessen und in "Verification" festgehalten; ohne die Längenbehauptung aus Abweichung 1 wäre die erste vakuum-grün geblieben.
- **T-19-10** (Falsch-Positiv, niedrig): Wortformen statt nackter Substrings, die drei bekannten legitimen Fundstellen namentlich als Negativfall, die akzentuierte Realform aus `README.fr.md:68` zusätzlich. Die Wendung "Audit-Log" bleibt erlaubt und ist als eigener Fall belegt (Pitfall 15).
- **T-19-SC** (Supply Chain, niedrig): `git diff --stat 4baacbd HEAD -- pyproject.toml uv.lock` ist leer, `re` ist Standardbibliothek.

Ein Hinweis für 19-05, 19-08 und 19-09: das Gate liest `docs/**/*.md` rekursiv. Jede neue
Doku-Seite dieser Phase steht damit unter beiden Regeln, ohne dass jemand sie eintragen muss;
`docs/store-submission.md` ist die einzige Ausnahme und bleibt es.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Die vier Muster stehen oben wortgetreu samt einer Tabelle, was rot wird und was grün bleibt; 19-05, 19-08 und 19-09 können ihre Sätze dagegen schreiben, ohne die Testdatei zu lesen.
- Der Enterprise-Absatz aus 19-PATTERNS.md (`Audit log, group policies and SSO ...` in drei Sprachen) läuft durch alle vier Muster still: gemessen mit `claim_findings` über alle drei Fassungen, je eine leere Liste. Er nennt weder ein Regelwerk noch eine Zertifizierung, für 19-08 ist damit nichts umzuformulieren.
- Der Wortlaut der Beschriftung aus 19-02 ("changed or removed unnoticed", "recompute", "180 days", "100 MB") ist ebenfalls anspruchsfrei; wenn 19-05 daraus in `docs/privacy.md` zitiert, kommt das Gate nicht in die Quere.
- `tests/unit/test_exapp_admin_settings.py` trägt weiterhin seine eigene, kleinere `FORBIDDEN_CLAIMS`-Fassung aus 19-02 für die Formularfläche. Das sind zwei Listen für zwei Flächen (Formular gegen öffentlichen Text), aber es sind zwei Wortlaute derselben Regel: 19-09 sollte entscheiden, ob die Formularprüfung auf die Liste dieses Plans zeigt. Diese Zusammenlegung ist hier bewusst nicht gemacht worden, weil der Plan ausdrücklich nur die eine Datei anfasst.

## Verification

- `uv run pytest tests/unit/test_exapp_env_setup.py -q`: grün, 165 Fälle (vorher 153, also zwölf mehr: zehn aus Task 1 und zwei Gegenproben).
- `uv run pytest tests/unit/test_exapp_env_setup.py -k claim -q`: 12 Fälle grün.
- `uv run pytest tests/unit/test_exapp_env_setup.py -k forbidden_claim -q`: grün am unveränderten Baum.
- `uv run pytest tests/unit tests/contract -q`: Exitcode 0, 3027 gesammelte Fälle (19-02 stand auf 3015).
- `uv run ruff check .`: All checks passed. `uv run ruff format --check .`: 218 files already formatted.
- `uv run pyright`: 0 errors, 0 warnings, 0 informations.
- `uv run vulture src scripts vulture_whitelist.py`: still.
- `uv run python scripts/check_tool_budget.py`: `tools/list: 15712 bytes, 21 tools, budget 18000`, unverändert.
- `git diff --name-only a4e82c3 HEAD`: `tests/unit/test_exapp_env_setup.py`, sonst nichts.
- `git diff --stat 4baacbd HEAD -- README.md README.de.md README.fr.md CHANGELOG.md docs appinfo/info.xml`: leer.
- `git diff --stat 4baacbd HEAD -- pyproject.toml uv.lock`: leer.
- `grep -c` in `tests/unit/test_exapp_env_setup.py`: `FORBIDDEN_CLAIMS` 3, `def claim_findings` 1, `spike-opendesk` 2.
- **Gegenprobe von Hand (vom Plan gefordert):** `FORBIDDEN_CLAIMS` binär auf `()` gesetzt, dann `uv run pytest tests/unit/test_exapp_env_setup.py -k "claim_gate_fires" -q`. Beide Gegenproben rot: `FAILED test_the_claim_gate_fires_on_a_constructed_line` und `FAILED test_the_claim_gate_fires_on_the_manifest_text`. Zurückgenommen mit `git checkout -- tests/unit/test_exapp_env_setup.py`, `git status --short` danach leer.
- **Erster Durchgang derselben Messung (vor Abweichung 1):** nur `test_the_claim_gate_fires_on_the_manifest_text` wurde rot, die Schleifen-Gegenprobe blieb grün. Das ist der Befund, der zur Längenbehauptung geführt hat.

## Self-Check: PASSED

Die geänderte Datei liegt auf der Platte, alle drei Commits stehen im Log (`faacde7`,
`f54de5e`, `086d562`), `FORBIDDEN_CLAIMS` liest sich mit vier Einträgen und
`claim_findings("This log is revisionssicher.\n", "probe.md")` liefert genau eine Meldung, die
mit `probe.md:1: revisionssicher:` beginnt.

---
*Phase: 19-audit-log-bedienung-und-textnachzug*
*Completed: 2026-08-31*
