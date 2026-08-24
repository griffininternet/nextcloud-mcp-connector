<!--
  - SPDX-FileCopyrightText: 2026 street1983nk
  - SPDX-License-Identifier: AGPL-3.0-or-later
-->
---
phase: 11-b-ndelung-budget-und-release-0-1-6
plan: 09
subsystem: release
tags: [release, version, changelog, store-description, gates, in-02, exapp-07]

# Dependency graph
requires:
  - phase: 11-b-ndelung-budget-und-release-0-1-6
    plan: 06
    provides: "die Live-Messung der vier Beine, aus der die Aussagen des 0.1.8-Blocks über das Bündel stammen"
  - phase: 11-b-ndelung-budget-und-release-0-1-6
    plan: 07
    provides: "BUDGET_BYTES = 18000, verankert auf 15612 Bytes bei 21 Werkzeugen, und die 157 Bytes Diät"
  - phase: 11-b-ndelung-budget-und-release-0-1-6
    plan: 08
    provides: "preview_truncated als Eintragsfeld der Mail-Antwort, die Vertragsänderung, die im Changelog stehen muss"
  - phase: 10-mail-strikt-lesend-und-die-trifecta-grenze
    provides: "der vollständige Mail-Block, der unter [Unreleased] stand, und der Info-Befund IN-02"
provides:
  - "Version 0.1.8 an allen vier Stellen als identische Zeichenkette"
  - "CHANGELOG.md mit der Sektion [0.1.8] und der nachgetragenen Sektion [0.1.5]"
  - "die drei Store-Beschreibungen mit dem Ein-Aufruf-Bündel und den zwei direkt lesbaren Treffern"
  - "zwei Proof-Zeilen in docs/store-submission.md: sechs grüne Gates und der Archiv-Probelauf"
  - "die gemessene Oberfläche dieser Fassung: 15657 Bytes bei 21 Werkzeugen, Budget 18000"
affects:
  - "11-10 (setzt den Tag v0.1.8 auf genau diesen Zustand und baut das Release daraus)"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Der Unreleased-Block wird zur Versionssektion, und die Unreleased-Link-Definition bleibt stehen und zeigt auf die neue Version (die Form, die dieses Repo seit 0.1.7 hat: Link ohne Sektion)"
    - "Eine nachgetragene Sektion wird kurz und belegt geschrieben; was nicht in der Nachweistabelle steht, wird nicht erfunden"
    - "Eine Proof-Zeile entsteht nach ihrem Ereignis, nie davor"

key-files:
  created:
    - .planning/phases/11-b-ndelung-budget-und-release-0-1-6/11-09-SUMMARY.md
  modified:
    - pyproject.toml
    - src/mcp_connector/__init__.py
    - appinfo/info.xml
    - CHANGELOG.md
    - docs/store-submission.md
    - uv.lock

key-decisions:
  - "Die Release-Nummer ist 0.1.8 und nicht die 0.1.6 des Phasentitels: 0.1.4 bis 0.1.7 liegen im Store"
  - "Kein leerer [Unreleased]-Block über [0.1.8]: der Stand bei v0.1.7 hatte die Link-Definition ohne Sektion, und das ist die Form dieser Datei"
  - "IN-02 wird durch die fehlende Sektion geschlossen und nicht durch eine Linkkorrektur: der Tag v0.1.5 existiert (Proof-Zeile 2026-08-22 10:59Z, Run 32569019469)"
  - "Der Spendenlink bekommt trotzdem einen Changelog-Eintrag unter Changed: die Adresse auf der öffentlichen Store-Seite ändert sich für jeden Leser, auch wenn die Zeile selbst in diesem Plan nicht angefasst wurde"
  - "uv.lock wird mitgeführt, gegen den Wortlaut von Verifikation 5: uv schreibt die eigene Projektversion in die Lockdatei, und alle vier bisherigen Release-Commits (0.1.5, 0.1.6, 0.1.7) haben dieselbe eine Zeile mitgenommen"
  - "Die zwei neuen Aussagen der Store-Beschreibung stehen als Aufzählungspunkte in der Fähigkeitenliste statt als eigener Absatz: die Form der Beschreibung seit 0.1.5 ist eine Zeile je Fähigkeit"

