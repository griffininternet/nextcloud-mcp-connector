---
phase: 19-audit-log-bedienung-und-textnachzug
plan: 05
subsystem: docs
tags: [audit-log, privacy, uninstall, faq, audit-06, d-v1.5-01, r-18-04, doc-truth]

# Dependency graph
requires:
  - phase: 18
    plan: 01
    provides: "audit/store.py mit AUDIT_FILENAME, RETENTION_DAYS, SIZE_LIMIT_BYTES, USER_SILENCE_DAYS und dem kommentierten Schema der 17 Felder"
  - phase: 18
    plan: 09
    provides: "T-18-22, vier Fälle in tests/unit/test_exapp_purge.py: der Purge leert die sieben Tabellen des OAuth-Speichers und das Audit-Log übersteht ihn"
  - phase: 19
    plan: 02
    provides: "Der volle Wortlaut der Formularbeschriftung als Zitatquelle: 180 Tage Vorgabe, 100 MB, Kontolöschung, kein Weg als der einzige"
  - phase: 19
    plan: 03
    provides: "FORBIDDEN_CLAIMS und das Vokabular-Gate über docs/**/*.md rekursiv, gegen die die neuen Sätze geschrieben sind"
provides:
  - "docs/privacy.md: zwei benannte SQLite-Dateien, acht Tabellenzeilen über audit.sqlite3 samt der Zeile, was nie darin steht, ein Purge-Absatz über den Fortbestand und ein Retention-Abschnitt mit allen drei automatischen Löschwegen"
  - "docs/uninstall.md: Titel, Scope, Abschnittstitel, Versionstabelle, tables_cleared-Zeile, ein fünfter Pruefschritt für audit.sqlite3 und die --rm-data-Grenze im Nutzertext (schliesst R-18-04)"
  - "docs/faq.md: die completely-Antwort nennt beide Kommandos, den überlebenden Purge und die Ausnahme"
  - "tests/unit/test_docs_audit_truth.py: zwölf Fälle, die drei Dokumente an vier Codekonstanten binden"
affects: [19-08, 19-09]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Eine Zahl in einem öffentlichen Text wird im Test aus der Konstante formatiert und nie als Literal wiederholt"
    - "Ein Textabschnitt wird als Abschnitt geprüft (split auf die Überschrift), nicht als Vorkommen irgendwo in der Datei: drei Zahlen in einer Datei können drei zusammenhanglose Sätze sein"
    - "Eine Doku-Aussage, die eine bewusste Ausnahme von einer Löschung erklärt, nennt die Begründung im Text und den Pruefschritt daneben, damit der Fortbestand eine Zahl ist und kein Versprechen"
    - "Ein Messprotokoll bekommt keine erfundene Messung nachgetragen: ein später hinzugefügter Check sagt ausdrücklich, dass er die auszuführende Form ist und keine Messung vom Messdatum"

key-files:
  created:
    - tests/unit/test_docs_audit_truth.py
  modified:
    - docs/privacy.md
    - docs/uninstall.md
    - docs/faq.md

key-decisions:
  - "Die verengte Formulierung aus D-v1.5-01 (die Frist sei der einzige automatische Löscher) ist bewusst NICHT übernommen: der Code kennt drei Wege, und wie viele es sind, ist eine Messung und keine Entscheidung"
  - "docs/faq.md ist eine Ergänzung über CONTEXT hinaus (Assumption A5): der Eintrag trägt das Wort completely und trug denselben falschen Satz über den Purge"
  - "Der neue Pruefschritt zeigt zwei richtige Antworten (eine Zeilenzahl oder eine fehlende Datei) statt einer erfundenen Messzahl, weil die Seite ein Messprotokoll vom 2026-08-19 ist und das Log damals nicht existierte"
  - "audit.sqlite3 steht in der bestehenden Speichertabelle von docs/privacy.md und nicht in einer zweiten Tabelle: die Zeile | Client registrations bleibt damit wörtlich unberührt (Pitfall 18)"
  - "Die drei Löschwege stehen als numerierte Liste mit fetten Kurznamen, weil ein Absatz mit drei Zahlen als eine Regel mit Ausnahmen gelesen wird und nicht als drei Regeln"
  - "Der Name im Nutzertext ist 'the audit log', mit 'the record of tool calls' als Erklärung daneben: das Wort ist vom Anspruchsgate ausdrücklich erlaubt und das Formular nennt den Schalter so"

