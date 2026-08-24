---
phase: 10-mail-strikt-lesend-und-die-trifecta-grenze
plan: 07
subsystem: docs
tags: [sec-01, lethal-trifecta, prompt-injection, store-text, markertest, filtergrammatik, i18n, vokabular-gate]

# Dependency graph
requires:
  - phase: 10-mail-strikt-lesend-und-die-trifecta-grenze
    provides: "Plan 10-04: FILTER_TYPES, FLAG_VALUES, DEFAULT_LIMIT 20, MAX_LIMIT 50, die zwei Parserregeln"
  - phase: 10-mail-strikt-lesend-und-die-trifecta-grenze
    provides: "Plan 10-05: fetch(mail:<databaseId>), 32-KiB-Kappe, die metadata-Vertrauens-Signale"
  - phase: 10-mail-strikt-lesend-und-die-trifecta-grenze
    provides: "Plan 10-06: mail_browse registriert, README-Tabellenzeile und die Zahl 21 in README.md"
  - phase: 09-talk
    provides: "NC_MCP_TALK_SEND als Admin-Schalter des Ausgangskanals (TALK-04)"
provides:
  - "docs/privacy.md: Abschnitt 'The chain that mail closes' als lange Fassung der Kette"
  - "docs/faq.md: Nutzerfrage zum Senden/Loeschen von Mail, Adminfrage zum Schliessen des Ausgangskanals"
  - "README.md, README.de.md, README.fr.md: Mail-Abschnitt, Filtergrammatik-Tabelle, Trifecta-Absatz, vier Grenzen-Zeilen"
  - "appinfo/info.xml: Mail-Faehigkeit, Mail-ist-strikt-lesend-Satz und Ausgangskanal-Absatz in EN, DE und FR"
  - "Viertes Marker-Tripel im Manifest-Test: read only / nur lesen / lecture seule"
  - "test_no_description_names_a_blocked_mailbox: die Vokabular-Falle mit Begruendung eingefroren"
  - "CHANGELOG.md: ein ## [Unreleased]-Block ueber 0.1.7, ohne Versionsnummer"
affects: [10-08, phase-11-release, phase-11-store-submission]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ein Satz im Store-Text ohne Marker-Test verschwindet beim naechsten Textumbau; jeder neue Kernsatz bekommt ein Tripel"
    - "Eine Textfalle wird einmal als Test mit Begruendung festgehalten, statt bei jedem Umbau neu gegen einen roten Lauf gefunden zu werden"
    - "Ein Changelog-Eintrag fuer unveroeffentlichte Arbeit lebt in ## [Unreleased] und nie in einer Versionsnummer, die die Phase nicht ausliefert"
    - "Fachbegriff zitieren statt erfinden: die Kette heisst lethal trifecta, mit Link auf die Quelle"

key-files:
  created: []
  modified:
    - "docs/privacy.md"
    - "docs/faq.md"
    - "README.md"
    - "README.de.md"
    - "README.fr.md"
    - "appinfo/info.xml"
    - "tests/unit/test_exapp_env_setup.py"
    - "CHANGELOG.md"

key-decisions:
  - "Die drei Marker sind read only, nur lesen und lecture seule, genau wie 10-RESEARCH sie empfiehlt; sie stehen im bestehenden FAQ-Markertest als viertes Tripel statt in einem eigenen Test, weil die Aussageart dieselbe ist"
  - "Die Store-Beschreibung nennt Ebenen (Konten, Postfaecher, Nachrichten) und keine Postfachnamen: die uebliche Standardliste traegt das gesperrte Wort in allen drei Sprachen gleichzeitig"
  - "Der Trifecta-Text existiert in zwei Laengen: die lange Fassung in docs/privacy.md, eine gekuerzte in jedem der drei READMEs mit Link auf die lange; der Store-Text traegt nur den Ausgangskanal-Absatz, weil dort jede Zeile Platz vor einer Installationsentscheidung ist"
  - "Fassungsaussage und Sicherheitsversprechen sind im Text getrennt: 'Mail ist strikt lesend' ist die Faehigkeit, 'es gibt in dieser App keinen Weg, eine Mail zu senden' ist das Versprechen, und der Halter ist das Contract-Gate aus 10-06"
  - "Die Werkzeugzahlen stehen als Wort (ten tools, zehn Tools, dix outils), weil der Doku-Zaehlwaechter Ziffern vor dem Wort tools liest und eine Ziffer dort eine zweite Pflegestelle waere"
  - "README.de.md und README.fr.md haben die Zahl 20 auf 21 gezogen, an beiden Stellen (Kopf und Status); 10-06 hatte bewusst nur README.md angefasst"
  - "info.xml bekam keinen Versionssprung und keine Umstellung: Release ist Phase 11, die naechste Nummer 0.1.8"

