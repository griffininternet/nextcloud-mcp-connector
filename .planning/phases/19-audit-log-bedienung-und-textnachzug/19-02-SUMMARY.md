---
phase: 19-audit-log-bedienung-und-textnachzug
plan: 02
subsystem: exapp-ui
tags: [audit-log, admin-settings, copy, works-council, audit-05, in-06, d-v1.5-02, d-v1.5-04]

# Dependency graph
requires:
  - phase: 18
    plan: 07
    provides: "Das siebte Formularfeld audit_log als Checkbox mit default False, samt der kurzen Beschriftung und ihrem Vertagungsvermerk"
  - phase: 18
    plan: 08
    provides: "exapp/audit_verify.LIMIT_SENTENCE als der Grenzsatz, an dem sich die Formularbeschriftung messen lässt"
  - phase: 18
    plan: 01
    provides: "audit/store.py mit RETENTION_DAYS, SIZE_LIMIT_BYTES, USER_SILENCE_DAYS und dem kommentierten Schema der 17 Felder"
provides:
  - "ADMIN_FIELD_AUDIT_LOG_DESCRIPTION in der langen Fassung: sechs Pflichten, Leistung, Grenze, Mitbestimmung, Aufbewahrung, Fortbestand, Aktivierungszyklus"
  - "Der volle Wortlaut der Beschriftung, unten wörtlich zitiert, als Zitatquelle für 19-05 und 19-09"
  - "FORBIDDEN_CLAIMS in tests/unit/test_exapp_admin_settings.py: die vier Ansprüche aus D-v1.5-02 als Muster in drei Sprachen"
  - "LEVEL_WORD: ein Wortformtest über alle sieben Formularfelder, der eine wählbare Inhaltsstufe an der Oberfläche ausschließt"
  - "Ein Test, der Formularhälfte und Konsolenhälfte des Grenzsatzes an ihren tragenden Begriffen gegeneinander hält"
affects: [19-03, 19-05, 19-06, 19-09]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Eine Zusage im Formulartext wird an die Konstante gebunden, die sie beschreibt, statt an eine Zahl im Satz"
    - "Zwei Orte, die dieselbe Grenze aussprechen, werden in einem Test aneinander gehalten und nicht jeder für sich geprüft"
    - "Ein Verbotswort wird als Wortform mit Wortgrenzen geprüft, weil derselbe Buchstabenlauf in gewöhnlichen Wörtern steckt"
    - "Ein Anspruchsverbot wird als Muster je Sprache geführt, nicht als nackter Substring: verboten ist die Behauptung, nicht das Wort"

key-files:
  created: []
  modified:
    - src/mcp_connector/exapp/ui/strings.py
    - tests/unit/test_exapp_admin_settings.py

key-decisions:
  - "Der Grenzsatz ist inhaltlich gleich und nicht wortgleich mit LIMIT_SENTENCE: gebunden sind die zwei tragenden Begriffe, nicht der Satzbau, weil das Formular vor der Entscheidung spricht und die Konsole nach der Prüfung"
  - "Das Wort für die zweite Inhaltsstufe wird als Wortform mit Wortgrenzen verboten, nicht als Substring: die Prüfung über json.dumps des Feldes soll an einem gewöhnlichen englischen Wort nicht scheitern"
  - "Der bestehende Beschreibungstest ist gewachsen und nicht ersetzt worden: die vier Behauptungen aus Phase 18 stehen unverändert darin"
  - "Die Verbotsliste ist zweigleisig geblieben: die vier deutschen Substrings der Phase 18 UND vier Muster mit ihren EN- und FR-Entsprechungen daneben"
  - "Aufbewahrung steht als 180 Tage Vorgabe im Text und nicht als Zusage auf Dauer, und der Satz nennt alle drei automatischen Löschwege, statt einen davon zum einzigen zu erklären"
  - "ADMIN_FIELD_AUDIT_LOG_LABEL blieb unverändert: der Text wird durch die lange Beschreibung nicht irreführend"