patterns-established:
  - "Zwölf Behauptungen als zwölf Testfunktionen: eine rote Zeile sagt, welcher Satz welcher Datei gebrochen ist"
  - "Die Negativliste der verschwundenen Wendungen wird zusätzlich als Schleife mit einer Längenbehauptung geprüft, damit eine geleerte Liste nicht vakuum-grün besteht (Lehre aus 19-03)"

requirements-completed: []
# AUDIT-06 bleibt Pending: die Texte sind die zweite von drei Hälften. Der Enterprise-Absatz
# in drei Sprachen ist 19-08, die Zusammenführung im [Unreleased]-Block ist 19-09.
requirements-advanced: [AUDIT-06]

# Metrics
duration: 19min
completed: 2026-08-31
---

# Phase 19 Plan 05: Die Nutzerdokumentation sagt die Wahrheit Summary

**`docs/privacy.md` nennt zwei SQLite-Dateien statt einer, beschreibt `audit.sqlite3` in acht Zeilen der bestehenden Speichertabelle samt der Zeile, was nie darin steht, sagt dass der Purge nur die sieben Tabellen des OAuth-Speichers leert und dass das Audit-Log ihn absichtlich übersteht, und nennt im Retention-Abschnitt alle drei automatischen Löschwege mit ihren Zahlen (180 Tage Vorgabe, 100 MB Obergrenze, Konto seit 30 Tagen stumm und in Nextcloud gelöscht) samt der Markierung, die jede Lücke erklärt; `docs/uninstall.md` nennt das Log jetzt in zwölf Zeilen statt in keiner, hat einen fünften Pruefschritt, der die Zeilenzahl aus dem Volume liest, und sagt im Nutzertext, dass `--rm-data` die benannte Ausnahme ist; und zwölf Testfälle halten die neuen Sätze gegen `RETENTION_DAYS`, `SIZE_LIMIT_BYTES`, `USER_SILENCE_DAYS` und `AUDIT_FILENAME`.**

## Performance

- **Duration:** 19 min
- **Started:** 2026-08-31T14:56:00Z
- **Completed:** 2026-08-31T15:15:00Z
- **Tasks:** 3
- **Files modified:** 3, davon 1 neu

## Accomplishments

### docs/privacy.md (Task 1)

- Die Einleitung von "What the app stores" sagt **zwei** Datenbanken, benannt als `oauth.sqlite3` und `audit.sqlite3`, und sagt, dass die zweite Datei nur existiert, wenn ein Administrator das Protokoll eingeschaltet hat oder es einmal eingeschaltet war.
- Acht neue Zeilen in der bestehenden Tabelle `| Data | Where | Form |`: Kontoname, Werkzeugname, Zeit, die drei Clientspalten samt Verbindung, Ergebnisstatus mit dem Ablehnungsgrund als feste Kennung, Dauer, Parameternamen als sortierte JSON-Liste, und als achte Zeile ausdrücklich, was **nicht** darin steht (keine IP, kein User-Agent, kein Parameterwert, kein Teil eines Ergebnisses, kein Text einer Fehlermeldung). Alle Zeilen stehen **hinter** der bestehenden Tabelle, die Zeile `| Client registrations` ist unberührt (`git diff` zeigt sie nicht).
- Der Purge-Satz heisst jetzt "empties the seven tables of its OAuth database". Ein neuer, fetter Absatz **The audit log survives the purge** sagt den Fortbestand, die Begründung ("a record that one command removes records nothing, because that command is the first thing anybody reaches for who wants an entry gone"), dass die Datei danach weiter im Volume liegt, und dass `uninstall.md` die Zeilenzahl daraus liest, "so what stays is a number an administrator can see rather than a sentence on this page". Die Wendung "how to verify that nothing is left" ist ersetzt durch "how to check what is gone afterwards, and how to see what stays".
- Der Retention-Abschnitt trägt die drei Löschwege als numerierte Liste in der Rangfolge des Plans, mit `NC_MCP_AUDIT_RETENTION_DAYS` als dem Grund, warum 180 Tage eine Vorgabe und keine Zusage sind. Danach der Satz über die Markierung: in allen drei Fällen bleibt sie stehen und nennt die Zahl der fehlenden Zeilen, weshalb eine spätere Prüfung eine erklärte Lücke meldet und keinen Bruch. Zusätzlich ein Satz aus D-v1.5-01, den CONTEXT ausdrücklich nennt: Pausieren und Trennen löschen nichts aus dem Protokoll.