patterns-established:
  - "Ein Prüfskript des Plans, das gegen die Wirklichkeit der Datei falsch ist, wird korrigiert ausgeführt und die Korrektur wird als Abweichung benannt"

requirements-completed: []  # EXAPP-07 wird erst mit dem Store-Upload in Plan 11-10 wahr

# Metrics
duration: 25min
completed: 2026-08-25
---

# Phase 11 Plan 09: Version 0.1.8, der Changelog dieser Phase und sechs grüne Gates Summary

**Die Fassung steht am Rand des irreversiblen Schritts: vier identische Versionsstrings, ein
Changelog-Block, der jede nutzerrelevante Änderung dieser Phase benennt, die seit Phase 10
fehlende Sektion 0.1.5 nachgetragen, Store-Texte in drei Sprachen, sechs lokal grüne Gates und
kein Tag.**

## Performance

- **Duration:** ca. 25 min
- **Started:** 2026-08-24T22:16Z
- **Completed:** 2026-08-24T22:42Z
- **Tasks:** 3
- **Files modified:** 6

## Die vier Versionsstellen

| Datei | Zeile | vorher | nachher |
|-------|-------|--------|---------|
| `pyproject.toml` | 3 | `version = "0.1.7"` | `version = "0.1.8"` |
| `src/mcp_connector/__init__.py` | 7 | `__version__ = "0.1.7"` | `__version__ = "0.1.8"` |
| `appinfo/info.xml` | 165 | `<version>0.1.7</version>` | `<version>0.1.8</version>` |
| `appinfo/info.xml` | 239 | `<image-tag>0.1.7</image-tag>` | `<image-tag>0.1.8</image-tag>` |

Der fünfte identische String, der Git-Tag `v0.1.8`, existiert nicht: `git tag --list v0.1.8` ist
leer. Er entsteht in Plan 11-10 nach der Owner-Freigabe.

`uv.lock` trägt eine sechste Stelle, die keine Entscheidung ist: die eigene Projektversion in
`[[package]] name = "nextcloud-mcp-connector"`. `uv` schreibt sie beim ersten Lauf nach dem
Bump selbst, und die Release-Commits von 0.1.5, 0.1.6 und 0.1.7 haben dieselbe Zeile
mitgenommen. Keine Abhängigkeit wurde hinzugefügt, entfernt oder in der Version bewegt.

Die `<donation>`-Zeile mit `paypalme/KhaledCherifDev` ist unverändert. Sie steht seit Commit
`d36356d` richtig im Manifest und wird mit diesem Release zum ersten Mal im Store sichtbar,
weil der Store das Manifest nur beim Upload liest.

## Der Inhalt des 0.1.8-Blocks

Überschrift `## [0.1.8] - 2026-08-25`, danach ein Absatz Prosa und drei Abschnitte.

**Prosa:** Mail ist die neueste Familie und die erste, die ausschliesslich liest; darum herum
geht es in dieser Fassung um einen Aufruf und eine Id.

**### Added**, sieben Punkte:

1. `prepare_context` trägt den Talk-Digest: höchstens drei Konversationen mit Ungelesenem oder
   Erwähnung, Vorschau bei 200 Bytes, eigenes Zeitbudget, eigener `degraded`-Eintrag (11-04).
2. `prepare_context` trägt die Mail-Ungelesen-Zähler für höchstens drei Konten und ihre Inbox,
   ausdrücklich ohne Betreff und ohne Nachrichteninhalt, mit einem fehlenden Feld statt einer
   Null, und mit dem gemessenen Preis von einem zusätzlichen Requestpaar (11-05, 11-06).
