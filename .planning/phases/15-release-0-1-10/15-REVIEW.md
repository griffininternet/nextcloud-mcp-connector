---
phase: 15-release-0-1-10
reviewed: 2026-08-28T05:35:00Z
depth: standard
files_reviewed: 9
files_reviewed_list:
  - appinfo/info.xml
  - CHANGELOG.md
  - pyproject.toml
  - src/mcp_connector/__init__.py
  - uv.lock
  - README.md
  - README.de.md
  - README.fr.md
  - docs/store-submission.md
findings:
  critical: 0
  warning: 5
  info: 10
  total: 15
status: issues_found
---

# Phase 15: Code Review Report

**Reviewed:** 2026-08-28T05:35:00Z
**Depth:** standard
**Files Reviewed:** 9
**Status:** issues_found

## Summary

Ein reines Text- und Versions-Release. Die mechanischen Teile halten: Version, Changelog-Struktur
und Zeilenenden wurden nachgerechnet und stimmen exakt, nicht nur plausibel.

Was ich gegengeprüft und als korrekt bestätigt habe:

- Versions-Konsistenz über alle sechs Stellen: `pyproject.toml:3`, `src/mcp_connector/__init__.py:7`,
  `appinfo/info.xml:183` (`<version>`), `appinfo/info.xml:258` (`<image-tag>`), die drei
  `Version 0.1.10.`-Statuszeilen der READMEs und der Self-Eintrag in `uv.lock:472`. Kein
  0.1.9-Rest in einer Quelldatei; die vier Treffer in `CHANGELOG.md` sind historische
  Bezüge und Linkdefinitionen, also gewollt.
- `uv lock --check` läuft sauber durch, die Hand-Edit-Zeile in `uv.lock` hat den Lockfile
  nicht von der Auflösung getrennt.
- Changelog-Struktur: 11 Überschriften gegen 11 Linkdefinitionen, kein ungepaartes Paar in
  beide Richtungen, kein `[Unreleased]`, Datumsreihenfolge absteigend.
- Zeilenenden byte-genau erhalten: CRLF 536 / 551 / 570 / 540 für `README.md`, `README.de.md`,
  `README.fr.md`, `appinfo/info.xml`, kein einziges nacktes LF, also kein versteckter
  Massen-Diff. Damit ist die Behauptung der Proof-Zeile 146 unabhängig belegt.
- XSD-Verträglichkeit: alle drei Summaries unter 128 Zeichen (106 / 110 / 110), kein Backtick,
  kein Pipe-Zeichen, kein Bild, kein HTML-Element, kein leeres `<default>`, kein verbotenes
  Vokabular. `uv run --no-sync pytest tests/unit/test_exapp_env_setup.py -q` ist grün, also hält
  das Manifest-Gate auch nach dem Post-Tag-Commit `b3267cd`.
- SEC-01 ist trotz der Kürzung weiter erfüllt: Die Anforderung verlangt für die Store-Beschreibung
  den Mail-ist-strikt-lesend-Satz (steht in allen drei Sprachen als eigener Aufzählungspunkt),
  und der Doku-Abschnitt mit der Exfiltrationskette samt `NC_MCP_TALK_SEND` liegt in
  `docs/privacy.md`, das dieses Release nicht angefasst hat. Der gekürzte Absatz nennt weiterhin
  alle vier verlangten Teile: fremde Texte, Talk als einzigen direkten Ausgang, den
  Admin-Schalter und geteilte Ablagen als Restweg.
- Release-Fakten gegen die Live-Systeme: Asset 46973 Bytes mit sha256 `4236d2e8…`, `isDraft` false,
  Workflow-Job `publish` 04:50:10Z bis 04:51:54Z, Tag `v0.1.10` auf `156280f`, 15 Tags lokal,
  11 `v0.1.*`-Tags, GHCR trägt alle elf Image-Tags, der Store-Katalog listet 11 Releases inklusive
  `0.1.10`. Keine erfundene Zahl gefunden.