patterns-established:
  - "Der #:-Kommentar über einer Textkonstante zählt die Pflichten des Satzes numeriert auf und nennt die Anforderung, die Entscheide und den Review-Befund, die ihn verlangen"
  - "Eine Gegenprobe je neue Zusage: der Rückbau des Wortes macht den Test rot, einmal von Hand ausgeführt und zurückgenommen"

requirements-completed: [AUDIT-05]

# Metrics
duration: 20min
completed: 2026-08-31
---

# Phase 19 Plan 02: Die lange Beschriftung des Audit-Schalters Summary

**Die Formularbeschriftung des Audit-Schalters sagt jetzt alle sechs Dinge, die ein Administrator vor dem Einschalten braucht, einschließlich der drei Felder, die die kurze Fassung verschwieg (Parameternamen, Ablehnungsgrund, Dauer, Review-Befund IN-06), der Grenze in denselben tragenden Begriffen wie das Prüfkommando, des Mitbestimmungshinweises und der Aufbewahrung in den Zahlen des Codes; das Formular selbst ist unverändert und trägt kein Wort einer wählbaren Inhaltsstufe.**

## Performance

- **Duration:** 20 min
- **Started:** 2026-08-31T14:11:00Z
- **Completed:** 2026-08-31T14:31:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- `ADMIN_FIELD_AUDIT_LOG_DESCRIPTION` ist ersetzt und trägt die sechs Pflichten des Plans. Der volle Wortlaut steht unten, damit Plan 19-05 und Plan 19-09 daraus zitieren können, ohne die Datei zu lesen.
- Die drei Felder aus dem Review-Befund IN-06 stehen im Text: die Namen der Parameter mit der Pflichtwendung "the names of the parameters, never their values", der Ablehnungsgrund als "a fixed identifier of the reason" und die Dauer als "how long it took".
- Die Grenzbeschreibung ist an `exapp/audit_verify.LIMIT_SENTENCE` gebunden: "changed or removed unnoticed" und "recompute" stehen wortgleich in beiden Sätzen, und ein eigener Test hält die zwei gegeneinander, statt jeden für sich zu prüfen.
- Der Mitbestimmungshinweis (D-v1.5-04) nennt "works council", Deutschland und Österreich, und sagt ausdrücklich "this is a hint and not legal advice".
- Aufbewahrung und Fortbestand stehen in den Zahlen des Codes: 180 Tage (`store.RETENTION_DAYS`), 100 MB (`store.SIZE_LIMIT_BYTES`), die Kontolöschung als dritter automatischer Löschweg, und dass eine Zeile `occ mcp_connector:purge` und die Deinstallation übersteht, während das Löschen des Datenvolumes sie mitnimmt. Kein Satz erklärt einen der drei Wege zum einzigen.
- Das Wort einer zweiten Inhaltsstufe ist aus `strings.py` vollständig verschwunden: `grep -ci "full"` meldete vorher 1 Treffer (im Vertagungsvermerk der kurzen Fassung) und meldet jetzt 0. Kein Feldtext, kein Feldtyp und keine Optionsliste des Formulars trägt es, gehalten von einem Test über alle sieben Felder.
- Das Formular ist unangetastet: `admin_settings.form_scheme()` baut dieselben sieben Felder, `audit_log` bleibt Checkbox mit `"default": False` und ohne `sensitive` in jeder Schreibweise. Die vier Nachbartests, die das halten, sind unverändert.
- Zwei Gegenproben von Hand ausgeführt und zurückgenommen (siehe "Verification"): der Rückbau von "works council" und ein eingefügtes Stufenwort machten je den zuständigen Test rot.

## Der volle Wortlaut der neuen Beschriftung

`ADMIN_FIELD_AUDIT_LOG_LABEL` (unverändert):

```
Keep a record of tool calls
```

`ADMIN_FIELD_AUDIT_LOG_DESCRIPTION` (1280 Zeichen, ein Fließtextabsatz):