3. `fetch` löst zwei weitere Id-Arten auf: `message:<token>:<messageId>` über die spurenlose
   Kontextroute, mit Ablehnung statt Nachbarnachricht, und `table:<tableId>` mit Titel,
   Gesamtzeilenzahl und den ersten Zeilen. Eine View bleibt URL, ein Mail-Treffer bleibt URL
   mit genanntem Grund (11-01, 11-02, 11-03).
4. bis 7. sind der Mail-Block aus Phase 10, wörtlich aus `[Unreleased]` übernommen:
   `mail_browse` auf drei Ebenen, die Filter mit der Ablehnung unbekannter Bedingungen, der
   Volltext über `fetch` mit `mail:<databaseId>` samt Vertrauens-Signalen neben dem Text, und
   die einsätzige Degradation aller drei Familien ohne die Mail-App.

**### Changed**, drei Punkte:

1. Die Antwortformat-Änderung, ausdrücklich als solche benannt: `truncated` auf Eintragsebene
   von `mail_browse(level="messages")` heisst `preview_truncated`; die Antwortebene behält
   `truncated`. Der Satz sagt, dass ein Abnehmer des alten Schlüssels nachziehen muss (11-08).
2. Die Beschreibungen sind 157 Bytes kürzer bei gleicher Information, und das Gate steht zum
   ersten Mal auf einer Messung, die es senkt: 15612 Bytes bei 21 Werkzeugen, Gate von 18500
   auf 18000 (11-07).
3. Der PayPal-Spendenknopf zeigt auf eine paypal.me-Adresse statt auf eine, die eine
   Mailadresse im Klartext auf einer öffentlichen Seite trug. Gleicher Empfänger.

**### Security**, ein Punkt: Mail ist nur lesend, mit dem Vertragstest und der Benennung der
Kette samt Gegenmassnahme `NC_MCP_TALK_SEND` (wörtlich aus `[Unreleased]`).

Der Linkblock am Dateiende bekam `[0.1.8]: .../compare/v0.1.7...v0.1.8`, und die
`[Unreleased]`-Definition zeigt jetzt auf `compare/v0.1.8...HEAD`. Eine leere
`[Unreleased]`-Sektion wurde bewusst nicht angelegt: der Stand bei `v0.1.7` hatte die
Link-Definition ohne Sektion, und das ist die Form dieser Datei.

## Die nachgetragene 0.1.5-Sektion und ihre Belegquelle

`## [0.1.5] - 2026-08-22`, zwischen `[0.1.6]` und `[0.1.4]`, ein Absatz Prosa und ein
`### Changed` mit einem Punkt. Inhalt: die heutige Store-Beschreibung (eine Zeile je Familie,
danach was die App bewusst nicht tut und wer den Schalter hält), plus Homepage-Link, beide
Dokumentationslinks und beide Spendenknöpfe. Der Absatz sagt zusätzlich, warum es zwei
Releases waren: die Änderung war eine Minute nach dem Upload nicht auf der Store-Seite, und
0.1.6 hat einen Cache gejagt, der sich selbst erneuert.

Belegquellen, alle im Repo:

- `docs/store-submission.md`, Proof-Zeile `2026-08-22 11:00Z`: die Store-Seite zeigt die neue
  Beschreibung, Homepage, beide Dokumentationslinks und beide Spendenknöpfe und nennt 0.1.5.
- `docs/store-submission.md`, Cache-Notiz am Dateiende: "Version 0.1.5 and 0.1.6 were both
  spent on that mistake."
- `appinfo/info.xml`, Kommentar über den Beschreibungen: "The shape since 0.1.5".
- Proof-Zeile `2026-08-22 10:59Z`, Run `32569019469`: der Tag `v0.1.5` existiert. Deshalb ist
  die fehlende Sektion der Fehler und nicht die Link-Definition, und die Links blieben
  unverändert.