- Keine Em-Dashes, keine ASCII-Ersatzumlaute, keine Secrets, keine Debug-Reste in den neun Dateien.

Kein BLOCKER: Dieses Release enthält keine ausführbare Logik, und die einzige geänderte
Python-Zeile ist eine Versionskonstante. Ich habe aktiv nach einem gesucht (Manifest-Gate,
Lock-Konsistenz, Live-Abgleich Store/GHCR/GitHub) und keinen belegen können.

Die fünf Warnungen betreffen zwei Muster: Beschreibungstexte, die durch die Kürzung sachlich
schwächer oder falsch geworden sind, und Proof-Zeilen beziehungsweise Changelog-Sätze, die mehr
behaupten, als tatsächlich gemessen oder geschrieben wurde. Genau das ist bei einem Release, dessen
gesamter Wert in seinen Texten liegt, die relevante Fehlerklasse.

Ein `<structural_findings>`-Block wurde nicht übergeben, deshalb entfällt der Abschnitt dazu.

## Narrative Findings (AI reviewer)

### Warnings

### WR-01: Vierter Nachweis von Runbook-Schritt 8 wurde durch eine lokale Git-Abfrage ersetzt

**Status:** FIXED in `901b294`

**File:** `docs/store-submission.md:153` (Regel gegen `docs/store-submission.md:287-297`)
**Issue:** Schritt 8 des eigenen Runbooks verlangt vier Nachweise, der vierte ist wörtlich
`https://ghcr.io/v2/street1983nk/mcp_connector/tags/list  # every released tag` (Zeile 296). Die
Proof-Zeile für 0.1.10 belegt stattdessen `git tag --list 'v0.1.*'` und formuliert das als
"the tag list holds eleven `v0.1.*` tags with `v0.1.10` among them". Eine lokale Git-Tagliste sagt
nichts über die Container-Registry aus. Genau dieser Registry-Aufruf ist aber der Test gegen ein
umgeschriebenes oder entferntes Image-Tag, den die Sektion "Two production dependencies, both
permanent" (Zeile 301-308) als nicht optional bezeichnet, und jede frühere Release-Zeile trägt ihn
(Zeilen 100, 108, 116, 123, 132, 144: "All nine/ten tags exist, none was rewritten and none was
removed"). Die Zeile erklärt Schritt 8 dennoch für erledigt. Erschwerend: die Abweichungsnotiz zu
dieser zusammengefassten Zeile behauptet, inhaltlich fehle kein Nachweis.

Der Sachverhalt selbst stimmt, ich habe die Registry abgefragt:
`{"tags":["0.1.0",...,"0.1.9","0.1.10"]}`. Falsch ist der Beleg, nicht die Welt. Ein Runbook, dessen
Beweisspalte einen anderen Befehl nennt als den durchgeführten, verliert genau die Eigenschaft,
für die es existiert.

**Fix:** Den echten Nachweis nachholen und die Beweisspalte korrigieren:

```bash
TOKEN=$(curl -sS "https://ghcr.io/token?scope=repository:street1983nk/mcp_connector:pull&service=ghcr.io" \
  | grep -o '"token":"[^"]*' | cut -d'"' -f4)
curl -sS -H "Authorization: Bearer $TOKEN" \
  https://ghcr.io/v2/street1983nk/mcp_connector/tags/list
# erwartet: alle elf Tags 0.1.0 bis 0.1.10, keiner entfernt
```

Ergebnis als eigene, datierte Zeile eintragen und in der bestehenden Zeile 153 die Formulierung
"the tag list holds eleven `v0.1.*` tags" durch "the local git tag list holds eleven `v0.1.*` tags,
which is not the registry check of step 8" ersetzen oder ganz streichen.

### WR-02: Die Adresse, die dieses Release entfernen sollte, wird vom Store weiter veröffentlicht

**Status:** OWNER-ENTSCHEID OFFEN. Die `<author mail=...>`-Adresse ist die Store-Konto-Identität; ob sie ebenfalls auf admin@infranode.dev wechselt, entscheidet der Owner. Bis dahin bleibt sie unverändert.

**File:** `appinfo/info.xml:185`, Anspruch in `CHANGELOG.md:20-22`
**Issue:** Der Changelog-Block sagt: "the contact address in it moved from k.cherif@outlook.de to
admin@infranode.dev". Das Manifest trägt aber unverändert
`<author mail="k.cherif@outlook.de">street1983nk</author>`, und dieses Feld ist öffentlich. Live
gegen den Katalog gemessen:

```
authors: [{'name': 'street1983nk', 'mail': 'k.cherif@outlook.de', 'homepage': ''}]
```

Die Proof-Zeile 153 zählt `k.cherif@outlook.de` deshalb korrekt mit null, prüft aber ausschließlich
`translations[*].description`, nicht `authors`. Die Adresse steht damit weiter im Klartext auf einer
öffentlichen Seite, und das ist exakt die Begründung, mit der 0.1.8 den PayPal-Button ausgetauscht
hat: "It carried a mail address in plain text on a public page before, which is a harvesting target
and not a payment detail anybody needs" (`CHANGELOG.md:146-149`). Dieselbe Begründung, dieselbe
Adresse, anderes Feld, unbemerkt geblieben. `pyproject.toml:7` trägt sie zusätzlich, das ist aber
Paket-Metadatum und nicht Store-Oberfläche.

**Fix:** Entweder das Autorenfeld im nächsten Release nachziehen und die Prüfung erweitern:

```xml
<author mail="admin@infranode.dev">street1983nk</author>
```

oder, falls die private Adresse dort bewusst stehen bleibt, den Changelog-Satz auf das begrenzen,
was er belegt: "the contact address of the enterprise section moved ...; the author field of the
manifest is unchanged and still public". Zusätzlich in Schritt 8 des Runbooks das Feld `authors`
mit in die Zählung nehmen, sonst wiederholt sich die Lücke bei jedem Release.

### WR-03: Der gekürzte Trifecta-Absatz nennt einen falschen Restweg

**Status:** FIXED in `901b294`

**File:** `appinfo/info.xml:68` (EN), `appinfo/info.xml:113` (DE), `appinfo/info.xml:160` (FR)
**Issue:** Die Kürzung `b3267cd` ersetzt "they can land in a folder, board or table that is shared
with other people" durch "they can land in a shared folder". Eine Deck-Karte landet in einem Board,
eine Tables-Zeile in einer Tabelle, keines von beiden in einem Ordner. Die Aufzählung nennt also
drei Schreibwege und dann einen Restweg, der nur für einen davon existiert. Dieselbe Verkürzung in
allen drei Sprachen ("in einem geteilten Ordner landen", "dans un dossier partagé"). Das ist kein
Stilpunkt: der Satz ist die einzige Stelle im gesamten Store-Text, die den indirekten Ausgangskanal
benennt, und ein Leser, der prüft, was sein Konto teilt, sieht nach diesem Satz nur in die
Dateifreigaben und nicht in Boards und Tabellen.

**Fix:** Ein Wort pro Sprache zurückholen, ohne den Absatz wieder aufzublähen:

```
EN: ... but they can land in a folder, board or table that is shared.
DE: ... können aber in einem geteilten Ordner, Board oder in einer geteilten Tabelle landen.
FR: ... mais ils peuvent atterrir dans un dossier, un tableau ou une table partagés.
```

Da `b3267cd` ohnehin erst mit 0.1.11 in den Store fährt, kostet die Korrektur kein zusätzliches
Release.

### WR-04: Die Manifest-Änderung nach dem Tag ist in keiner der geprüften Dateien festgehalten

**Status:** FIXED in `901b294`

**File:** `CHANGELOG.md:12-37`, `docs/store-submission.md:146-153`, `appinfo/info.xml:68,113,160`
**Issue:** `b3267cd` ändert `appinfo/info.xml` nach dem Tag `v0.1.10` (`156280f`). Damit weicht das
Manifest im Repository sowohl vom signierten 0.1.10-Asset als auch von dem ab, was der Store
ausliefert. Live gegengeprüft: die Store-Beschreibung trägt in EN, DE und FR weiterhin den langen
Absatz, der kurze steht nur lokal. Keine der neun geprüften Dateien hält das fest:

- `CHANGELOG.md` hat keinen Eintrag dafür und, korrekt nach dem eigenen Gate, auch keinen
  `[Unreleased]`-Abschnitt, in den er gehören würde.
- `docs/store-submission.md` hat dafür keine Proof-Zeile, obwohl das Dokument bei 0.1.10 sogar
  ausdrücklich vermerkt, dass eine nachträgliche Korrektur des 0.1.9-Blocks "after that tag existed"
  entstand (Zeile 148). Die gleiche Sorgfalt fehlt hier.

Der Hinweis existiert nur in einem Planungsartefakt, das gleichzeitig "keine `info.xml` nach dem Tag
geändert" behauptet und zwei Zeilen später das Gegenteil beschreibt. Für jemanden, der später das
Repo-Manifest gegen die Store-Kopie hält, ist die Abweichung damit unerklärt, und der Changelog-
Eintrag für 0.1.11 hängt an einer einzelnen Notiz in einer Datei, die nicht ausgeliefert wird.

**Fix:** Einen `## [Unreleased]`-Block im Changelog anlegen, der die Kürzung trägt, und ihn beim
nächsten Release in den 0.1.11-Block überführen:

```markdown
## [Unreleased]

### Changed

- The paragraph about reading text strangers wrote is three sentences now instead of one long
  one, in all three store descriptions. It travels with the next release, because the store
  reads the manifest only at upload time.
```

Zusätzlich eine datierte Zeile in `docs/store-submission.md`, die festhält, dass das Manifest im
Repository seit `b3267cd` bewusst von der veröffentlichten 0.1.10-Kopie abweicht.

### WR-05: Der Changelog behauptet eine Deutlichkeit, die die gekürzten Texte nicht mehr haben

**Status:** FIXED in `901b294`

**File:** `CHANGELOG.md:20-28`
**Issue:** Der Satz lautet: "the section describes a plan and not a feature, and the short wording
says so as plainly as the long one did". Die lange Fassung sagte es mit einem eigenen, fett
gesetzten Satz: "**None of the three exists in this app today, in no version and behind no
setting.**" (entfernt in `55a5822`). Die kurze Fassung sagt in allen vier Texten nur noch "are
planned as a commercial add-on" beziehungsweise "sind als kommerzielles Add-on geplant" /
"sont prévus comme module commercial" (`README.md:514-516`, `README.de.md:529-531`,
`README.fr.md:547-549`, `appinfo/info.xml:79`). "Geplant" impliziert die Nichtexistenz, benennt sie
aber nicht, und die Verneinung "in keiner Version und hinter keiner Einstellung" ist ersatzlos weg.
"As plainly as the long one did" ist damit nachweisbar falsch. Das trifft genau das Risiko, das
dieses Projekt in Phase 13 unter WR-03 selbst als Fake-Door-Kriterium behandelt hat, und es steht in
dem Dokument, das die Korrektheit der Kürzung belegen soll.

**Fix:** Entweder den Satz im Changelog auf das reduzieren, was gilt:

```
... exist in this version in no form and behind no setting: the section describes a plan and not a
feature, and the short wording says "planned" where the long one spelled the negation out.
```

oder besser, die Verneinung in die vier kurzen Texte zurücknehmen, einen Halbsatz pro Sprache, zum
Beispiel EN: "... are planned as a commercial add-on and exist in this version in no form."

### Info

### IN-01: "A release without a code change" ist eine Zeile Python zu absolut

**File:** `CHANGELOG.md:14-16`
**Issue:** `src/mcp_connector/__init__.py:7` ist geändert, und die Änderung ist nach außen sichtbar:
die eigene Proof-Zeile (`docs/store-submission.md:148`) misst, dass die Tool-Oberfläche um genau ein
Byte wächst, weil `serverInfo` im `tools/list`-Envelope die Versionszeichenkette trägt. Ein
verbundener Assistent bekommt also eine andere Antwort als unter 0.1.9. 0.1.3 hat genau diesen
Handshake-Wert als eigenen Fixed-Eintrag geführt.
**Fix:** "A release without a change to a tool, an answer or a setting. The only line of code that
moved is the version constant, which an assistant sees in the handshake."

### IN-02: Die Liste der Nur-Text-Releases ist unsauber

**File:** `CHANGELOG.md:26-28`
**Issue:** "0.1.5, 0.1.6 and 0.1.9 were all releases for exactly that reason". 0.1.9 war kein reines
Text-Release, sein eigener Block führt unter Changed eine Formatänderung (`truncated` zu
`message_truncated`, `CHANGELOG.md:57-67`). Umgekehrt fehlt 0.1.7, das laut eigenem Block
ausschließlich Store-Text und Kategorien geändert hat. Die Aufzählung wurde aus dem 0.1.9-Block
übernommen und hat dessen Ungenauigkeit mitgenommen.
**Fix:** "0.1.5, 0.1.6 and 0.1.7 were releases for exactly that reason, and 0.1.9 carried the same
kind of text next to its one format change."

### IN-03: "which is not a French word" ist zu stark

**File:** `CHANGELOG.md:33-34`
**Issue:** "confidemment" ist kein erfundenes Wort, sondern ein veraltetes, in modernen Texten nicht
mehr gebrauchtes Adverb, das ältere Wörterbücher führen. Die Korrektur selbst ist richtig und die
Ersetzung "une réponse fausse mais assurée" ist gutes Französisch, nur die Begründung behauptet
mehr, als sie belegen kann.
**Fix:** "The word 'confidemment', which no modern French text uses, is replaced at both of its
places ..."

### IN-04: Der Beschreibungs-Beleg lässt Französisch aus

**File:** `docs/store-submission.md:153`
**Issue:** "the `translations` of the same catalogue entry count `admin@infranode.dev` once and
`k.cherif@outlook.de` zero times in the English and the German description". Das Release liefert
drei Sprachen aus, geprüft wurden zwei. Ich habe die dritte nachgeholt, sie stimmt (fr: einmal
`admin@infranode.dev`, keine Outlook-Adresse), aber der Beleg deckt sie nicht ab.
**Fix:** Die Zählung über alle Schlüssel von `translations` laufen lassen und "in all three
descriptions" schreiben.

### IN-05: Der genannte Veröffentlichungszeitpunkt stimmt nicht mit der Release-API überein

**File:** `docs/store-submission.md:150`
**Issue:** Die Zeile warnt zu Recht davor, `createdAt` für den Veröffentlichungszeitpunkt zu halten,
und nennt als echten Zeitpunkt 04:51:55Z. `gh release view v0.1.10` liefert
`"publishedAt":"2026-08-28T04:51:46Z"` und das Asset mit `"createdAt":"2026-08-28T04:51:45Z"`. Die
04:51:55Z sind weder das eine noch das andere, der Job endete um 04:51:54Z. In einer Zeile, deren
Zweck die Unterscheidung zweier Zeitstempel ist, ist ein dritter, unbelegter besonders unglücklich.
**Fix:** "which the release API reports as `publishedAt` 04:51:46Z, one second after the asset
upload at 04:51:45Z".

### IN-06: Der gekürzte Satz doppelt den Aufzählungspunkt darüber und hat ein unklares "it"

**File:** `appinfo/info.xml:66` und `appinfo/info.xml:68`
**Issue:** Zeile 66: "**One direct messaging channel**: sending a Talk message, and an administrator
can switch it off". Zeile 68 wiederholt fast wörtlich: "The only direct way out is a Talk message,
and an administrator can switch it off". Nach der Kürzung trägt der Absatz gegenüber dem Punkt
darüber nur noch den geteilten Ordner bei. Zusätzlich bezieht sich das englische "it" grammatisch
auf "a Talk message", also auf eine einzelne Nachricht, die man nicht abschalten kann; DE ("ihn",
der Weg) und FR ("la", la sortie) lösen es sauber auf.
**Fix:** EN auf den Kanal beziehen: "The only direct way out is Talk, and an administrator can close
that channel for the whole instance." Damit verschwindet auch die Dopplung.

### IN-07: Die deutsche Beschreibung wechselt zwischen "Assistent" und "Assistenz"

**File:** `appinfo/info.xml:92` gegen `appinfo/info.xml:113,118,120`
**Issue:** Überschrift und Aufzählung sagen "Was ein Assistent kann", der von `b3267cd` neu
geschriebene Absatz und die Punkte darunter sagen "Eine Assistenz". Beide Formen im selben,
kurzen Text.
**Fix:** Auf "Assistent" vereinheitlichen, weil die Überschrift und die Sprache der Summary
(`appinfo/info.xml:19`, "KI-Assistenten") das schon vorgeben.

### IN-08: Die Aufzählung der anlegenden Schreibwege ist unvollständig

**File:** `appinfo/info.xml:68,113,160`
**Issue:** "New files, cards or rows" lässt Notizen und Kalendertermine aus, obwohl dieselbe
Beschreibung sie als Schreibwege nennt (Zeile 51: "Notes: search, read, write", Zeile 50:
"Calendar: ... create an event"). Eine Notiz kann genauso in einem geteilten Ordner landen. Die
lange Fassung hatte dieselbe Lücke, die Kürzung war die Gelegenheit, sie zu schließen. Positiv
geprüft: Kalendertermine sind kein Ausgangskanal, `src/` kennt weder `ATTENDEE` noch `ORGANIZER`,
es werden also keine Einladungen verschickt.
**Fix:** "New files, notes, events, cards or rows send nothing to anyone, but they can land in a
folder, board or table that is shared."

### IN-09: Sechs Variablen-Blöcke haben ein zusammengeklebtes schließendes Tag

**File:** `appinfo/info.xml:517,521,525,529,533,537`
**Issue:** Jeder der sechs `<variable>`-Blöcke endet als
`</description>\t\t\t</variable>` auf einer Zeile, während der Rest der Datei sauber eingerückt ist.
XML-gültig und vom Gate unbeanstandet, aber es macht jeden künftigen Diff an diesen Zeilen
unnötig unleserlich. Bestand vor dieser Phase, hier nur festgehalten.
**Fix:** `</variable>` auf eine eigene Zeile mit der Einrückung der Geschwisterelemente setzen.

### IN-10: "Talk to us" im Store-Text kollidiert mit der Talk-Familie

**File:** `appinfo/info.xml:79`
**Issue:** Der englische Store-Text sagt "Want to run this app in your organisation? Talk to us:
admin@infranode.dev", vier Zeilen unter dem Aufzählungspunkt "**Talk**: read conversations, send a
message" und dem Absatz über den Talk-Kanal. In einem Text, in dem "Talk" ein Produktname ist, ist
"Talk to us" doppeldeutig. Die READMEs formulieren an derselben Stelle anders ("Happy to support
your organisation with evaluation and deployment"), die deutsche und die französische Fassung haben
das Problem nicht.
**Fix:** "Want to run this app in your organisation? Write to admin@infranode.dev"

---

_Reviewed: 2026-08-28T05:35:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