```
With this on, every tool call is written down: the account it ran for, the name of the tool,
the time, the app that called, whether the call succeeded, how long it took, and, where a call
was refused, a fixed identifier of the reason. A row also holds the names of the parameters,
never their values. No parameter value and no part of a result is stored, and neither is a
network address, a user agent or the text of an error message. A later check of the record
shows that an entry was changed or removed unnoticed. It does not show who is able to write the
file behind it, because whoever can write it can recompute the chain behind the change. A
record that ties calls to named accounts can come under the codetermination of a works council
in Germany and in Austria, so whoever switches this on settles that beforehand; this is a hint
and not legal advice. Rows are kept for 180 days by default, the record stops growing at 100 MB
where the oldest rows give way, and an account removed in Nextcloud takes its own rows with it.
A row outlives occ mcp_connector:purge and the removal of this app, and only deleting the data
volume of this app deletes the record with it. This is off unless you switch it on, and a change
takes effect after you disable and enable this app again.
```

Die Zeilenumbrüche oben sind Umbrüche dieses Dokuments; die Konstante ist eine einzige
Zeichenkette aus implizit verketteten Literalen ohne Zeilenumbruch, ohne Backtick, ohne
Em-Dash und ohne Nicht-ASCII-Zeichen.

## Task Commits

1. **Task 1: Die lange Fassung der Beschriftung schreiben** - `9765014` (feat)
2. **Task 2: Zusagen an die Beschriftung als Tests** - `3faa425` (test)

## Files Created/Modified

- `src/mcp_connector/exapp/ui/strings.py` - `ADMIN_FIELD_AUDIT_LOG_DESCRIPTION` ersetzt; der `#:`-Kommentar darüber ersetzt den Vertagungsvermerk durch die sechs Pflichten als numerierte Liste, nennt AUDIT-05, D-v1.5-02, D-v1.5-04 und IN-06, und hält fest, dass die Grenzbeschreibung an `audit_verify.LIMIT_SENTENCE` gebunden ist und ein Test das hält. `ADMIN_FIELD_AUDIT_LOG_LABEL` unverändert, `__all__` unverändert (beide Namen standen schon darin).
- `tests/unit/test_exapp_admin_settings.py` - `FORBIDDEN_CLAIMS` und `LEVEL_WORD` als Modulkonstanten; `test_the_audit_log_description_says_what_is_kept_and_what_is_not` erweitert (Docstring angepasst, die vier Behauptungen der Phase 18 unverändert enthalten); zwei neue Tests `test_the_limit_of_the_record_reads_the_same_in_the_form_and_in_the_console` und `test_no_field_of_the_form_offers_a_level_of_recording`; die zwei Audit-Konstanten in die Parametrisierung der Em-Dash- und Emoji-Regel aufgenommen.

## Decisions Made