### docs/uninstall.md und docs/faq.md (Task 2)

- Titel: "Removing this app, and proving what is gone and what stays". Die Scope-Zeile sagt dasselbe und nennt den Fortbestand ("the audit log outlives the purge and goes only with the data volume").
- Abschnittstitel: "What the occ way leaves behind: the audit log, and nothing else" (vorher "... : nothing").
- Ein fünfter Pruefschritt in der Form von Check 2 (Wegwerf-Container, `-v nc_app_mcp_connector_data:/d:ro alpine:3`, Kopie nach `/tmp`, `sqlite3 ... "select count(*) from entries"`). Darunter zwei Aufzählungspunkte: eine Zahl ungleich null ist die erwartete Antwort, wenn das Protokoll an war, samt der Aufzählung, wann diese Zeilen doch gehen (Frist, Obergrenze, Kontolöschung, Schritt 2); eine fehlende Datei ist die erwartete Antwort, wenn es nie an war.
- Die Zeile zu `tables_cleared` nennt die sieben Tabellen von `oauth.sqlite3` und sagt, dass `audit.sqlite3` keine davon ist und mit allen Zeilen daneben liegen bleibt.
- Nach den Gegenpruefungen zu `--rm-data` steht die benannte Ausnahme im Nutzertext: das Log geht mit dem Volume, das ist der eine Löschweg dieser App, der `audit.sqlite3` ganz nimmt, und dieselbe Wirkung hat die Checkbox "Delete data on remove" auf Nextcloud 32 und 33. Dazu der Hinweis, dass eine Instanz, die das Protokoll über die Deinstallation hinaus braucht, die Datei vorher aus dem Volume kopiert.
- Die Versionstabelle nennt bei NC 32/33 denselben Sachverhalt, und die "all three"-Zeile sagt jetzt "the seven tables of `oauth.sqlite3` emptied ... then the volume with `audit.sqlite3` in it".
- `docs/faq.md`: die completely-Antwort behält ihre Form (zwei Kommandos in dieser Reihenfolge, Verweis auf `uninstall.md` am Ende) und trägt einen zweiten Absatz über den überlebenden Purge und die `--rm-data`-Ausnahme. Der falsche Satz "empties every table of its database" stand auch hier und ist mitkorrigiert.

### tests/unit/test_docs_audit_truth.py (Task 3)