Was nicht in die Sektion kam, weil es nicht belegbar ist: eine Aufzählung dessen, was genau
0.1.6 zusätzlich zu 0.1.5 änderte. Der `[0.1.6]`-Block wurde nicht angefasst.

## Die Store-Beschreibung in drei Sprachen

Je zwei neue Aufzählungspunkte am Ende der Fähigkeitenliste, in EN, DE und FR in derselben
Aussagetiefe:

- **One call / Ein Aufruf / Un seul appel**: `prepare_context` bündelt Suche, kommende Woche,
  wartende Talk-Konversationen und Mail-Ungelesen-Zähler in einer Antwort, und der Satz sagt
  ausdrücklich, dass das Standardbündel weder Betreff noch Nachrichteninhalt enthält.
- **Open a hit in place / Einen Treffer direkt lesen / Lire un résultat sur place**: eine
  Talk-Nachricht und eine Tabelle aus der Suche werden dort gelesen, wo sie gefunden wurden;
  ein Mail-Treffer bleibt bewusst ein Link, mit dem Grund im selben Satz.

Die Ketten-Formulierung aus Befund CR-01 (der Absatz über die Trifecta-Grenze) ist in allen
drei Sprachen unverändert. Die `<summary>`-Elemente wurden nicht angefasst und liegen weiter
unter 128 Zeichen. Alle drei Blöcke sind frei von Backtick, Tabelle, Bild, horizontaler Regel
und HTML, tragen mehr als zwei Absätze, echte Umlaute im deutschen und Akzente plus Cedille im
französischen Block, und keiner enthält das verbotene Wort.

## Die sechs Gates, mit ihren Ausgaben

| # | Befehl | Ausgabe |
|---|--------|---------|
| 1 | `uv run --no-sync pytest -q` | `2766 passed, 163 deselected in 92.50s` |
| 2 | `uv run --no-sync ruff check .` | `All checks passed!` |
| 3 | `uv run --no-sync ruff format --check .` | `197 files already formatted` |
| 4 | `uv run --no-sync pyright` | `0 errors, 0 warnings, 0 informations` |
| 5 | `uv run --no-sync vulture src scripts vulture_whitelist.py` | keine Ausgabe, Exit 0 |
| 6 | `uv run --no-sync python scripts/check_tool_budget.py` | `tools/list: 15657 bytes, 21 tools, budget 18000`, Exit 0 |

Die fünf grössten Werkzeuge aus Gate 6: `mail_browse` 1376, `calendar_create_event` 1351,
`calendar_list_events` 951, `search` 924, `deck_create_card` 877 Bytes. Alle unter
`MAX_TOOL_BYTES` 1400.

**Die Bytezahl weicht vom Akzeptanzkriterium ab, und zwar erklärbar.** Der Plan erwartete die
Zahl aus 11-07-SUMMARY, also 15612. Gemessen sind 15657, eine Differenz von genau 45 Bytes.
Das sind die 45 Bytes, die Plan 11-08 der `mail_browse`-Beschreibung hinzugefügt hat, als
`preview_truncated` benannt wurde (dort dokumentiert als 1331 auf 1376 von 1400). 11-07 ist die
ältere Messung, 15657 ist der Stand der Fassung, die released wird, und der Changelog nennt
bewusst 15612 als die Messung, auf der das Gate verankert wurde. Beide Zahlen sind wahr, und
sie beschreiben verschiedene Dinge.

## Der Archiv-Probelauf

`scripts/build_store_release.sh`, dann `tar -tzf dist/mcp_connector-0.1.8.tar.gz`:

```
mcp_connector/
mcp_connector/appinfo/
mcp_connector/appinfo/info.xml
mcp_connector/CHANGELOG.md
mcp_connector/LICENSE
mcp_connector/README.md
```