- **Inhaltlich gleich, nicht wortgleich:** Der Plan verlangt für den Grenzsatz "inhaltlich gleich" mit `LIMIT_SENTENCE` und für zwei Begriffe Wortgleichheit. Der Satz im Formular heißt deshalb "A later check of the record shows that an entry was changed or removed unnoticed", der in der Konsole "This check finds an entry that was changed or removed unnoticed": das Formular spricht über eine Prüfung, die es noch nicht gibt, die Konsole über die, die gerade gelaufen ist. Gebunden und getestet sind die zwei tragenden Begriffe.
- **Wortform statt Substring beim Stufenwort:** Die Prüfung läuft über `json.dumps(field).lower()` des ganzen Feldes. Ein nacktes Substring-Verbot wäre an jedem gewöhnlichen englischen Wort mit derselben Buchstabenfolge gescheitert, und ein Formular, das dieses Wort nie sagen darf, würde damit an einem Satz scheitern, der harmlos ist. `LEVEL_WORD = re.compile(r"\bfull\b")` ist die Regel; die Gegenprobe hat sie rot gesehen.
- **Die Verbotsliste zweigleisig:** Die vier deutschen Substrings der Phase 18 (`revisionssicher`, `ai-act`, `dsgvo`, `siem`) bleiben als Schleife stehen, weil sie ein bestehender Testinhalt sind. Daneben stehen vier Muster, die dieselben Ansprüche in EN und FR fassen (`tamper proof`, `AI Act compliant`, `GDPR compliant`, `conforme au RGPD`, `SIEM certified`). Verboten ist die Behauptung, nicht das Wort: ein Text darf sagen, dass dieses Log keine SIEM-Anbindung hat.
- **Kein Satz über einen einzigen Löschweg:** `19-CONTEXT.md` korrigiert D-v1.5-01 ausdrücklich: es gibt drei automatische Löschwege. Der Text nennt Frist, Obergrenze und Kontolöschung in einem Satz und behauptet über keinen davon, er sei der einzige.
- **Das Label bleibt:** "Keep a record of tool calls" wird durch die lange Beschreibung nicht irreführend, sondern von ihr erklärt. Eine Änderung hätte einen Nachbartest (`audit_log["title"] == strings.ADMIN_FIELD_AUDIT_LOG_LABEL`) ohne Gewinn berührt.
- **Der bestehende Test ist gewachsen:** Der Plan verlangt Erweitern statt Ersetzen. Die vier Behauptungen der kurzen Fassung stehen unverändert im erweiterten Test, nur der Docstring sagt nicht mehr, die lange Fassung gehöre einer späteren Phase.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing coverage] Die neue Beschriftung fiel unter keine Em-Dash- und Emoji-Regel**

- **Found during:** Task 2
- **Issue:** `test_no_new_sentence_carries_an_em_dash_or_an_emoji` ist parametrisiert und listet zehn Konstanten des Katalogs. Die beiden Audit-Konstanten fehlten darin (Phase 18 hat sie nicht nachgetragen), also war der längste und neueste Satz des Formulars der einzige, dessen Einhaltung der Projektregeln nur von einem Review abhing.
- **Fix:** `ADMIN_FIELD_AUDIT_LOG_LABEL` und `ADMIN_FIELD_AUDIT_LOG_DESCRIPTION` in die Parametrisierung aufgenommen, mit einem Kommentar, warum. Beide sind grün: kein Em-Dash, kein En-Dash, reines ASCII.
- **Files modified:** tests/unit/test_exapp_admin_settings.py
- **Verification:** Zwei zusätzliche Testfälle, beide grün; die Gesamtzahl der Suite steigt von 3011 auf 3015 (2 neue Tests plus diese 2 Fälle).
- **Committed in:** `3faa425`

### Abweichung im Wortlaut eines Akzeptanzkriteriums

Task 1 erwartet `grep -c "changed or removed unnoticed"` und `grep -c "recompute"` in `strings.py`
"mindestens 1"; gemessen sind je 2, weil der `#:`-Kommentar über der Konstante beide Begriffe
nennt, um die Bindung an `audit_verify.LIMIT_SENTENCE` im Code selbst festzuhalten. Das
Kriterium ist eine Untergrenze, also erfüllt.

Task 1 verlangt weiter, `grep -ci "full"` zeige "keinen Treffer innerhalb von
`ADMIN_FIELD_AUDIT_LOG_DESCRIPTION`", und erlaubt Treffer in anderen Konstanten. Zu benennen
gibt es keinen: der einzige Treffer der Datei stand im Vertagungsvermerk der kurzen Fassung
("The full wording an administrator needs ...") und ist mit ihm verschwunden. `strings.py` trägt
das Wort jetzt an keiner Stelle mehr, auch nicht in einem Kommentar.

Die Backtick-Prüfung gilt dem Text, nicht dem Kommentar: die Konstantenwerte tragen keinen
Backtick, der `#:`-Kommentar darüber verwendet die doppelten Backticks der Hausform (wie an
`ADMIN_FIELD_TALK_SEND_DESCRIPTION` und `ADMIN_FIELD_CIMD_DESCRIPTION`), weil das Sphinx-Markup
dieses Moduls ist und kein Text, den ein Administrator liest.

### Zur TDD-Reihenfolge von Task 2