- Zwölf Testfunktionen, keine Schleife über Behauptungen: drei Zahlen je einzeln gegen ihre Konstante, eine vierte Behauptung, dass alle drei Zahlen **im Retention-Abschnitt** stehen (per `split("## Retention")`, weil drei Zahlen irgendwo in einer Datei drei zusammenhanglose Sätze sein können), `AUDIT_FILENAME` mindestens zweimal in `privacy.md` und zweimal in `uninstall.md`, mindestens sechs Zeilen mit dem Wort audit in `uninstall.md` (der gemessene Ausgangszustand von R-18-04 war null), die faq-Antwort mit Dateiname und `--rm-data`, und vier verschwundene Wendungen als Negativfall über alle drei Dateien.
- Jede Zahl kommt aus dem Import: `f"{store.RETENTION_DAYS} days"`, `f"{store.SIZE_LIMIT_BYTES // 1_000_000} MB"`, `f"{store.USER_SILENCE_DAYS} days"`. `grep -n "180\|100_000_000\|\b30\b"` über die Datei findet nichts, auch nicht im Kommentar.
- Die Meldungsform der Negativfälle ist die des Vokabular-Gates: `f"{name}:{number}: {line.strip()}"`, Datei und Zeilennummer zuerst.
- Der letzte Fall prüft dieselben vier Wendungen als Schleife über `GONE` und nennt `len(GONE) == 4` als erste Behauptung. Das ist die Lehre aus Abweichung 1 von Plan 19-03: eine Schleife über eine geleerte Liste besteht sonst kommentarlos.
- Der Modul-Docstring begründet, warum die Datei zu keinem Modul gehört, nennt `tests/unit/test_oauth_store.py:1490-1509` als Herkunft des Musters und hat einen Abschnitt "What this does not do": kein zweites Vokabular- oder Anspruchsgate.

## Task Commits

1. **Task 1: docs/privacy.md** - `b2c8ee4` (docs)
2. **Task 2: docs/uninstall.md und docs/faq.md** - `a350f12` (docs)
3. **Task 3: die Bindung an die Konstanten** - `753102a` (test)

## Files Created/Modified

- `docs/privacy.md` - 52 Zeilen mehr, 9 weniger: Einleitung, acht Tabellenzeilen, Purge-Satz und -Absatz, Retention-Abschnitt.
- `docs/uninstall.md` - 41 Zeilen mehr, 7 weniger: Titel, Scope, zwei Tabellenzeilen, eine Tabellenzelle, Abschnittstitel, Pruefschritt 5 samt Erklärung, ein Absatz nach den `--rm-data`-Gegenpruefungen, ein Wort in der Messbeschreibung ("of the app's OAuth database").
- `docs/faq.md` - ein korrigierter Satz und ein neuer Absatz in der completely-Antwort.
- `tests/unit/test_docs_audit_truth.py` - NEU, 184 Zeilen, zwölf Fälle, vier Konstanten.

## Decisions Made

