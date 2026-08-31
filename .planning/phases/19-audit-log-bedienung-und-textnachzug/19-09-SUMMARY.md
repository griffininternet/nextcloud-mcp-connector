---
phase: 19-audit-log-bedienung-und-textnachzug
plan: 09
subsystem: docs
tags: [changelog, unreleased, keep-a-changelog, gate-lauf, lieferverbote, nachweistabelle, audit-06, t-19-36]

# Dependency graph
requires:
  - phase: 19
    plan: 06
    provides: "Kommandoname, die vier Optionen, der Deckel 200 und der Höchstwert 5000, die der Added-Punkt nennt"
  - phase: 19
    plan: 07
    provides: "Die Registrierung, die drei deklarierten Umgebungsvariablen und der Deaktivieren-Aktivieren-Zyklus"
  - phase: 19
    plan: 08
    provides: "Der Wortlaut der sechs Enterprise-Absätze, aus dem der Changed-Punkt geschrieben ist"
  - phase: 19
    plan: 05
    provides: "Die drei automatischen Löschwege und der fünfte Pruefschritt in docs/uninstall.md"
  - phase: 19
    plan: 02
    provides: "Der volle Wortlaut der Formularbeschriftung als Zitatquelle des Changed-Punkts"
  - phase: 19
    plan: 01
    provides: "Die eine Reinigungsregel und die geschlossene content-length-Falle, die der Fixed-Abschnitt beschreibt"
provides:
  - "CHANGELOG.md: ein neuer [Unreleased]-Block mit Added, Changed und Fixed über dem Eintrag zu 0.1.11"
  - "Die Linkdefinition [Unreleased] auf compare/v0.1.11...HEAD als erste Zeile des Definitionsblocks"
  - "Die Nachweistabelle je Erfolgskriterium der Phase mit ehrlichem Urteil"
  - "Die Owner-Schrittliste für den echten occ-Lauf, ausführbar ohne diesen Plan zu lesen"
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ein Release-Eintrag ist ein Datum: neue Aussagen kommen in einen neuen Block darüber, nie in einen veröffentlichten hinein"
    - "Ein Urteil in einer Nachweistabelle ist gemessen oder hergeleitet, und was ohne laufende Instanz nicht messbar ist, wird hergeleitet genannt statt geprüft weitergeschrieben (R-18-05)"

key-files:
  created:
    - .planning/phases/19-audit-log-bedienung-und-textnachzug/19-09-SUMMARY.md
  modified:
    - CHANGELOG.md

key-decisions:
  - "Der Block ist neu angelegt und nicht befüllt: Phase 16 hat den alten Block in den Eintrag zu 0.1.11 überführt, die Datei begann nach dem Kopf direkt mit 0.1.11 (Pitfall 13)"
  - "Der Deaktivieren-Aktivieren-Zyklus steht als eigener Changed-Punkt und nicht als Nebensatz: er ist die einzige Aussage des Blocks, die ein Administrator ausführen muss, damit die anderen wahr werden"
  - "Der Fixed-Punkt benennt U+202E und setzt das Zeichen nicht ein (T-19-39)"
  - "Zwei Zeilen der Nachweistabelle tragen das Urteil hergeleitet, obwohl ihr Kern am Baum gemessen ist: was ein Administrator in einer laufenden Instanz sieht, ist auf diesem Rechner nicht messbar"
  - "Kein Eintrag zu 0.1.10 oder 0.1.11 ist angefasst: der Diff des Plans ist 62 Einfügungen und 0 Löschungen"

patterns-established:
  - "Die Lieferverbote einer Phase werden am Ende mit Kommando und Ausgabe belegt und nicht als Absicht behauptet"

requirements-completed: [AUDIT-06]

# Metrics
duration: 12min
completed: 2026-08-31
---

# Phase 19 Plan 09: Der wartende Textrest im [Unreleased]-Block Summary