Task 2 ist `tdd="true"`, seine Zusagen prüfen aber Text, den Task 1 desselben Plans schon
geschrieben hat: eine echte RED-Phase über eine fehlende Implementierung gibt es hier nicht.
Der Plan setzt an ihre Stelle die Gegenprobe von Hand (Akzeptanzkriterium 2), und genau die ist
gelaufen, in zwei Fassungen, beide dokumentiert unter "Verification". Kein Testcommit ohne
gesehene Rotphase.

---

**Total deviations:** 1 auto-fixed (Rule 2), 2 Kriterienwortlaute präzisiert
**Impact on plan:** Kein erweiterter Auftrag. Die Aufnahme in die Em-Dash-Parametrisierung
berührt nur die Datei, die der Plan ohnehin ändert.

## Issues Encountered

- Der Arbeitsbaum trägt gemischte Zeilenenden (`core.autocrlf=true`); die zwei Gegenproben liefen deshalb über ein Python-Skript, das die Datei binär liest und schreibt, statt über `sed -i`, das einen Massen-Diff erzeugt hätte. Nach dem Zurücknehmen war `git diff` für `strings.py` leer.
- Die Testsuite gibt in diesem Repo keine Summenzeile aus (`addopts` enthält `-q`, die Ausgabe endet mit der Punktzeile), also ist die Zahl über `--collect-only -q` gezählt: 3015 Fälle, Exitcode 0.

## Anforderungen

**AUDIT-05 ist erfüllt und in `REQUIREMENTS.md` abgehakt.** Die Anforderung hat zwei Hälften:
"ab Werk abgeschaltet und über die Admin-Einstellungen einschaltbar" liefert Phase 18 (Plan
18-07, `"default": False` und das siebte Feld), "die Beschriftung sagt, was das Log leistet, was
es nicht leistet, und dass ein nutzerbezogenes Protokoll mitbestimmungsrelevant sein kann"
liefert dieser Plan. Beide Hälften sind durch Tests gehalten, und Plan 19-09 prüft die
Anforderung als Ganzes nach; ein Haken hier nimmt dieser Prüfung nichts, weil der Text im Baum
steht und nicht in einer Absicht.

AUDIT-04 und AUDIT-06 bleiben unverändert Pending.

## Threat Flags

Keine neue Fläche: keine Route, kein Netzzugang, keine Berechtigung, kein Paket, kein
Manifesteintrag, keine Versionszeichenkette, keine Änderung am Formular selbst. Die fünf Fäden
des Bedrohungsmodells dieses Plans:

- **T-19-04** (Repudiation, hoch): Alle sechs Pflichten stehen im Text und jede als Behauptung im Test, darunter die drei Felder des Review-Befunds IN-06. Die vier Verbotswörter bleiben draußen, jetzt zusätzlich in ihren EN- und FR-Entsprechungen.
- **T-19-05** (Information Disclosure, mittel): Keine Stufe, kein Auswahlfeld. `LEVEL_WORD` läuft über alle sieben Felder, über `description`, `title`, `type` und jede Optionsliste, als Wortform. `sensitive` bleibt in jeder Schreibweise abwesend, gehalten von den zwei bestehenden Tests.
- **T-19-06** (Repudiation, mittel): Formularhälfte und Konsolenhälfte des Grenzsatzes werden in einem Test aneinander gehalten. Ein Auseinanderdriften der beiden Orte fällt auf, bevor es veröffentlicht wird (Pitfall 12).
- **T-19-07** (Compliance und Mitbestimmung, hoch, akzeptiert): "Ab Werk aus" ist unverändert, das Formular nicht angefasst. Die Beschriftung nennt die Mitbestimmungsrelevanz und sagt ausdrücklich, dass sie ein Hinweis und keine Rechtsauskunft ist.
- **T-19-SC** (Supply Chain, niedrig): `git diff --stat 4baacbd HEAD -- appinfo/info.xml pyproject.toml uv.lock` ist leer.