- **Die verengte Formulierung aus D-v1.5-01 ist nicht übernommen.** Der Text sagt nirgends, die Aufbewahrungsfrist sei der einzige automatische Löscher, und ein eigener Testfall (`test_no_page_makes_one_deletion_path_the_only_one`) hält die Wendung "the only automatic" aus allen drei Dateien heraus. Begründung ausdrücklich für den Verifizierer: der Code kennt drei automatische Löschwege (`store.py:97` `RETENTION_DAYS`, `:102` `SIZE_LIMIT_BYTES` mit `:667-702`, `:128` `USER_SILENCE_DAYS` mit `:912-989`), und wie viele es sind, ist eine Messung und keine Entscheidung. Die Entscheidung D-v1.5-01 selbst (das Log überlebt Purge und Deinstallation, der Text wird ausdrücklich umgeschrieben statt stillschweigend falsch) ist unberührt und in allen drei Dateien eingelöst.
- **`docs/faq.md` ist eine Ergänzung über CONTEXT hinaus.** CONTEXT nennt nur `docs/privacy.md` und `docs/uninstall.md`; die Recherche empfiehlt den faq-Eintrag (Assumption A5), und der Plan übernimmt die Empfehlung. Die Messung gibt ihr recht: der Eintrag trug wörtlich denselben falschen Satz ("empties every table of its database") und heisst "How do I remove the app and its data **completely**?". Ohne ihn wäre die kürzeste öffentliche Antwort auf die Frage nach vollständiger Löschung die einzige falsch gebliebene.
- **Zwei richtige Antworten statt einer erfundenen Zahl.** `docs/uninstall.md` ist ein Messprotokoll mit Datum (2026-08-19, Nextcloud 34.0.2), und das Audit-Log existierte an diesem Tag in dieser App nicht. Der neue Check sagt das ausdrücklich ("unlike the four above it is not a measurement from 2026-08-19") und zeigt beide richtigen Ausgaben, eine Zeilenzahl als Beispiel und die Fehlermeldung von `cp` bei fehlender Datei. Eine nachgetragene Messzahl wäre die Art von Aussage, gegen die diese ganze Phase gerichtet ist.
- **Der Name im Nutzertext ist "the audit log".** Das Formular heisst "Keep a record of tool calls", also steht die Erklärung "the record of tool calls" daneben. Das Anspruchsgate erlaubt das Wort ausdrücklich (19-03-SUMMARY.md), und ein Text, der die Sache nicht benennt, wäre in `grep -ri audit docs/uninstall.md` genau der Ausgangszustand von R-18-04 geblieben.
- **Die neuen Zeilen stehen hinter der bestehenden Speichertabelle.** Die harte Randbedingung des Plans (Pitfall 18, `tests/unit/test_oauth_store.py:1501-1505`) ist damit ohne Sonderbehandlung erfüllt: kein Zeichen der Zeile `| Client registrations` ist angefasst, und `test_the_privacy_doc_describes_the_clients_table_as_it_is` lief bei jedem Lauf grün.
- **Die Zeilenenden sind pro Datei erhalten geblieben.** `docs/privacy.md` und `docs/faq.md` tragen im Arbeitsbaum CRLF, `docs/uninstall.md` LF (gemessen vor der ersten Änderung). Beide Änderungsläufe liefen über ein Python-Skript, das binär liest, die Zeilenendung aus der Datei nimmt und dieselbe zurückschreibt, damit kein Massen-Diff entsteht. `git diff --numstat` bestätigt: 52/9, 41/7, 9/4 Zeilen.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `docs/faq.md` trug denselben falschen Purge-Satz wie `docs/privacy.md`**

- **Found during:** Task 2
- **Issue:** Der Plan verlangt für `docs/faq.md` nur den Zusatz über den überlebenden Purge und `--rm-data`. Beim Lesen trug der Eintrag zusätzlich wörtlich "empties every table of its database", also genau die Aussage, die Task 1 in `docs/privacy.md` korrigiert. `<behavior>` von Task 3 verlangt ausserdem, dass **keine** der drei Dateien diese Wendung enthält; ohne die Korrektur wäre `test_no_page_still_says_the_purge_empties_every_table` rot gewesen.
- **Fix:** Der Satz heisst jetzt "empties the seven tables of its OAuth database", wortgleich zur neuen Fassung in `docs/privacy.md`.
- **Files modified:** docs/faq.md
- **Committed in:** `a350f12`

**2. [Rule 1 - Bug] Die Scope-Zeile und zwei Zellen der Versionstabelle von `docs/uninstall.md` behaupteten weiter, nichts bleibe übrig**

- **Found during:** Task 2
- **Issue:** Der Plan nennt sechs Stellen. Die Scope-Zeile (`:5-6`, "so that no credential it created stays valid and **no data it stored stays behind**") und die "all three"-Zeile der Versionstabelle ("every table emptied ... then the volume") tragen dieselbe Bestandsaussage wie der Titel, den Stelle 1 umschreibt. Ein umgeschriebener Titel über einer unveränderten Scope-Zeile hätte die Seite in sich widersprüchlich gemacht.
- **Fix:** Beide sagen jetzt, was bleibt und wodurch es geht. Die Zeile `:88` ("the row counts of all seven tables of the app's database") heisst zusätzlich "OAuth database", weil die Messung von 2026-08-19 nur diese Datei gelesen hat.
- **Files modified:** docs/uninstall.md
- **Committed in:** `a350f12`