Genau ein Verzeichnis auf oberster Ebene, `mcp_connector`, Kleinbuchstaben mit Unterstrich, mit
`appinfo/info.xml` darin, und `CHANGELOG.md` reist mit. Grösse 45710 Bytes, sha256
`15fc8719...`.

**Dieses Archiv ist nicht das Artefakt, das signiert wird.** `tar.gz` ist nicht
byte-reproduzierbar; der Beleg steht als Proof-Zeile vom 2026-08-20 in
`docs/store-submission.md`: 31909 gegen 32168 Bytes bei unterschiedlichem sha256 für dieselbe
Version. Signiert wird immer das heruntergeladene Release-Asset, und das ist Schritt 6 des
Runbooks und damit Plan 11-10.

## Im Runbook entdeckte Ungenauigkeiten

Eine, und sie ist nicht korrigiert worden, weil eine Korrektur eine Entscheidung ist und keine
Nebenwirkung:

`scripts/build_store_release.sh` gibt am Ende nicht nur den Pfad des gebauten Archivs aus,
sondern auch eine fertige base64-SHA-512-Signatur über genau dieses lokal gebaute Archiv, mit
der Zeile "paste into the store upload form". Runbook-Schritt 6 sagt das Gegenteil, und er hat
recht: signiert wird das heruntergeladene Asset, nie der lokale Bau. Wer den Probelauf aus
Schritt 3 macht und die ausgegebene Signatur benutzt, reicht eine Signatur ein, die nicht zu
den Bytes passt, die der Store herunterlädt. Das Skript widerspricht damit dem Runbook an der
teuersten Stelle. Vorschlag für Plan 11-10 oder später: entweder die Signaturausgabe aus dem
Skript entfernen, oder ihre Zeile umschreiben, sodass sie sagt, wofür sie nicht taugt.

Die acht Runbook-Schritte selbst sind im Wortlaut unverändert.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Das Prüfskript aus Task 2 las die Sprachattribute über den falschen Namensraum**

- **Found during:** Task 2
- **Issue:** Das im Plan mitgelieferte Skript liest die Sprache mit
  `el.get('{http://www.w3.org/XML/1998/namespace}lang')`, also `xml:lang`. `appinfo/info.xml`
  benutzt aber ein einfaches `lang`-Attribut (`<description lang="de">`), wie es `info.xsd`
  vorgibt. Alle drei Blöcke wären auf den Schlüssel `en` gefallen, das Dictionary hätte einen
  Eintrag gehabt, und die Behauptung `set(descriptions) >= {'en','de','fr'}` wäre
  fehlgeschlagen, obwohl die Datei richtig ist.
- **Fix:** Das Skript wurde mit `el.get('lang') or 'en'` ausgeführt. Alle Behauptungen sind
  danach grün, inklusive Umlaut- und Akzentprobe und der 128-Zeichen-Grenze der Summaries.
- **Files modified:** keine, es ist ein Prüfschritt und kein Artefakt.
- **Commit:** keiner.

**2. [Rule 3 - Blocking] `uv.lock` gehört in den Commit, gegen den Wortlaut von Verifikation 5**

- **Found during:** Task 1
- **Issue:** Verifikation 5 und T-11-SC verlangen eine unangetastete `uv.lock`. `uv` schreibt
  aber beim ersten Lauf nach dem Bump die eigene Projektversion in die Lockdatei
  (`name = "nextcloud-mcp-connector"`, `version`), und ein Lauf findet in diesem Plan
  zwangsläufig statt, weil jedes Gate über `uv run` geht.
- **Fix:** Die eine Zeile wurde mitcommittet. Der Sinn der Bedingung ist unberührt: keine neue,
  entfernte oder in der Version bewegte Abhängigkeit, kein `uv add`, kein `pip install`. Die
  Release-Commits von 0.1.5 (`dc780e7`), 0.1.6 (`fe0cd74`) und 0.1.7 (`6b67cbc`) haben dieselbe
  Zeile genauso mitgenommen.