Ein Hinweis für Plan 19-05 und Plan 19-09: der Wortlaut oben ist ab jetzt die Referenz für
`docs/privacy.md` und `docs/uninstall.md`. Wenn dort ein anderer Satz über die drei Löschwege
oder über den Fortbestand nach dem Purge steht, sagen zwei öffentliche Orte verschieden viel
über dieselbe Sache, und das ist genau der Fehler, den T-19-06 für den Grenzsatz schließt.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 19-05 (`docs/privacy.md`, `docs/uninstall.md`) kann den Wortlaut oben zitieren, ohne `strings.py` zu lesen; die drei automatischen Löschwege stehen darin in derselben Reihenfolge, in der die Doku sie nennen soll.
- Plan 19-09 findet AUDIT-05 abgehakt und die Zusagen als Tests vor; zu prüfen bleibt dort die Anforderung als Ganzes, nicht ihre Formulierung.
- Plan 19-03 (Wörter-Gate) kann `FORBIDDEN_CLAIMS` aus `tests/unit/test_exapp_admin_settings.py` als Vorlage nehmen: die vier Muster in drei Sprachen sind dort schon geschrieben und gegen die heutige Textfläche gemessen. Ob das Gate die Liste dorthin verschiebt oder eine zweite hält, ist die Entscheidung dieses Plans; zwei Listen wären ein zweiter Wortlaut derselben Regel.
- Nicht gemessen, sondern hergeleitet (ausdrücklich so gekennzeichnet): eine bestehende Installation sieht die neue Beschriftung erst nach einem Deaktivieren-Aktivieren-Zyklus, weil `register_admin_form` im `enabled=1`-Zweig läuft. Es steht keine Test-Nextcloud zur Verfügung, und der Text sagt diesen Zyklus selbst.

## Verification

- `uv run pytest tests/unit/test_exapp_admin_settings.py -q`: 45 Fälle grün (vorher 41, also vier mehr: zwei neue Tests und zwei neue Parametrisierungsfälle).
- `uv run pytest tests/unit tests/contract`: Exitcode 0, 3015 gesammelte Fälle (`--collect-only -q` gezählt; 19-01 stand auf 3011).
- `uv run ruff check .`: All checks passed. `uv run ruff format --check .`: 218 files already formatted.
- `uv run pyright`: 0 errors, 0 warnings, 0 informations.
- `uv run vulture src scripts vulture_whitelist.py`: still.
- `uv run python scripts/check_tool_budget.py`: `tools/list: 15712 bytes, 21 tools, budget 18000`, unverändert.
- `git diff --stat 4baacbd HEAD -- appinfo/info.xml pyproject.toml uv.lock`: leer.
- `grep -c` in `src/mcp_connector/exapp/ui/strings.py`: "works council" 1, "changed or removed unnoticed" 2, "recompute" 2, "180 days" 1, "100 MB" 1; `grep -ci "full"` 0.
- `grep -c "LIMIT_SENTENCE" tests/unit/test_exapp_admin_settings.py`: 2.
- **Gegenprobe 1 (vom Plan gefordert):** "come under the codetermination of a works council in Germany and in Austria" durch "be a matter for the organisation in Germany and in Austria" ersetzt. `test_the_audit_log_description_says_what_is_kept_and_what_is_not` wurde rot (`AssertionError: assert 'works council' in '...'`). Zurückgenommen, `git diff` für die Datei danach leer.
- **Gegenprobe 2 (zusätzlich):** ein Satz mit dem Stufenwort in die Beschreibung eingefügt. `test_no_field_of_the_form_offers_a_level_of_recording` wurde rot und nannte das Feld `audit_log`. Zurückgenommen.

## Self-Check: PASSED

Beide geänderten Dateien liegen auf der Platte, beide Commits stehen im Log (`9765014`,
`3faa425`), und `ADMIN_FIELD_AUDIT_LOG_DESCRIPTION` liest sich aus dem installierten Modul
mit dem oben zitierten Wortlaut (1280 Zeichen).

---
*Phase: 19-audit-log-bedienung-und-textnachzug*
*Completed: 2026-08-31*