patterns-established:
  - "Ein Doku-Absatz, den eine spaetere Phase wiederverwendet, steht woertlich in der Zusammenfassung, nicht nur als Verweis"

requirements-completed: [SEC-01, MAIL-01, MAIL-03]

# Metrics
duration: 13min
completed: 2026-08-24
---

# Phase 10 Plan 07: Die Kette benennen und die Familie dokumentieren, Zusammenfassung

**Die Exfiltrationskette steht jetzt in der Doku, in drei READMEs und in drei Store-Beschreibungen mit ihrem Namen da, samt Mechanismus, Gegenmassnahme und ehrlichem Rest, und drei Marker im Manifest-Test halten den Satz fest, dass Mail strikt lesend ist.**

## Performance

- **Duration:** 13 min
- **Started:** 2026-08-24T14:45:33Z
- **Completed:** 2026-08-24T14:58:36Z
- **Tasks:** 3
- **Files modified:** 8

## Accomplishments

- `docs/privacy.md` hat einen eigenen Unterabschnitt "The chain that mail closes" im
  Abschnitt "What leaves your control": die drei Zutaten mit ihrem Ort in diesem Server, der
  Begriff mit Link auf die Quelle, der Mechanismus Prompt Injection, fuenf Gegenmassnahmen
  mit ihrer Stelle und der ehrliche Rest.
- `docs/faq.md` hat zwei neue Frage-Antwort-Paare im Stil der bestehenden: eine Nutzerfrage
  ("Can the assistant send or delete my mail?", Antwort beginnt mit Nein) und eine
  Adminfrage ("I want to close the outgoing channel completely. What do I set?").
- Die drei READMEs tragen die Familie: Tabellenzeile, Mail-Abschnitt mit Filtergrammatik als
  Tabelle, erweiterte optionale Apps, eine Nichtsenden-Zeile, ein Trifecta-Absatz und vier
  Zeilen in den bekannten Grenzen.
- Die Store-Beschreibung sagt in EN, DE und FR, was Mail kann, dass Mail nur liest und dass
  es genau einen Ausgangskanal mit einem Admin-Schalter gibt, und ein Marker je Sprache
  macht den zweiten dieser Saetze pruefbar.
- Ein zweiter Test friert die Vokabular-Falle mit ihrer Begruendung ein, damit sie nicht beim
  naechsten Textumbau erneut gegen einen roten Lauf gefunden werden muss.
- `CHANGELOG.md` hat einen `## [Unreleased]`-Block ueber `## [0.1.7]`, mit `### Added` und
  `### Security`, ohne Versionsnummer und ohne gesperrtes Vokabular.

## Die drei Markertexte, die jetzt im Manifest geprueft werden

`test_every_description_carries_the_answer_of_the_faq` hat ein viertes Tripel. Das
Dictionary steht jetzt so da:

| Variante | Marker |
|----------|--------|
| ohne `lang` (Englisch) | `background`, `switch`, `disconnect`, **`read only`** |
| `lang="de"` | `Hintergrund`, `Schalter`, `trenn`, **`nur lesen`** |
| `lang="fr"` | `arrière-plan`, `interrupteur`, `déconnect`, **`lecture seule`** |

Die Zeilen, in denen die drei neuen Marker stehen (woertlich, fuer die naechste
Store-Einreichung):

- EN: `- **Mail is read only**: no way to send, to draft, to move, to flag or to delete a message`
- DE: `- **Mail nur lesen**: kein Weg, eine Nachricht zu senden, als Entwurf anzulegen, zu verschieben, zu markieren oder zu löschen`
- FR: `- **Mail en lecture seule** : aucun moyen d'envoyer, de rédiger un brouillon, de déplacer, de marquer ou de supprimer un message`

Der zweite neue Test heisst `test_no_description_names_a_blocked_mailbox` und behauptet fuer
jede der drei Varianten die Abwesenheit von `FORBIDDEN_VOCABULARY` im
Beschreibungstext, mit dem Grund im Docstring: die uebliche Aufzaehlung der Standardordner
eines Mailkontos traegt das Wort in allen drei Sprachen zugleich, deshalb nennt der Text
Ebenen. Die Doppelung zu `description_problems` ist bewusst: jene Funktion prueft das Wort
ueber das ganze Manifest, dieser Test nennt die Stelle und den Grund.