**`CHANGELOG.md` trägt über dem Eintrag zu 0.1.11 einen neuen `[Unreleased]`-Block mit drei Added-Punkten (das Lesekommando samt seiner vier Optionen und ohne Route im Manifest, die drei deklarierten Umgebungsvariablen, der fünfte Pruefschritt im Deinstallations-Runbook), vier Changed-Punkten (die neue Formularbeschriftung, die drei korrigierten Doku-Seiten, der Enterprise-Absatz, und der Deaktivieren-Aktivieren-Zyklus, ohne den eine laufende Installation nichts davon sieht) und zwei Fixed-Punkten (die eine Reinigungsregel, das `content-length`, das keinen Serverfehler mehr erzeugt); die sieben Gates laufen grün, die sechs Lieferverbote sind mit Kommando und Ausgabe belegt, und die fünf Erfolgskriterien der Phase haben je eine Nachweiszeile mit ehrlichem Urteil.**

## Performance

- **Duration:** 12 min
- **Started:** 2026-08-31T16:19:00Z
- **Completed:** 2026-08-31T16:31:00Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments

- Der Block ist **neu angelegt**, nicht befüllt: die Datei begann nach dem Kopf in Zeile 12 direkt
  mit `## [0.1.11] - 2026-08-28`, weil Phase 16 den vorigen `[Unreleased]`-Block dorthin überführt
  hat. Jetzt steht `## [Unreleased]` in Zeile 12 und `## [0.1.11]` in Zeile 73.
- Ein einleitender Absatz in Prosa, dann `### Added` (3 Punkte), `### Changed` (4 Punkte),
  `### Fixed` (2 Punkte), in der Form der Einträge darunter: ein Satz, der sagt, was ein Nutzer
  merkt, dann die Begründung, Zeilen um 100 Zeichen, Fortsetzungszeilen mit zwei Leerzeichen.
- Der Einleitungsabsatz sagt ausdrücklich, dass nichts davon ausgeliefert ist und eine
  installierte Instanz nichts davon vor dem nächsten Release sieht, weil der Store das Manifest
  nur beim Upload liest.
- Die Linkdefinition
  `[Unreleased]: https://github.com/street1983nk/nextcloud-mcp-connector/compare/v0.1.11...HEAD`
  steht als erste Zeile des Definitionsblocks am Dateiende, über `[0.1.11]`.
- **Kein Release-Eintrag ist angefasst.** `git diff --numstat HEAD~1 HEAD -- CHANGELOG.md` meldet
  `62 0`: zweiundsechzig Einfügungen, null Löschungen. Der Satz des Eintrags zu 0.1.10, der über
  die drei Enterprise-Dinge "exist in this version in no form" sagt, steht wörtlich unverändert;
  er ist über 0.1.10 wahr und bleibt es.
- Sieben Gates grün, Werkzeugoberfläche byte-gleich (15712 Bytes, 21 Werkzeuge), sechs
  Lieferverbote belegt, fünf Nachweiszeilen, eine Owner-Schrittliste mit neun Kommandos.

## Task Commits