**3. [Rule 1 - Bug] Eine interne Anforderungs-Kennung im Nutzertext**

- **Found during:** Task 2, unmittelbar nach dem ersten Schreiblauf
- **Issue:** Die neue Scope-Zeile trug "the audit log of AUDIT-01". Anforderungs-Kennungen leben in `.planning/` und sagen einem Administrator nichts.
- **Fix:** Ersetzt durch "the audit log outlives the purge and goes only with the data volume". Noch vor dem Commit von Task 2 korrigiert.
- **Files modified:** docs/uninstall.md
- **Committed in:** `a350f12`

### Zur Rotphase von Task 3

Task 3 trägt `tdd="true"`, aber seine Prüfsubjekte sind die Dokumente aus Task 1 und Task 2 und
damit vor dem Test fertig. Eine echte Rotphase durch "der Test läuft gegen fehlenden Code" gibt
es hier nicht, und ein künstliches Zurückbauen der eben committeten Texte wäre eine Messung ohne
Aussage gewesen. Die Rotphase, die der Plan selbst als Akzeptanzkriterium nennt, ist die
Gegenprobe an der Konstante, und sie ist gelaufen (siehe "Verification"): `RETENTION_DAYS = 90`
von Hand gesetzt macht zwei der zwölf Fälle rot, danach zurückgenommen. Der Commit trägt
deshalb den Typ `test` und nicht `feat`.

### Zum Umfang der Zahlen im Text

Task 1 verlangt "180 Tage als Vorgabe (nicht als Immer)". Umgesetzt mit der Begründung im Satz:
`NC_MCP_AUDIT_RETENTION_DAYS` kann sie verschieben, "und die Zahl, die gilt, ist die, mit der
diese Instanz ausgerollt wurde". Der Test bindet trotzdem die Codekonstante, weil die Vorgabe
der Code ist und die Umgebungsvariable eine Abweichung davon.

---

**Total deviations:** 3 auto-fixed (Rule 1), alle in derselben Datei-Familie und im Sinne des Plan-Ziels (Wahrheit statt Wortlaut)
**Impact on plan:** Kein erweiterter Auftrag. Abweichung 1 ist Voraussetzung dafür, dass Task 3 grün ist; Abweichung 2 verhindert eine Seite, die sich in Titel und Scope widerspricht.

## Issues Encountered

- Der Arbeitsbaum trägt gemischte Zeilenenden: `docs/privacy.md` und `docs/faq.md` CRLF, `docs/uninstall.md` LF. Git meldet beim Commit von `docs/uninstall.md` und der neuen Testdatei "LF will be replaced by CRLF the next time Git touches it"; das ist der bestehende Zustand des Repos (`core.autocrlf=true`) und kein Ergebnis dieses Plans. Gemessen wurde vor jeder Änderung mit `python -c "open(p,'rb').read().count(b'\r\n')"`, geschrieben wurde binär mit demselben Zeilenende.
- `grep -c $'\r' docs/privacy.md` antwortet in dieser Git-Bash mit `0`, obwohl die Datei CRLF trägt. Für Zeilenenden ist in diesem Repo nur die binäre Messung mit Python belastbar.

## Anforderungen

**AUDIT-06 bleibt in `REQUIREMENTS.md` Pending und ist nicht abgehakt.** Die Anforderung hat
drei Teile: das Wörter-Gate (19-03, steht), die neuen Sätze in `docs/privacy.md` und
`docs/uninstall.md` (dieser Plan, steht) und der Enterprise-Absatz in drei Sprachen (19-08,
offen), zusammengeführt im `[Unreleased]`-Block von 19-09. Ein Haken hier wäre dieselbe Art von
Aussage, gegen die diese Phase antritt.

AUDIT-04 unverändert Pending (19-06 und 19-07 offen), AUDIT-05 seit 19-02 Complete.