## Der Ausgangskanal-Absatz der Store-Beschreibung, woertlich

Er steht in allen drei Varianten unter der Liste "What it will not do", als eigener Absatz:

> Reading text written by strangers next to private data would be a chain if there were a
> way out. There is exactly one, sending a Talk message, and an administrator can close it
> for the whole instance. That is what the switch is for.

> Von Fremden geschriebenen Text neben privaten Daten zu lesen wäre eine Kette, wenn es einen
> Weg nach außen gäbe. Es gibt genau einen, das Senden einer Talk-Nachricht, und die
> Administration kann ihn für die ganze Instanz schließen. Dafür ist der Schalter da.

> Lire des textes écrits par des inconnus à côté de données privées formerait une chaîne s'il
> existait une sortie. Il en existe exactement une, l'envoi d'un message Talk, et un
> administrateur peut la fermer pour toute l'instance. C'est à cela que sert l'interrupteur.

Der Mail-Aufzaehlungspunkt bei den Faehigkeiten, ebenfalls woertlich:

- EN: `- **Mail**: read the accounts, the mailboxes of one, the messages of one, and the full text of a single message, with filters`
- DE: `- **Mail**: die Konten, die Postfächer eines Kontos, die Nachrichten eines Postfachs und den Volltext einer einzelnen Nachricht lesen, mit Filtern`
- FR: `- **Mail** : lire les comptes, les boîtes aux lettres de l'un d'eux, les messages de l'une d'elles et le texte complet d'un seul message, avec des filtres`

## Die Formulierung des Trifecta-Absatzes (Phase 11 verwendet sie wieder)

Die **README-Fassung**, englisch, als eigener Unterabschnitt direkt in "What this server
cannot do", vor "Known limitations":

> ### The chain this server has, and the switch that breaks it
>
> Reading mail completes a combination worth naming rather than describing. This server has
> access to **private data** (files, calendar, notes, contacts, Tables and now mail), it
> takes in **untrusted content** (a mail and a Talk message are written by somebody else, and
> for a mail that somebody needs no account on your instance at all), and it has exactly one
> **outgoing channel**, `talk_send`. Those three together are what Simon Willison calls the
> [lethal trifecta](https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/), and a
> language model does not reliably separate data from instructions, so a mail can carry a
> sentence meant for the model and the answer can take the way out.
>
> Two things stand against it here. `talk_send` sits behind the administration switch
> `NC_MCP_TALK_SEND`, which closes the outgoing channel for the whole instance while reading
> stays untouched. And **mail is read only**: this family adds reach, and deliberately no
> second way out. Neither makes prompt injection impossible. The long form, with every
> countermeasure and the honest remainder, is in [docs/privacy.md](docs/privacy.md), section
> "The chain that mail closes".

Die deutsche Ueberschrift lautet "Die Kette, die dieser Server hat, und der Schalter, der sie
bricht", die franzoesische "La chaîne que ce serveur possède, et l'interrupteur qui la brise".

Die **lange Fassung** in `docs/privacy.md` ist nach demselben Aufbau gegliedert und traegt
zusaetzlich: die nummerierte Liste der drei Zutaten, die fuenf Gegenmassnahmen (Schalter,
Mail strikt lesend, keine destruktiven Schreibpfade, Impersonation, Markerentfernung) und den
Absatz, der Faehigkeitsaussage und Sicherheitsversprechen trennt.

## Was in den drei READMEs neu oder erweitert ist

| Stelle | Aenderung |
|--------|-----------|
| Kopfzeile | Mail steht in der Aufzaehlung der Familien |
| Kopfabsatz und Status (nur DE und FR) | Zahl 20 auf 21 gezogen; README.md hatte 10-06 schon |
| Werkzeugtabelle | `mail_browse` mit `read` (DE und FR neu, EN aus 10-06) |
| **`### Mail`** (neu, zwischen Deck und der cloud-weiten Suche) | drei Ebenen mit Pflicht-Ids, Volltext ueber `fetch` mit `mail:<databaseId>` samt 32-KiB-Kappe und Vertrauens-Signalen, Filtergrammatik als Tabelle plus die zwei Parserregeln, das bewusst Fehlende |
| `### Optional apps` | Mail ergaenzt, neun auf **zehn** Tools, Mail-Fehlt-Satz, plus ein Absatz ueber den zweiten Erkennungsweg (Navigation statt Capabilities) und seine Kosten |
| `## What this server cannot do` | neue Zeile **No sending mail.**, die das Contract-Gate als Halter nennt |
| Trifecta-Unterabschnitt (neu) | gekuerzte Fassung mit Link auf `docs/privacy.md` |
| `## Known limitations` | eine erweiterte Zeile (optionale Apps, zehn Tools) und **drei neue**: Sekundengrenze des Cursors, fehlendes `body:`, nicht synchronisiertes Postfach und unerreichbarer Mailserver |