1. **Task 1: Den [Unreleased]-Block neu anlegen** - `d00ec9e` (docs)
2. **Task 2: Gate-Kette, Lieferverbote und Nachweistabelle** - kein eigener Commit: der Task
   ändert nach seiner eigenen Anweisung keinen Dateiinhalt ("Kein weiterer Dateiinhalt, sondern
   Messen und Belegen"). Sein Ergebnis ist dieses SUMMARY und wandert mit dem Abschlusscommit
   in den Baum.

## Files Created/Modified

- `CHANGELOG.md` - ein neuer Block über 0.1.11 und eine Linkdefinition; 62 Einfügungen, 0
  Löschungen. Die Datei trägt LF (binär gemessen: 0 CRLF), geschrieben wurde binär mit demselben
  Zeilenende, damit kein Massen-Diff entsteht.

## Der Gate-Lauf, mit Ausgabe

| # | Kommando | Ausgabe | Urteil |
|---|----------|---------|--------|
| 1 | `uv run ruff check .` | `All checks passed!` | grün |
| 2 | `uv run ruff format --check .` | `221 files already formatted` | grün |
| 3 | `uv run pyright` | `0 errors, 0 warnings, 0 informations` | grün |
| 4 | `uv run vulture src scripts vulture_whitelist.py` | still, Exitcode 0 | grün |
| 5 | `uv run pytest tests/unit tests/contract -q` | Exitcode 0, 3095 gesammelte Fälle (`--collect-only` gezählt, wie 19-08) | grün |
| 6 | `uv run python scripts/check_tool_budget.py` | `tools/list: 15712 bytes, 21 tools, budget 18000` | grün |
| 7 | `uv run pytest -m matrix` | Exitcode 0, 8 Fälle | grün |

Zusätzlich, weil der Block unter zwei Gates fällt, die diese Phase gebaut oder erweitert hat:

- `uv run pytest tests/unit/test_exapp_env_setup.py -q`: 167 Fälle grün.
- `uv run pytest tests/unit/test_exapp_env_setup.py -k "vocabulary or forbidden_claim" -q`: 6
  Fälle grün. Beide Gates lesen `CHANGELOG.md` ausdrücklich mit: die Datei steht namentlich in
  `PUBLIC_MARKDOWN` (`tests/unit/test_exapp_env_setup.py:2009`), das Anspruchs-Gate liest
  dieselbe Liste (`:2223-2240`), und `test_the_vocabulary_gate_reads_a_list_that_is_not_empty`
  (`:2107`) behauptet, dass die Liste sie enthält, damit keine leere Liste grün besteht.

## Die sechs Lieferverbote, mit Kommando und Ausgabe

| # | Verbot | Kommando | Ausgabe |
|---|--------|----------|---------|
| 1 | Kein Tag | `git tag --points-at HEAD` | leer. `git tag --list "v0.1.12"`: leer |
| 2 | Kein Store-Archiv, kein Upload | `git status --short` | leer; kein `.tar.gz` im Baum (`git ls-files \| grep -c "\.tar\.gz$"` ergibt 0), kein Lauf von `scripts/build_store_release.sh` |
| 3 | Keine Versionszeichenkette angefasst | `git diff 4baacbd HEAD -- appinfo/info.xml \| grep "<version>"` | leer; `version` im Manifest ist weiter `0.1.11` (per `lxml` gelesen); `grep -c "0.1.12" CHANGELOG.md` ergibt 0 |
| 4 | Kein `image-tag` geändert | `git diff 4baacbd HEAD -- appinfo/info.xml \| grep "image-tag"` | leer |
| 5 | Keine neue Route | `lxml`-Zählung der `<url>`-Einträge in `appinfo/info.xml` | `13`, unverändert gegenüber dem Stand vor der Phase |
| 6 | Werkzeugoberfläche eingefroren | `uv run python scripts/check_tool_budget.py` | `tools/list: 15712 bytes, 21 tools, budget 18000`, byte-gleich zu 18-10 und zu jedem Plan dieser Phase |

Dazu T-19-SC, das siebte Verbot der Phase, das jeder Plan mitführt:
`git diff --stat 4baacbd HEAD -- pyproject.toml uv.lock` ist leer. Die ganze Phase hat kein Paket
installiert.

## Nachweistabelle je Erfolgskriterium der Phase

Wortlaut der Kriterien aus `.planning/ROADMAP.md:221-225`, gekürzt auf den tragenden Satz.
Erlaubte Urteile: `gemessen` oder `hergeleitet`. Die Präzedenz für das zweite ist R-18-05:
was ohne laufende Test-Nextcloud nicht messbar ist, wird hergeleitet genannt, damit die nächste
Phase es nicht als geprüft weiterschreibt.

| # | Kriterium (ROADMAP.md:221-225) | Belegstelle | Urteil |
|---|--------------------------------|-------------|--------|
| 1 | Ein Administrator liest und exportiert das Log über ein `occ`-Kommando; das Manifest deklariert dafür keine neue Route, und die von aussen erreichbare Angriffsfläche ist unverändert | Gemessen am Baum: `src/mcp_connector/exapp/occ.py:128` (`OCC_AUDIT_READ_COMMAND_NAME = "mcp_connector:audit:read"`), `src/mcp_connector/exapp/audit_read.py:90` (`AUDIT_READ_PATH = "/audit-read"`), `src/mcp_connector/entry_exapp.py:243` (die Route an der Anwendung), `tests/unit/test_exapp_audit_read.py:318,328` (`len(urls) == 13`), 39 Handlerfälle in derselben Datei. Nicht messbar auf diesem Rechner: dass das Kommando nach dem Zyklus in `occ list` erscheint und dass keiner der vier Optionsnamen mit einer globalen Symfony-Option kollidiert (Assumption A2) | hergeleitet |
| 2 | Ab Werk ist das Log aus; ein Administrator schaltet es in den Admin-Einstellungen ein, und die Beschriftung sagt, was das Log leistet, was es nicht leistet, und dass ein nutzerbezogenes Protokoll mitbestimmungsrelevant sein kann | Gemessen am Baum: `src/mcp_connector/exapp/admin_settings.py:178,188` (`audit_log` als Checkbox mit `"default": False`), `src/mcp_connector/exapp/ui/strings.py:663` (`ADMIN_FIELD_AUDIT_LOG_DESCRIPTION`, 1280 Zeichen, voller Wortlaut in `19-02-SUMMARY.md:93-108`), `tests/unit/test_exapp_admin_settings.py` mit 45 Fällen, darunter der Grenzsatz gegen `audit_verify.LIMIT_SENTENCE`. Nicht messbar: dass ein Administrator die neue Beschriftung in einer laufenden Instanz sieht, weil `register_admin_form` im Aktivierungszweig läuft | hergeleitet |
| 3 | Die Admin-Einstellung bietet keine Stufe an, die Parameterwerte oder Ergebnisinhalte protokolliert; `keys` ist der einzige einschaltbare Inhaltsumfang, `full` existiert nirgends in der Oberfläche | `grep -ci "full" src/mcp_connector/exapp/ui/strings.py` ergibt 0, auch in keinem Kommentar; `tests/unit/test_exapp_admin_settings.py:418` (`test_no_field_of_the_form_offers_a_level_of_recording`) läuft als Wortform über alle sieben Formularfelder, über `description`, `title`, `type` und jede Optionsliste; Gegenprobe in 19-02 gefahren und zurückgenommen | gemessen |
| 4 | `docs/privacy.md` und `docs/uninstall.md` sagen im eigenen Text, dass das Log Purge und Deinstallation übersteht; das v1.0-Erfolgskriterium ist umgeschrieben statt stillschweigend falsch | `tests/unit/test_docs_audit_truth.py`, 12 Fälle, binden die drei Seiten an `RETENTION_DAYS`, `SIZE_LIMIT_BYTES`, `USER_SILENCE_DAYS` und `AUDIT_FILENAME`; `docs/uninstall.md` nennt das Log in 12 Zeilen (Ausgangszustand 0, R-18-04 geschlossen) und hat den fünften Pruefschritt; `docs/faq.md` und `docs/privacy.md` sagen "the seven tables of its OAuth database". **Bewusst nicht wörtlich erfüllt:** der Text nennt nicht die Frist als einzigen automatischen Löscher, sondern alle drei Löschwege, weil der Code drei kennt (`store.py:97,102,128`); Begründung in `19-RESEARCH.md`, `19-05-SUMMARY.md` und `ROADMAP.md:256` | gemessen |
| 5 | Der Enterprise-Absatz nennt das Audit-Log in allen drei Sprachen nicht länger als geplant, ein Gate hält die vier Wörter draussen, und alle Textänderungen warten im `[Unreleased]`-Block: kein Tag, kein Store-Upload | `tests/unit/test_exapp_env_setup.py:2518` (Markertripel an allen sechs Stellen) und `:2548` (kein Ort nennt das Log geplant), `:2223` (Anspruchs-Gate über jede öffentliche Seite und den Manifesttext, `FORBIDDEN_CLAIMS` mit vier Mustern in EN/DE/FR), `:2085` (Vokabular-Gate über `CHANGELOG.md` und `docs/**`); der Block steht in `CHANGELOG.md:12-70` mit der Linkdefinition in `:590`; die sechs Lieferverbote oben mit Ausgabe | gemessen |

Ausdrücklich hergeleitet und nicht gemessen, in einer Liste, damit die Phasenverifikation sie
nicht überliest:

1. Das Erscheinen von `mcp_connector:audit:read` in `occ list` nach dem
   Deaktivieren-Aktivieren-Zyklus (Registrierung läuft im `enabled=1`-Zweig,
   `getOccCommands()` liest einen verteilten Cache).
2. Das Ausbleiben einer Namenskollision der vier Optionsnamen mit globalen occ-Optionen von
   Symfony (Assumption A2 der Recherche).
3. Die Sichtbarkeit der neuen Beschriftung in den Admin-Einstellungen einer bestehenden
   Installation, aus demselben Grund wie 1.

Der Grund ist derselbe wie in Phase 18: auf diesem Rechner läuft keine Test-Nextcloud, die
Topologie ist seit 06-07 heruntergefahren. Die Messung ist ein Release-Gate von EXAPP-12.

## Owner-Schrittliste für den echten Lauf

Ausführbar, ohne diesen Plan oder ein anderes Artefakt zu lesen. Auf der Nextcloud-Instanz, in
dieser Reihenfolge:

1. `occ app_api:app:disable mcp_connector`
2. `occ app_api:app:enable mcp_connector`
3. `occ list | grep mcp_connector` , es müssen **drei** Zeilen erscheinen:
   `mcp_connector:purge`, `mcp_connector:audit:verify` und `mcp_connector:audit:read`. Zeigt
   der Schritt nur zwei, ist die Registrierung fehlgeschlagen; der Grund steht als eine Zeile
   im Log der App und nennt den Namen des Kommandos.
4. `occ list --help` , prüfen, dass keiner der vier Optionsnamen (`user`, `since`, `limit`,
   `json`) mit einer globalen Option von Symfony kollidiert.
5. `occ mcp_connector:audit:read` , die Textform, neueste zuerst, mit dem angewandten Deckel
   (200) in der Kopfzeile.
6. `occ mcp_connector:audit:read --user alice --limit 5` , eine Kontokette mit eigenem Deckel.
7. `occ mcp_connector:audit:read --since 7` , die letzten sieben Tage.
8. `occ mcp_connector:audit:read --json` , die Maschinenform, ein JSON-Dokument mit den
   Schlüsseln `read`, `count`, `limit_applied`, `truncated`, `entries`, `note`, die Einträge in
   Kettenreihenfolge.
9. `occ mcp_connector:audit:verify` , die Gegenprobe, dass das ältere Prüfkommando durch die
   dritte Registrierung unverändert antwortet.

Zusätzlich mit dem Auge, kein Kommando: die Admin-Einstellungen dieser App öffnen und prüfen,
dass unter "Keep a record of tool calls" die lange Beschriftung steht (Parameternamen niemals
ihre Werte, Ablehnungsgrund, Dauer, Mitbestimmungshinweis, 180 Tage, 100 MB).

Wird ein Schritt rot, ist das kein Fund dieser Phase, sondern die Messung, die diese Phase
ausdrücklich nicht liefern konnte.

## Decisions Made

- **Der Block ist neu angelegt.** Der Plan warnt davor (Pitfall 13), und die Messung gibt ihm
  recht: `grep -n "^## " CHANGELOG.md | head -1` zeigte vor diesem Plan `12:## [0.1.11] -
  2026-08-28`. Phase 16 hat den vorigen `[Unreleased]`-Block in diesen Eintrag überführt. Ein
  "Befüllen" hätte bedeutet, in einen veröffentlichten Eintrag zu schreiben.
- **Der Deaktivieren-Aktivieren-Zyklus ist ein eigener Punkt.** Er ist die einzige Aussage des
  Blocks, die eine Handlung verlangt, und er entscheidet, ob die anderen Punkte für eine
  bestehende Installation überhaupt zutreffen. Als Nebensatz in einem der drei anderen Punkte
  hätte ihn niemand gelesen, der nur die Überschriften überfliegt.
- **U+202E wird benannt und nicht eingesetzt.** Der Fixed-Punkt schreibt "a formatting
  character, such as U+202E"; das Zeichen selbst steht nirgends in der Datei (T-19-39). Ein
  Changelog, das ein Leserichtungszeichen einsetzt, um von ihm zu erzählen, dreht die Zeile,
  die es beschreibt.
- **Zwei Zeilen der Nachweistabelle tragen `hergeleitet`, obwohl ihr Kern gemessen ist.** Die
  Alternative wäre ein drittes Urteil gewesen ("teils"), und genau das verbietet der Plan. Die
  Belegspalte trennt deshalb ausdrücklich, was am Baum gemessen ist und was ohne Instanz nicht
  messbar war; das Urteil folgt dem schwächeren Teil, weil das Kriterium eine Aussage über eine
  laufende Installation ist.
- **Der Einleitungsabsatz nennt keine Versionsnummer.** Ein `[Unreleased]`-Block, der schon
  wüsste, welche Nummer er einmal trägt, wäre eine Vorwegnahme von EXAPP-12; `grep -c "0.1.12"
  CHANGELOG.md` ergibt 0.

## Deviations from Plan

### Klarstellungen im Wortlaut

- **Task 2 hat keinen eigenen Commit.** Seine Anweisung beginnt mit "Kein weiterer Dateiinhalt,
  sondern Messen und Belegen", und seine Akzeptanzkriterien verlangen ausschliesslich Zeilen im
  SUMMARY. Ein leerer Commit hätte nichts belegt; das Ergebnis von Task 2 ist dieses Dokument
  und wandert mit dem Abschlusscommit in den Baum.
- **Das erste Akzeptanzkriterium von Task 1 zum Diff ist erfüllt, und die eine erlaubte
  `^-`-Zeile ist eine andere als die vermutete.** `git diff 4baacbd HEAD -- CHANGELOG.md |
  grep -c "^-"` ergibt **1**, und diese eine Zeile ist die Kopfzeile `--- a/CHANGELOG.md` des
  Diffs selbst und nicht die Kontextzeile des Definitionsblocks: der Block ist eine reine
  Einfügung, auch am Dateiende. Keine Inhaltszeile wurde entfernt oder verschoben,
  `git diff --numstat 4baacbd HEAD -- CHANGELOG.md` ergibt `62 0`.
- **`grep -c "disable and enable" CHANGELOG.md` ergibt 1** und nicht mehr. Das Kriterium
  verlangt mindestens 1. Die Wendung steht genau einmal, im vierten Changed-Punkt, wo sie
  hingehört.

---

**Total deviations:** 0 auto-fixed, 3 Klarstellungen
**Impact on plan:** Kein erweiterter Auftrag, keine Zusage des Plans geändert.

## Issues Encountered

- `CHANGELOG.md` trägt im Arbeitsbaum LF (binär gemessen: 0 CRLF), anders als die vier
  Textdateien aus 19-08. Git meldet beim Commit "LF will be replaced by CRLF the next time Git
  touches it"; das ist der bestehende Zustand des Repos (`core.autocrlf=true`, `* text=auto`)
  und kein Ergebnis dieses Plans. Geschrieben wurde binär mit demselben Zeilenende, Ergebnis
  ist ein Diff von 62 Einfügungen und 0 Löschungen.
- Die Testsuite gibt in diesem Repo keine Summenzeile aus (`addopts` enthält `-q`), also sind
  die 3095 Fälle mit `--collect-only -q` gezählt, wie in den Plänen davor.
- Keine Korruption in `.planning/STATE.md` oder `.planning/ROADMAP.md` entdeckt
  (Verifikationsschritt 5): Prozentwert, `last_activity` und die Tabellentrenner der
  Progress-Tabelle waren vor der Änderung intakt. Beide Dateien sind in diesem Plan **von Hand**
  fortgeschrieben und nicht über `gsd-sdk`, genau deshalb.
- **Eine kleine Drift in `.planning/STATE.md` gefunden und von Hand korrigiert:** der Abschnitt
  "Session Continuity" stand auf `Stopped at: Completed 19-07-PLAN.md`, während das Frontmatter
  bereits `Completed 19-08-PLAN.md` sagte; Plan 19-08 hatte den Abschnitt nicht nachgezogen.
  Beide Stellen sagen jetzt `Completed 19-09-PLAN.md`. Ebenfalls veraltet und mitgezogen: der
  Abschnitt "Operator Next Steps" empfahl noch, die Phasen 16 bis 18 zu planen.

## Anforderungen

**AUDIT-06 ist mit diesem Plan erfüllt und in `REQUIREMENTS.md` abgehakt** (Checkbox und Zeile
der Nachweistabelle). Die Anforderung hatte vier Hälften, und alle vier stehen:

1. Das Vier-Wörter-Gate als Anspruchsliste neben dem Vokabular-Gate (19-03), mit zwei
   Gegenproben.
2. Die neue Wahrheit in `docs/privacy.md`, `docs/uninstall.md` und `docs/faq.md` (19-05), an
   vier Codekonstanten gebunden.
3. Der Enterprise-Absatz an allen sechs Stellen in drei Sprachen (19-08), an drei Markertripeln
   gehalten.
4. Der `[Unreleased]`-Block, der die drei zusammenführt und sagt, dass nichts davon
   ausgeliefert ist (dieser Plan).

AUDIT-04 (seit 19-07) und AUDIT-05 (seit 19-02) bleiben unverändert Complete. Damit sind alle
drei Anforderungen der Phase erfüllt: AUDIT-04 durch 19-01, 19-04, 19-06 und 19-07, AUDIT-05
durch 19-02, AUDIT-06 durch 19-03, 19-05, 19-08 und 19-09.

## Threat Flags

Keine neue Fläche: keine Route, kein Netzzugang, keine Berechtigung, kein Paket, kein
Manifesteintrag, keine Versionszeichenkette, keine Produktionsdatei. Die sechs Fäden des
Registers dieses Plans:

- **T-19-36** (Tampering, kritisch): kein Tag, kein Archiv, kein Upload.
  `git tag --points-at HEAD` leer, `git tag --list "v0.1.12"` leer, `git status --short` leer,
  kein `.tar.gz` im Baum, kein Lauf von `scripts/build_store_release.sh`. Milestone-Tags heissen
  `milestone-v*` und nie `v*`, weil `release.yml` auf `v*` triggert (D-v1.5-03).
- **T-19-37** (Repudiation, hoch): die Einträge zu 0.1.10 und 0.1.11 sind unberührt.
  `git diff --numstat HEAD~1 HEAD -- CHANGELOG.md` ergibt `62 0`; keine Satzzeile eines
  Release-Eintrags ist entfernt oder umgeschrieben.
- **T-19-38** (Repudiation, hoch): jedes Urteil der Nachweistabelle ist `gemessen` oder
  `hergeleitet`, und die drei nicht messbaren Punkte stehen zusätzlich als eigene Liste, damit
  die Phasenverifikation sie nicht als geprüft weiterschreibt (Präzedenz R-18-05).
- **T-19-39** (Information Disclosure, gering): kein Kontoname, kein Pfad, kein Parameterwert
  und kein Steuerzeichen im Blocktext. U+202E ist benannt und nicht eingesetzt; die Datei
  enthält kein Zeichen der Kategorie Cf.
- **T-19-40** (Tampering, mittel): `scripts/check_tool_budget.py` meldet unverändert
  `15712 bytes, 21 tools, budget 18000`; kein Grenzwert wurde angehoben, kein Gate abgeschaltet.
- **T-19-SC** (Supply Chain, gering): `git diff --stat 4baacbd HEAD -- pyproject.toml uv.lock`
  ist leer.

Das Anspruchs-Gate und das Vokabular-Gate laufen über den neuen Blocktext und sind still: kein
"revisionssicher", kein "tamper proof", keine Konformitätsbehauptung, keine Zertifizierung, kein
verbotenes Wort, kein Em-Dash, kein En-Dash, kein Emoji.

## User Setup Required

Der Blocktext erreicht niemanden ausserhalb dieses Repositories, bis EXAPP-12 ein Release baut.
Für den Owner bleibt allein die Schrittliste oben, und sie ist ein Release-Gate und keine
Voraussetzung dieser Phase.

## Next Phase Readiness

- Phase 19 ist mit diesem Plan ausgeführt (9 von 9 Plänen); die Verifikation der Phase steht
  noch aus und findet in diesem SUMMARY die Nachweistabelle, die sechs Lieferverbote mit
  Ausgabe und die drei ausdrücklich hergeleiteten Punkte.
- EXAPP-12 (Release 0.1.12 mit dem Audit-Log) findet den ganzen Textrest im
  `[Unreleased]`-Block; beim Release wandert der Block unter eine Versionsüberschrift mit Datum,
  die Linkdefinition wird auf `compare/v0.1.11...v0.1.12` umgeschrieben und ein neuer leerer
  Block entsteht darüber. Die Owner-Schrittliste oben ist das Gate davor.
- Offener Hinweis aus 19-03 und 19-08, hier nicht angefasst:
  `tests/unit/test_exapp_admin_settings.py` trägt weiterhin eine eigene, kleinere
  `FORBIDDEN_CLAIMS`-Fassung für die Formularfläche. Zwei Listen sind zwei Wortlaute derselben
  Regel; die Zusammenlegung ist ein eigener kleiner Auftrag und gehört nicht in einen
  Abschlussplan, der keine Produktionsdatei anfassen soll.
- `exapp/ui/layout.py` trägt weiter eine vierte Fassung der Reinigungsregel (Hinweis aus
  19-01); sie ist keine Lücke im Sinne von R-18-06, aber die letzte Stelle mit einem zweiten
  Wortlaut derselben Zusage.

## Verification

- Sieben Gates: siehe Tabelle oben, alle grün.
- `grep -c "^## \[Unreleased\]" CHANGELOG.md`: 1.
- `grep -n "^## " CHANGELOG.md | head -2`: `12:## [Unreleased]`, `73:## [0.1.11] - 2026-08-28`.
- `grep -c "^\[Unreleased\]:" CHANGELOG.md`: 1, Zeile 590, endet auf `v0.1.11...HEAD`.
- `git diff 4baacbd HEAD -- CHANGELOG.md | grep -c "^-"`: 1 (gefordert höchstens 1), und diese
  Zeile ist `--- a/CHANGELOG.md`, die Kopfzeile des Diffs.
  `git diff --numstat 4baacbd HEAD -- CHANGELOG.md`: `62 0`.
- `grep -c "0.1.12" CHANGELOG.md`: 0. `grep -ci "archiv" CHANGELOG.md`: 0.
  `grep -c "disable and enable" CHANGELOG.md`: 1.
- Em-Dash und En-Dash in `CHANGELOG.md`, zeichenweise gezählt: je 0. CRLF-Zahl: 0.
- `uv run pytest tests/unit/test_exapp_env_setup.py -k "vocabulary or forbidden_claim" -q`: 6
  Fälle grün.
- Lieferverbote: siehe Tabelle oben, alle sechs belegt, dazu T-19-SC.
- `git status --short` nach dem Commit von Task 1: leer.
- `git diff --diff-filter=D --name-only HEAD~1 HEAD`: leer, keine Datei gelöscht.

## Self-Check: PASSED

- `CHANGELOG.md` liegt auf der Platte, 602 Zeilen, mit `## [Unreleased]` in Zeile 12 und der
  Linkdefinition in Zeile 590.
- `.planning/phases/19-audit-log-bedienung-und-textnachzug/19-09-SUMMARY.md` liegt auf der
  Platte.
- Der Task-Commit `d00ec9e` steht im Log (`git log --oneline -1` vor dem Abschlusscommit).

---
*Phase: 19-audit-log-bedienung-und-textnachzug*
*Completed: 2026-08-31*