## Threat Flags

Keine neue Fläche: keine Route, kein Netzzugang, keine Berechtigung, kein Paket, kein
Manifesteintrag, keine Versionszeichenkette, keine Produktionsdatei unter `src/`. Die fünf
Fäden des Bedrohungsmodells dieses Plans:

- **T-19-15** (Repudiation, hoch): Alle drei automatischen Löschwege stehen mit ihren Zahlen im Retention-Abschnitt von `docs/privacy.md`, jede Zahl per Test an ihre Konstante gebunden, und die Wendung "the only automatic" ist über alle drei Dateien als Negativfall verboten. Mitigiert.
- **T-19-16** (Repudiation, hoch): `docs/uninstall.md` nennt das Log in zwölf Zeilen (Ausgangszustand null), hat einen eigenen Pruefschritt für `audit.sqlite3` und eine präzisierte `tables_cleared`-Zeile. Restpunkt R-18-04 geschlossen, gehalten von `test_the_runbook_mentions_the_audit_log_at_all`.
- **T-19-17** (Information Disclosure, mittel): Die Speichertabelle nennt die Felder, die es gibt, und in einer eigenen Zeile die, die es nicht gibt (IP, User-Agent, Parameterwert, Ergebnisinhalt, Fehlermeldungstext). Kein Beispiel eines echten Parameterwerts steht im Text; die Beispielwerte des Textes sind Spaltennamen und die drei Ergebnisklassen `ok`, `rejected`, `failed`. Mitigiert.
- **T-19-18** (Repudiation, mittel): Die completely-Antwort in `docs/faq.md` nennt beide Kommandos, den überlebenden Purge und die Ausnahme; als Ergänzung über CONTEXT hinaus (Assumption A5) oben ausgewiesen. Mitigiert.
- **T-19-19** (Repudiation, niedrig) und **T-19-SC** (Supply Chain, niedrig): Das Anspruchsgate und das Vokabular-Gate aus 19-03 laufen über `docs/**/*.md` rekursiv und sind über alle neuen Sätze grün; `git diff --stat 4baacbd HEAD -- pyproject.toml uv.lock` ist leer.

Eine neue Fläche im weiteren Sinn ist der Pruefschritt selbst: er nennt einen
`docker run`-Aufruf mit dem Volume **read only** gemountet und einer Kopie nach `/tmp`, in
genau der Form von Check 2. Er liest eine Zeilenzahl und keine Zeile, also gibt die Anleitung
keinen Kontonamen und keinen Werkzeugnamen aus.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- 19-08 (Enterprise-Absatz in drei Sprachen) kann den Satz "heute in keiner Form vorhanden" ersetzen und dabei auf `docs/privacy.md` verweisen, das die Speicherung jetzt vollständig beschreibt.
- 19-09 findet für den `[Unreleased]`-Block drei Punkte in diesem Plan: die zwei Datenbanken in der Datenschutzbeschreibung, den Fortbestand über Purge und Deinstallation samt der `--rm-data`-Ausnahme, und den neuen Pruefschritt im Deinstallations-Runbook.
- Für 19-06 (Lesekommando) ist eine Zusage dieses Plans zu halten: `docs/privacy.md` sagt, dass eine Zeile keinen Parameterwert, keinen Ergebnisinhalt und keinen Fehlermeldungstext trägt. Das gilt für die Ablage; die Ausgabe des Lesekommandos darf nichts hinzufügen, was diese Zusage bricht.
- `tests/unit/test_docs_audit_truth.py` ist die Stelle, an der die nächste Textänderung an einer dieser drei Seiten rot wird, wenn sie eine Zahl fallen lässt. Wer eine der drei Konstanten ändert, ändert zwei Dateien.

## Verification