Die Filtergrammatik steht in allen drei Sprachen als Tabelle mit sieben Zeilen (`is:`, `not:`,
`from:`, `subject:`, `tags:`, `start:`, `end:`), je mit Beispiel, gefolgt von den zwei
Parserregeln (`%20` fuer das Leerzeichen, `%3A` fuer den Doppelpunkt), den Unix-Sekunden und
dem Grund fuer die Ablehnung eines unbekannten Typs.

## Task Commits

1. **Task 1: Die Kette in docs/privacy.md und docs/faq.md** - `077049f` (docs)
2. **Task 2: Die Familie in den drei READMEs, mit Filtergrammatik und Grenzen** - `a701ee5` (docs)
3. **Task 3: Store-Beschreibung in drei Sprachen, Markertest und Changelog** - `a2e555d` (docs)

## Files Created/Modified

- `docs/privacy.md` - Unterabschnitt "The chain that mail closes"; "What the app never does" um die Mail-Zeile erweitert
- `docs/faq.md` - eine Nutzerfrage und eine Adminfrage
- `README.md` - Kopfzeile, Mail-Abschnitt, optionale Apps, Nichtsenden-Zeile, Trifecta-Absatz, vier Grenzen-Zeilen
- `README.de.md` - dasselbe auf Deutsch, plus Tabellenzeile `mail_browse` und die Zahl 21 an zwei Stellen
- `README.fr.md` - dasselbe auf Franzoesisch, plus Tabellenzeile `mail_browse` und die Zahl 21 an zwei Stellen
- `appinfo/info.xml` - drei Beschreibungen ergaenzt (Faehigkeit, Nicht-Faehigkeit, Ausgangskanal-Absatz) und ein Kommentar, der die Vokabular-Regel erklaert; Elementreihenfolge und `version` unangetastet
- `tests/unit/test_exapp_env_setup.py` - viertes Marker-Tripel plus `test_no_description_names_a_blocked_mailbox`
- `CHANGELOG.md` - `## [Unreleased]`-Block mit `### Added` und `### Security`

## Decisions Made

Siehe `key-decisions` im Frontmatter. Die drei wichtigsten:

1. Der Trifecta-Text existiert in drei Laengen und nicht dreimal in derselben: lang in
   `docs/privacy.md`, gekuerzt mit Link in den READMEs, und im Store-Text nur der
   Ausgangskanal-Absatz. Ein Store-Leser entscheidet ueber eine Installation und liest
   keinen Aufsatz.
2. Die Werkzeugzahlen sind Woerter. Der Doku-Zaehlwaechter in
   `tests/contract/test_tool_surface.py` liest `(\d+)\s+tools`, also waere "10 tools" eine
   zweite Pflegestelle, die bei der naechsten Familie rot wird; "ten tools" nicht.
3. Die Store-Beschreibung nennt Ebenen statt Postfachnamen, und das steht ab jetzt als Test
   mit Begruendung da statt als Wissen in einem Plan.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Die Zahl 20 in README.de.md und README.fr.md**