- **Files modified:** `uv.lock` (eine Zeile).
- **Commit:** `8392680`.

**3. [Rule 2 - Vollständigkeit] Der Spendenlink bekam einen Changelog-Eintrag**

- **Found during:** Task 1
- **Issue:** Der Plan nimmt die `<donation>`-Zeile ausdrücklich vom Umfang aus, sagt aber
  nichts über den Changelog. Für einen Leser der Store-Seite ändert sich mit diesem Release
  die Zahlungsadresse, und eine Änderung, die ein Nutzer sieht, gehört in den Changelog.
- **Fix:** Ein Punkt unter `### Changed`, der Adresse, Grund und gleichbleibenden Empfänger
  nennt. Die Zeile in `appinfo/info.xml` selbst wurde nicht angefasst.
- **Files modified:** `CHANGELOG.md`.
- **Commit:** `8392680`.

### Abweichung ohne Fix

**Die Bytezahl aus Gate 6 ist 15657 und nicht die vom Akzeptanzkriterium erwartete 15612.**
Erklärung oben im Abschnitt über die sechs Gates: die Differenz sind exakt die 45 Bytes, die
Plan 11-08 nach der Messung von 11-07 hinzugefügt hat. Das Gate ist grün, die Grenze von 18000
ist unverändert, und keine Zahl wurde angepasst, um ein Kriterium zu treffen.

## Keine Authentifizierungs-Gates

Keine. Dieser Plan berührt keinen fremden Dienst; alles lief lokal.

## Was bewusst nicht getan wurde

- **Kein Tag, kein Push.** `git tag --list v0.1.8` ist leer. Schritt 4 des Runbooks ist der
  irreversible Schritt und gehört zu Plan 11-10 mit seinem Owner-Checkpoint.
- **Keine Proof-Zeilen für die Runbook-Schritte 4 bis 8.** Eine Zeile, die vor ihrem Ereignis
  geschrieben wird, ist eine Behauptung ohne Deckung.
- **Keine Korrektur der Link-Definitionen im Changelog.** Sie waren richtig; die Sektion fehlte.
- **Kein Umschreiben des Runbook-Textes.** Die entdeckte Ungenauigkeit steht als Satz oben.

## Commits

| Commit | Task | Inhalt |
|--------|------|--------|
| `8392680` | 1 | Version 0.1.8 an vier Stellen, `[0.1.8]`- und `[0.1.5]`-Sektion, Linkblock |
| `346ac33` | 2 | die zwei neuen Aussagen in allen drei Store-Beschreibungen |
| `5c51c19` | 3 | zwei Proof-Zeilen für die sechs Gates und den Archiv-Probelauf |

## Verification

1. Vier identische Versionsstrings, `paypalme/KhaledCherifDev` unverändert: grün.
2. `CHANGELOG.md` mit `[0.1.8]` und `[0.1.5]`, absteigend sortiert, Linkblock vollständig,
   `preview_truncated` enthalten, keine Em- oder En-Dashes, kein verbotenes Wort: grün.
3. `uv run pytest tests/unit/test_exapp_env_setup.py -q`: grün, 148 Fälle.
4. Alle sechs Gates aus Runbook-Schritt 3: grün, Ausgaben in der Tabelle oben.
5. Archiv-Probelauf: genau ein Verzeichnis auf oberster Ebene mit `appinfo/info.xml` und
   `CHANGELOG.md` darin.
6. Zwei Proof-Zeilen mit Datum inklusive Zeit in Z, Behauptung als ganzer Satz und Befehl.
7. `git tag --list v0.1.8`: leer.

## Next

Plan 11-10: der Owner-Checkpoint, danach Tag `v0.1.8`, Workflow, Signatur über das
heruntergeladene Asset, Store-Upload und die vier Proofs aus Runbook-Schritt 8.