- `uv run pytest tests/unit/test_docs_audit_truth.py -q`: grün, 12 Fälle (`--collect-only`: `tests/unit/test_docs_audit_truth.py: 12`).
- `uv run pytest tests/unit/test_oauth_store.py tests/unit/test_exapp_env_setup.py -q`: grün (Verify von Task 1, einschliesslich `test_the_privacy_doc_describes_the_clients_table_as_it_is`).
- `uv run pytest tests/unit/test_exapp_env_setup.py -k "vocabulary or forbidden_claim" -q`: 6 Fälle grün, nach Task 1 und nach Task 2 je einmal gelaufen.
- `uv run pytest tests/unit tests/contract -q`: Exitcode 0, 3052 gesammelte Fälle (19-04 stand auf 3040, also genau die zwölf neuen).
- `uv run ruff check .`: All checks passed. `uv run ruff format --check .`: 219 files already formatted.
- `uv run pyright`: 0 errors, 0 warnings, 0 informations.
- `uv run vulture src scripts vulture_whitelist.py`: still, Exitcode 0.
- **Gegenprobe von Hand (Akzeptanzkriterium von Task 3):** `RETENTION_DAYS` binär auf `90` gesetzt, dann `uv run pytest tests/unit/test_docs_audit_truth.py -q`. Zwei Fälle rot: `test_the_privacy_page_names_the_retention_window_of_the_code` und `test_the_privacy_page_names_all_three_deletion_paths_together` ("AssertionError: the Retention section has to name '90 days'"). Zurückgenommen, `git status --short` danach nur mit der noch nicht committeten Testdatei, `git diff --name-only 05b0548 HEAD` nennt keine Datei unter `src/`.
- Kriterien von Task 1, gemessen: `audit.sqlite3` 11 Treffer (gefordert 2), `180` 1, `100 MB` 1, `30 days` 1, `empties every table` 0, `There is no long lived store of personal data` 0, Zeilen mit `^| Client registrations` genau 1 (mit "hash" und "never in the clear"), `the only automatic` 0 (case-insensitive), `archiv` 0 (case-insensitive).
- Kriterien von Task 2, gemessen: Zeilen mit "audit" in `docs/uninstall.md` 12 (gefordert 6), `audit.sqlite3` 7 Treffer (gefordert 2), `leaves behind: nothing` 0, `rm-data` 9 Treffer (gefordert 3) und im Abschnitt der Gegenpruefungen nach `--rm-data` steht "audit", Zeilen mit "audit" in `docs/faq.md` 2 (gefordert 1), `archiv` in beiden Dateien 0.
- Kriterien von Task 3, gemessen: 12 Fälle (gefordert 8), `grep -c "RETENTION_DAYS\|SIZE_LIMIT_BYTES\|USER_SILENCE_DAYS\|AUDIT_FILENAME"` in der Testdatei 15 (gefordert 4), `grep -n "180\|100_000_000\|\b30\b"` über die ganze Datei ohne Treffer (auch nicht im Kommentar).
- Verifikationsschritt 3 des Plans: `git diff --stat 4baacbd HEAD -- appinfo/info.xml README.md README.de.md README.fr.md CHANGELOG.md pyproject.toml uv.lock` ist leer.
- Verifikationsschritt 4: `git tag --points-at HEAD` leer, `grep -c "0.1.12" appinfo/info.xml pyproject.toml` je 0.
- `git diff --name-only 05b0548 HEAD`: `docs/faq.md`, `docs/privacy.md`, `docs/uninstall.md`, `tests/unit/test_docs_audit_truth.py`, sonst nichts.

## Self-Check: PASSED

Die drei geänderten Dokumente und die neue Testdatei liegen auf der Platte
(`tests/unit/test_docs_audit_truth.py`, 184 Zeilen), alle drei Task-Commits stehen im Log
(`b2c8ee4`, `a350f12`, `753102a`), und `git status --short` war vor dem Schreiben dieses
Summary leer.

---
*Phase: 19-audit-log-bedienung-und-textnachzug*
*Completed: 2026-08-31*