- **Found during:** Task 2
- **Issue:** Der Plan nennt fuer die Uebersetzungen nur Tabellenzeile und Prosa. Beide
  Dateien trugen aber noch zweimal die Zahl 20 (Kopfabsatz "Die 20 Tools" und Status "Alle 20
  Tools"), und eine Uebersetzung, die eine falsche Werkzeugzahl behauptet, ist genau die
  Drift, gegen die der Zaehlwaechter im englischen README gebaut ist.
- **Fix:** Beide Stellen auf 21 gezogen, in beiden Dateien.
- **Files modified:** `README.de.md`, `README.fr.md`
- **Verification:** `grep` ueber alle drei READMEs findet keine 20er-Zahl mehr; das
  Pruefskript des Plans laeuft gruen.
- **Committed in:** `a701ee5`

**2. [Rule 2 - Missing Critical] Mail fehlte in der Kopfzeile aller drei READMEs**

- **Found during:** Task 2
- **Issue:** Der erste Satz jeder README zaehlt die Familien auf, die dieser Server
  verbindet, und Mail fehlte darin, obwohl die Werkzeugtabelle zwei Bildschirme weiter unten
  `mail_browse` fuehrt. Der Plan nennt die Zeile nicht, aber eine Aufzaehlung, die eine
  Familie auslaesst, ist die erste Zeile, die ein Leser sieht.
- **Fix:** Mail in die Aufzaehlung, in allen drei Sprachen.
- **Files modified:** `README.md`, `README.de.md`, `README.fr.md`
- **Verification:** `uv run pytest tests/contract/test_tool_surface.py -q` gruen.
- **Committed in:** `a701ee5`

**3. [Rule 3 - Blocking] `mail_browse` musste woertlich in den Changelog-Block**

- **Found during:** Task 3
- **Issue:** Das Pruefskript des Plans verlangt `mail_browse` im `## [Unreleased]`-Block. Der
  Changelog dieses Projekts nennt sonst keine Werkzeugnamen, sondern beschreibt in Prosa, was
  ein Assistent kann; der erste Entwurf folgte dieser Form und war damit rot.
- **Fix:** Der erste `### Added`-Punkt nennt den Namen einmal ("with one tool called
  `mail_browse`") und bleibt im Uebrigen Prosa.
- **Files modified:** `CHANGELOG.md`
- **Verification:** Das Changelog-Pruefskript des Plans laeuft gruen.
- **Committed in:** `a2e555d`

---

**Total deviations:** 3 auto-fixed (2 missing critical, 1 blocking)
**Impact on plan:** Keine Ausweitung des Umfangs. Zwei Korrekturen betreffen Zahlen und eine
Aufzaehlung in den Uebersetzungen, die dritte ist eine Formulierung im Changelog.

## Issues Encountered

Keine. Alle Gates waren beim ersten vollstaendigen Lauf gruen, mit Ausnahme der oben
genannten Changelog-Zeile, die das Pruefskript des Plans wie vorgesehen gefunden hat.

## Known Stubs

Keine. Dieser Plan ist Textarbeit plus zwei Testaenderungen; `git diff --stat` zeigt keine
Aenderung an `src/mcp_connector/`, an `pyproject.toml` oder an `uv.lock`.

## Threat Flags

Keine neue Angriffsflaeche: kein Endpunkt, kein Auth-Pfad, kein Dateizugriff und keine
Schema-Aenderung. Die Aenderungen dieses Plans sind Text und ein Test.

## User Setup Required

None. Der genannte Schalter `NC_MCP_TALK_SEND` existiert seit Phase 9 und ist unveraendert;
dieser Plan beschreibt ihn nur dort, wo ein Administrator ihn liest.

## Next Phase Readiness

- **Plan 10-08** kann den Abnahmelauf fahren; an Text ist nichts mehr offen.
- **Phase 11, Release:** `appinfo/info.xml` traegt weiterhin `0.1.7`, der Changelog-Eintrag
  liegt in `## [Unreleased]`. Beim Release wandert die Ueberschrift auf die neue Nummer
  (**0.1.8**, weil 0.1.6 und 0.1.7 im Store bereits stehen und die Release-Nummer der Roadmap
  ueberholt ist), und `version` sowie `image-tag` steigen gemeinsam.
- **Phase 11, Store-Einreichung:** die drei Markertexte und der Ausgangskanal-Absatz stehen
  oben woertlich, ebenso die Regel, dass die Beschreibung Ebenen und keine Postfachnamen
  nennt. Der Trifecta-Absatz der README ist die Kurzfassung, die in eine Ankuendigung passt.

## Self-Check: PASSED

Alle acht geaenderten Dateien liegen auf der Platte, die drei Commits (`077049f`, `a701ee5`,
`a2e555d`) stehen im Log. Gates am Planende: `uv run pytest -q`,
`uv run pytest tests/contract/test_tool_surface.py -q`,
`uv run pytest tests/unit/test_exapp_env_setup.py -q`, `uv run ruff check .`,
`uv run ruff format --check .` und `uv run pyright` alle gruen; die drei Pruefskripte des
Plans (Doku, READMEs, Changelog), die Marker-Gegenprobe ueber `lxml` und die
Versionszeilen-Behauptung ueber `git diff` ebenfalls.

---
*Phase: 10-mail-strikt-lesend-und-die-trifecta-grenze*
*Completed: 2026-08-24*
