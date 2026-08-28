---
phase: 15
slug: release-0-1-10
status: verified
threats_open: 0
asvs_level: 1
created: 2026-08-28
register_authored_at_plan_time: true
block_on: high
---

# Phase 15 — Security

> Per-Phase-Sicherheitsvertrag: Threat-Register, akzeptierte Risiken, Audit-Trail.
> Geprüft wurde gegen den Arbeitsbaum, gegen den getaggten Stand `v0.1.10` (`156280f`),
> gegen die veröffentlichten Bytes des Assets und gegen die Live-Systeme
> (GitHub Releases, ghcr.io, apps.nextcloud.com). Dokumentation allein galt nicht als Beleg.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Arbeitsbaum zu Git-Tag | Der Tag löst `release.yml` aus und ist irreversibel | Versionszeichenketten, Store-Texte |
| Repo-Text zu veröffentlichtem Artefakt | Was im Tag steht, reist unveränderlich im signierten Tarball | `appinfo/info.xml`, `CHANGELOG.md`, `README.md`, `LICENSE` |
| Lokal gebautes Archiv zu veröffentlichtem Asset | Zwei verschiedene Bytefolgen; nur die zweite darf signiert werden | tar.gz-Bytes, sha256 |
| Automat zu Mensch | Die Owner-Freigabe ist die eine Entscheidung, die kein Kommando ersetzt | Freigabewort, Weg für Schritt 7 |
| Privater Signierschlüssel und Store-Token zu Repo | Schlüssel liegt außerhalb des Arbeitsbaums, Token bleibt im Browser | Schlüsselmaterial, Base64-Signatur |
| Veröffentlichtes Asset zu AppAPI-Installationen | Administratoren installieren von der Release-URL, nicht aus dem Store | Asset-URL, Content-Length |
| Nachweistabelle zu Leser | Einziger Beleg für die Sorgfalt des Releases; Richtung ist Ereignis, dann Zeile | Datum, Behauptung, Befehl |

---

## Threat Register

Register aus den `<threat_model>`-Blöcken der Pläne 15-01 bis 15-04, plus eine
Register-Ergänzung (`T-15-PT`) für die nach dem Tag entstandenen Änderungen, deren
Disposition im Audit-Auftrag ausdrücklich benannt wurde.

| Threat ID | Category | Component | Disposition | Mitigation | Evidence (verifiziert) | Status |
|-----------|----------|-----------|-------------|------------|------------------------|--------|
| T-15-01 | Tampering | Die sechs Versionsstellen | mitigate | Grep je Stelle, Manifest-Gate, zweite Prüfung in `release.yml` | `pyproject.toml:3`, `src/mcp_connector/__init__.py:7`, `appinfo/info.xml` `<version>`/`<image-tag>`, `README.md:27`, `README.de.md:29`, `README.fr.md:31`, `uv.lock:472` tragen alle `0.1.10`; kein `0.1.9`-Rest in den sieben Dateien (rc=1); `tests/unit/test_exapp_env_setup.py` am HEAD grün (153 Tests); `.github/workflows/release.yml:47-53` bricht bei Tag-Ungleichheit mit Exit 1 ab | closed |
| T-15-02 | Denial of Service | Git-Tag v0.1.10 (Plan 01) | mitigate | Plan 01 erzeugt keinen Tag | `v0.1.10` zeigt auf `156280f`, einen Commit aus Plan 15-03 (`docs(15-03): proof row for the branch push`), also nach `c80a45c` und `9829f1e` | closed |
| T-15-03 | Tampering | Nutzlast in `appinfo/info.xml` und den READMEs | mitigate | Gekürzter Enterprise-Text nicht neu formuliert, Diff auf die Versionszeilen begrenzt | `git diff -U0 c80a45c^ c80a45c -- appinfo/info.xml` zeigt genau vier Zeilen: `<version>` und `<image-tag>`, keine `<summary`-, `<description`-, `Enterprise`- oder `<default`-Zeile | closed |
| T-15-04 | Denial of Service | `appinfo/info.xml`, leeres Element | mitigate | Beschreibungs- und Variablenblöcke unangetastet, ElementTree-Parse | `xml.etree.ElementTree.parse` läuft fehlerfrei; einziges kindloses Element ist `<nextcloud min-version="32" max-version="34"/>` (`:235`), also attributtragend und nicht die 500-Klasse; Store-Upload antwortete 201 und der Katalog listet `0.1.10` | closed |
| T-15-05 | Repudiation | `CHANGELOG.md` | mitigate | Nur belegte, nutzersichtbare Einträge; Paarung als Mengengleichheit | 11 Abschnitte gegen 11 Linkdefinitionen, `grep -c 'Unreleased'` gibt 0, Block `## [0.1.10] - 2026-08-28` über `## [0.1.9] - 2026-08-25`; im veröffentlichten Asset genau ein `## [0.1.10]` | closed |
| T-15-06 | Tampering | Zeilenenden der vier CRLF-Dateien | mitigate | Byte-exaktes Patchen per Python rb/wb | CRLF-Zahlen am HEAD gemessen: `README.md` 536, `README.de.md` 551, `README.fr.md` 570, `appinfo/info.xml` 540, exakt die deklarierten Werte; `CHANGELOG.md` und `docs/store-submission.md` je 0 CRLF | closed |
| T-15-SC/01 | Tampering | `uv.lock`, `pyproject.toml` Dependencies | mitigate | Kein Lock-Lauf, kein Paketmanager, Diff ohne Dependency-Zeile | `git diff -U0 v0.1.9..HEAD -- pyproject.toml uv.lock` zeigt ausschließlich die zwei Paare `-version = "0.1.9"` / `+version = "0.1.10"`; kein Fremdpaketname, keine `dependencies`- oder `requires-dist`-Zeile | closed |
| T-15-07 | Tampering | `dist/mcp_connector-0.1.10.tar.gz` | mitigate | Probelauf als Strukturprüfung benannt, Skript-Signatur ist Diagnose | Selbst nachgemessen: lokal 47299 Bytes / sha256 `4682e06d…`, veröffentlicht 46973 Bytes / sha256 `4236d2e8…`, zwei verschiedene Bytefolgen; Proof-Zeile 148 nennt "structure check" und sagt, dass der lokale Bau nicht signiert wird | closed |
| T-15-08 | Tampering | Gate-Grenzwerte | mitigate | Grenzwerte auf der v1.2-Messung, Abweichung als Befund | `git diff v0.1.9..HEAD -- scripts/check_tool_budget.py tests/contract/test_tool_surface.py` ist leer; `BUDGET_BYTES = 18_000` (`:83`), `MAX_TOOL_BYTES = 1400` (`:117`); die Abweichung 15711 zu 15712 ist in 15-02-SUMMARY und Proof-Zeile 148 als serverInfo-Versionszeichenkette benannt und gegengeprüft | closed |
| T-15-09 | Repudiation | `docs/store-submission.md` Schritte 1 bis 3 | mitigate | Nur Zeilen für eingetretene Ereignisse, Form Datum plus Behauptung plus Befehl | Zeilen 146, 147, 148 tragen `2026-08-27 23:20Z`, `23:22Z`, `23:34Z` mit Kommandos in Spalte 3; die Uhrzeiten 23:20Z und 23:22Z sind die Commit-Zeitpunkte von `c80a45c` und `9829f1e`, also die Ereigniszeiten | closed |
| T-15-10 | Denial of Service | Git-Tag v0.1.10 (Plan 02) | mitigate | Plan 02 erzeugt keinen Tag | Der Tag zeigt auf `156280f`, das nach dem Plan-02-Commit `4be5129` liegt | closed |
| T-15-11 | Tampering | Fünfte Versionsstelle im Tarball | mitigate | Archiv-README vor dem Tag gegen `^Version 0\.1\.10\.` geprüft | Im heruntergeladenen, veröffentlichten Asset zählt `mcp_connector/README.md` genau einmal `^Version 0\.1\.10\.`; die 0.1.8-Panne (veröffentlicht als 0.1.7) wiederholt sich nicht | closed |
| T-15-12 | Information Disclosure | `dist/` im Arbeitsbaum | accept | `dist/` gitignored, nichts daraus committet | `git check-ignore -v` nennt `.gitignore:17 dist/`; `git ls-files dist` ist leer; siehe Accepted Risks R-15-01 | closed |
| T-15-13 | Denial of Service | Tag vor der Owner-Freigabe | mitigate | Blockierender Checkpoint, `autonomous: false`, Tag nur bei `freigeben` | Der Tag-Push löste den Lauf `33142956284` mit `event: push`, `headBranch: v0.1.10`, `createdAt 2026-08-28T04:50:07Z` aus, also nach der in 15-03-SUMMARY protokollierten Freigabe von `2026-08-28T04:49Z`; der getaggte Commit `156280f` ist selbst die Proof-Zeile, die die Abwesenheit des Tags behauptet. Evidenzgrenze: der Freigabezeitpunkt selbst ist nur durch das Executor-Protokoll belegt, nicht durch ein unabhängiges Kanalartefakt | closed |
| T-15-14 | Tampering | Tag-Name | mitigate | Name wörtlich `v0.1.10`, Gleichheitsprüfung in `release.yml`, kein Milestone-Tag | `git tag --list 'v0.1.1*'` gibt nur `v0.1.1` und `v0.1.10`; `git ls-remote --tags origin v0.1.10` nennt `156280fea850c7df6360b10bacbe6a256f0300f7`; 15 Tags lokal; kein `v1.4` entstanden | closed |
| T-15-15 | Denial of Service | Release-Asset und Tag-Historie | mitigate | Kein Delete-Asset, kein `git tag -f`, kein Force-Push | Lokaler und remote Tag zeigen auf denselben Commit; `gh release list` nennt genau ein `v0.1.10`; das Asset antwortet 302 dann 200 mit `Content-Length: 46973`; ghcr.io führt alle elf Tags `0.1.0` bis `0.1.10` | closed |
| T-15-16 | Tampering | Nicht gepushter Stand unter einem Tag | mitigate | `git log origin/main..HEAD` gleich 0 vor der Tag-Entscheidung | `git merge-base --is-ancestor 156280f origin/main` ist wahr; Proof-Zeile 149 (23:42Z) entstand und wurde gepusht, bevor der Tag existierte | closed |
| T-15-17 | Repudiation | Proof-Zeile Schritt 4 und 5 | mitigate | Zeile erst nach grünem Lauf, mit Run-Id, Job, Laufzeit, Exit-Code, Freigabezeitpunkt | Zeilen 149 (23:42Z) und 150 (04:53Z); `gh run view 33142956284` gibt `conclusion: success`, `startedAt 04:50:07Z`, `updatedAt 04:51:55Z`; Asset 46973 Bytes, `isDraft` false. Residual (Info): Zeile 150 nennt 04:51:55Z als Veröffentlichungszeitpunkt, die Release-API nennt `publishedAt 04:51:46Z` (Review IN-05, nicht behoben) | closed |
| T-15-18 | Repudiation | Changelog-Datum | mitigate | Datumszeile gegen den Kalendertag des Tags geprüft | `## [0.1.10] - 2026-08-28` gegen Tag-Entstehung am `2026-08-28 04:50Z`; die Zeile stimmt in UTC und in Europe/Berlin | closed |
| T-15-SC/03 | Tampering | Build im Workflow | transfer | Image und Archiv entstehen im GitHub-Workflow aus dem getaggten Quellstand, nicht lokal hochgeladen | Transferdokumentation vorhanden und geprüft: `.github/workflows/release.yml:74-88` baut per `docker/build-push-action@v7` für `platforms: linux/amd64,linux/arm64`, ruft `scripts/build_store_release.sh` im Job `publish` und hängt das Asset per `softprops/action-gh-release@v3` an; Lauf `33142956284` grün. Residual: die Actions sind auf bewegliche Major-Tags gepinnt (`@v7`, `@v4`, `@v3`), nicht auf Commit-SHAs | closed |
| T-15-19 | Tampering | Signatur über das falsche Artefakt | mitigate | Nur die per `curl -sSLO` geholte Datei signiert, Gegenprobe mit `openssl dgst -sha512 -verify` | Stärkster Beleg unabhängig nachgemessen: der Store hat `0.1.10` angenommen und listet es, und der Store prüft die Signatur gegen die Bytes, die er von der Release-URL lädt. Diese Bytes sind sha256 `4236d2e864470ed2b3b6e9e485d6cf3f60e130cc500e3ffdde9a436216f8865d`, 46973 Bytes, und damit nicht der lokale Bau `4682e06d…` / 47299 Bytes. Proof-Zeile 151 hält beide Größen, beide sha256-Präfixe und `Verified OK` fest | closed |
| T-15-20 | Information Disclosure | Privater Schlüssel und Store-Token | mitigate | Schlüssel nicht kopiert, Token nicht im Repo, Greps ohne Treffer | `grep -rn 'BEGIN PRIVATE KEY\|BEGIN RSA PRIVATE KEY' docs .planning` trifft ausschließlich die wörtlichen Muster-Selbstzitate in 13-06-PLAN.md, 13-06-SUMMARY.md, 13-SECURITY.md und 15-04-PLAN.md, kein Schlüsselmaterial; `grep -rniE '(NC_STORE_TOKEN=\|Authorization: Token [A-Za-z0-9])' docs .planning` ebenso nur Selbstzitate ohne Wert; `git status --short` leer, keine `.sig`-, `.pem`- oder `.tar.gz`-Datei im Repo-Wurzelverzeichnis | closed |
| T-15-21 | Information Disclosure | Base64-Signatur in einem Commit | mitigate | Signatur nie aufgeschrieben, keine langen Base64-Ketten im Commit | Jeder Commit `v0.1.9..HEAD` gegen `^\+[A-Za-z0-9+/]{100,}={0,2}$` geprüft: kein Treffer | closed |
| T-15-22 | Denial of Service | Store-Upload antwortet 500 | mitigate | Manifest-Gates plus ElementTree-Parse vor dem Upload | Upload antwortete 201 (Proof-Zeile 152); `curl` auf `api/v1/appapi_apps.json` listet `mcp_connector` mit 11 Releases inklusive `0.1.10`; kein leeres Textelement im Manifest | closed |
| T-15-23 | Denial of Service | Zweites Release wegen Cache-Versatz | mitigate | 201 ist die Annahme, kein Nachrelease | `gh release list` nennt genau ein `v0.1.10`; Store-Katalog zählt 11 Releases, kein zweiter 0.1.10-Versuch | closed |
| T-15-24 | Denial of Service | Gelöschtes Asset, umgeschriebener Tag | mitigate | `curl -I`-Nachweis ist Pflicht, kein Löschen, kein Force | Asset live erreichbar: 302 dann 200, `Content-Length: 46973`; ghcr.io-Tagliste vollständig mit elf Tags; Tag lokal gleich remote | closed |
| T-15-25 | Repudiation | Proof-Zeilen der Schritte 6 bis 8 | mitigate | Jede Zeile nach ihrem Ereignis, mit Datum, Zahl oder Statuscode und Befehl; Datumsspalte aufsteigend | Zeilen 151 (05:00Z), 152 (05:02Z), 153 (05:18Z) vorhanden; 67 datierte Zeilen, Spalte durchgehend aufsteigend, keine Verletzung; WR-01 (vierter Nachweis von Schritt 8 war eine lokale Git-Abfrage) ist in `901b294` korrigiert, und ich habe den echten Registry-Nachweis selbst geführt: `ghcr.io/v2/.../tags/list` gibt elf Tags inklusive `0.1.10` | closed |
| T-15-26 | Tampering | Fehlzählung durch das Präfix 0.1.1 | mitigate | Verankerte Muster, Sortierfalle im Plan benannt | Eigene Prüfungen als Mengenzugehörigkeit statt Reihenfolge geführt: Katalog 11 Releases mit `0.1.10` enthalten, Registry elf Tags mit `0.1.10` enthalten; 15-04-SUMMARY benennt die Sortierfalle ausdrücklich | closed |
| T-15-SC/04 | Tampering | Herkunft des veröffentlichten Images | transfer | Nachweise über OCI-Index und Tagliste bei ghcr.io, kein eigener Build hochgeladen | Transferdokumentation vorhanden und live gegengeprüft: OCI-Index zu `0.1.10` nennt `linux/amd64` und `linux/arm64` (dazu zwei `unknown/unknown`-Einträge, die Buildx-Attestierungen sind); Tagliste elf Tags; das Asset ist byte-identisch zum getaggten Quellstand, siehe T-15-PT | closed |
| T-15-PT | Repudiation | Aktenkundigkeit der Post-Tag-Änderungen in `docs/store-submission.md:154-155` | mitigate | Post-Tag-Drift vollständig und reproduzierbar in der Nachweistabelle: drei Commits an `appinfo/info.xml` inklusive `<author>`-Wechsel plus die `CHANGELOG.md`-Abweichung | **Erfüllt nach zwei Nachbesserungen** (`560e2e3`, `86c0f55`). Alle vier Belege der 06:05Z-Zeile nachgefahren und zutreffend; die 05:40Z-Zeile ist auf ihre Minute eingeschränkt und fährt gegen den Stand nach, den sie nennt (`778b594`). Zeilen 151 und 155 zählen `admin@infranode.dev` im Asset jetzt beide mit drei, der Widerspruch ist weg. Prüfprotokoll unten | closed |

*Status: open · closed*
*Disposition: mitigate (Implementierung nötig) · accept (dokumentiertes Risiko) · transfer (Dritte)*

### Sonderprüfung 1: Hat eine Post-Tag-Änderung das ausgelieferte Artefakt verfälscht?

Nein, und das ist nicht plausibel, sondern gemessen.

- `mcp_connector/appinfo/info.xml` aus dem heruntergeladenen, veröffentlichten Asset ist
  byte-identisch zu `git show v0.1.10:appinfo/info.xml` (`diff -q` ohne Unterschied).
- Das Asset trägt weiter den langen Trifecta-Absatz ("would be a chain if there were a way
  out", 1 Treffer) und nicht die Kürzung aus `b3267cd` ("reads text that strangers wrote",
  0 Treffer).
- Das Asset trägt `<author mail="k.cherif@outlook.de">`, also den Stand vor `deafbf4`.
- Tag lokal und remote unverändert auf `156280f`, genau ein Release, Asset live erreichbar
  mit unveränderten 46973 Bytes und sha256 `4236d2e8…`.

Die Post-Tag-Änderungen berühren ausschließlich den Arbeitsbaum. Der Store liefert
korrekterweise weiter den 0.1.10-Stand aus. Der Preis ist ein Repo-zu-Asset-Drift in zwei
Dateien (`appinfo/info.xml`, `CHANGELOG.md`), dessen Aktenkundigkeit unvollständig ist:
siehe T-15-PT.

### Sonderprüfung 2: Ist SEC-01 im gekürzten Text weiter erfüllt?

Ja, in beiden Ständen.

SEC-01 (`.planning/milestones/v1.2-REQUIREMENTS.md:53`) verlangt drei Dinge: einen
Doku-Abschnitt, der Mail- und Talk-Inhalte als fremde Daten und die Exfiltrationskette beim
Namen nennt, einen Verweis auf den TALK-04-Schalter, und den Mail-ist-strikt-lesend-Satz in
der Store-Beschreibung in EN, DE und FR.

- Doku-Abschnitt und Schalterverweis: `docs/privacy.md:106` nennt die lethal trifecta samt
  Quelle, `:116` die Exfiltration, `:121` und `:154` den Schalter `NC_MCP_TALK_SEND`.
  `git log v0.1.9..HEAD -- docs/privacy.md` ist leer, die Datei wurde in dieser Phase nicht
  angefasst.
- Mail-ist-lesend-Satz am HEAD in allen drei Sprachen: `appinfo/info.xml:65`
  ("Mail is read only"), `:110` ("Mail nur lesen"), `:157` ("Mail en lecture seule").
- Der gekürzte Absatz nennt weiter alle vier Teile der Kette: fremde Texte, Talk als einzigen
  direkten Ausgang, den Admin-Schalter und geteilte Ablagen als Restweg (EN `:68`, DE `:113`,
  FR `:160`).
- Der Restweg-Fehler aus Review WR-03 (nur "shared folder", obwohl eine Deck-Karte in einem
  Board und eine Tables-Zeile in einer Tabelle landet) ist in `901b294` behoben, allerdings
  anders als im Review vorgeschlagen: der Satz ist auf "somewhere you share with others"
  beziehungsweise "dort, wo Sie mit anderen teilen" und "là où vous partagez avec d'autres"
  verallgemeinert. Die falsche Verengung ist damit weg, die Aussage bleibt richtig.
- Das ausgelieferte 0.1.10-Asset trägt ohnehin die lange, stärkere Fassung.

Manifest-Gate am HEAD grün: `uv run --no-sync pytest tests/unit/test_exapp_env_setup.py -q`,
153 Tests bestanden.

---

## Unregistered Flags

Keines der vier SUMMARY-Dokumente trägt einen Abschnitt `## Threat Flags`. Neue
Angriffsfläche wurde vom Executor also nicht deklariert; die Vollständigkeit des Registers
ruht allein auf der Planungszeit (`register_authored_at_plan_time: true`). Die folgenden
Punkte sind während der Umsetzung aufgetaucht und in keinem der vier Register abgebildet.

| Flag | Beobachtung | Bewertung |
|------|-------------|-----------|
| UF-01 | `<author mail="...">` in `appinfo/info.xml` ist öffentliche Store-Oberfläche und war in keinem der vier Threat-Register erfasst. Live gemessen: `authors: [{'mail': 'k.cherif@outlook.de'}]` im Katalogeintrag, und das unveränderliche 0.1.10-Asset trägt dieselbe Adresse. Zusätzlich `pyproject.toml:7`. Aufgetaucht erst im Code-Review als WR-02 | WARNING, kein Blocker. Owner-Entscheid vom 2026-08-28: Wechsel auf `admin@infranode.dev` (`deafbf4`), sichtbar im Store mit 0.1.11. Bis dahin akzeptiertes Restrisiko R-15-02 |
| UF-02 | Kein `## Threat Flags`-Abschnitt in 15-01 bis 15-04-SUMMARY | WARNING, kein Blocker. Für die Folgephase: Abschnitt auch dann setzen, wenn er "keine" sagt, damit die Abwesenheit belegt ist und nicht angenommen werden muss |

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| R-15-01 | T-15-12 | `dist/` liegt im Arbeitsbaum und hält gebaute Archive aus öffentlichem Quellcode. Kein Geheimnis, kein Nutzerdatum. `.gitignore:17` hält das Verzeichnis draußen, `git ls-files dist` ist leer | Plan 15-02 (Disposition accept) | 2026-08-28 |
| R-15-02 | UF-01 | Die private Adresse `k.cherif@outlook.de` steht bis zum Release 0.1.11 im öffentlichen `authors`-Feld des Store-Katalogs und unveränderlich im 0.1.10-Asset. Eine Korrektur am Asset ist unmöglich (immutable), ein Sonderrelease nur dafür wurde als unangemessen bewertet. Der Repo-Stand ist per `deafbf4` schon gewechselt | Owner-Entscheid, festgehalten in 15-REVIEW.md WR-02 | 2026-08-28 |
| R-15-03 | T-15-SC/03 | Die GitHub Actions des Release-Workflows sind auf bewegliche Major-Tags gepinnt (`actions/checkout@v7`, `docker/build-push-action@v7`, `softprops/action-gh-release@v3`), nicht auf Commit-SHAs. Bei ASVS Level 1 und Disposition `transfer` als Restrisiko getragen; ein SHA-Pinning ist Kandidat für den Tech-Debt-Backlog | Auditor-Feststellung, Bestätigung durch Owner offen | 2026-08-28 |

*Akzeptierte Risiken tauchen in künftigen Audit-Läufen nicht wieder auf.*

---

## Open Threats

Keine. T-15-PT war in zwei Läufen offen und ist im dritten geschlossen; die Historie steht
unten, weil ein geschlossener Befund ohne seinen Weg nicht nachprüfbar ist.

### Prüfprotokoll T-15-PT, Zeile für Zeile

Geprüfter Stand: `560e2e3` ("the post-tag drift in full, the 05:40Z row bounded to its
minute"). Alle vier Belege der neuen 06:05Z-Zeile wurden nachgefahren.

| Beleg der 06:05Z-Zeile | Nachgefahren | Ergebnis |
|------------------------|--------------|----------|
| "`git log --oneline v0.1.10..HEAD -- appinfo/info.xml` names `b3267cd`, `901b294` and `deafbf4`" | ebenso | **stimmt**, genau diese drei Commits, keine weiteren |
| "`git log --oneline v0.1.10..HEAD -- CHANGELOG.md` names `901b294`" | ebenso | **stimmt**, genau ein Commit |
| "touches the three `<description>` blocks and the one `<author>` line and no `<version>` or `<image-tag>` line" | `git diff -U0 v0.1.10..HEAD -- appinfo/info.xml` | **stimmt**: die drei geänderten Prosazeilen sind die EN-, DE- und FR-Trifecta-Absätze, dazu genau ein `<author>`-Paar (`k.cherif@outlook.de` zu `admin@infranode.dev`); Grep auf `<version>` und `<image-tag>` im Diff ohne Treffer (rc=1) |
| "`tar -xzOf` ... is byte identical to `git show v0.1.10:appinfo/info.xml`, counting the long paragraph once and `admin@infranode.dev` zero times" | `cmp` beider Dateien; `grep -c` je Muster | **halb falsch im zweiten Lauf**, korrigiert in `86c0f55`, siehe den Abschnitt darunter. Byte-Identität und langer Absatz stimmten, die Zählung nicht |

Zusätzlich geprüft und in Ordnung: die auf ihre Minute eingeschränkte 05:40Z-Zeile fährt
gegen den Stand nach, den sie nennt. `git log --oneline v0.1.10..778b594 -- appinfo/info.xml`
(778b594 war HEAD um 05:40Z) nennt genau die zwei Commits, und der Diff enthält null
`<author>`-Zeilen. Die Einschränkung ist also nicht nur behauptet, sondern zutreffend, und
der Vorwärtsverweis auf die Folgezeile steht. Restpunkt ohne Threat-Bezug: die 05:40Z-Zeile
sagt "both only in the three store descriptions", obwohl `901b294` schon zu diesem Zeitpunkt
auch `CHANGELOG.md` berührte; die 06:05Z-Zeile trägt das mit "superseding the count in the
row above" nach, womit der Drift in der Tabelle vollständig aktenkundig ist.

### Dritter Lauf: der korrigierte vierte Beleg

Geprüfter Stand `86c0f55` ("the fourth proof counts what it measures"), ein Commit mit einer
geänderten Zeile in `docs/store-submission.md` und keiner weiteren Datei. Der Halbsatz lautet
jetzt: "counting the long paragraph once, the `<author mail>` attribute as the old
`k.cherif@outlook.de` and `admin@infranode.dev` three times, which is the enterprise contact
in the English, German and French description and the payload this release exists for".

Nachgefahren gegen die frisch heruntergeladenen Bytes (sha256
`4236d2e864470ed2b3b6e9e485d6cf3f60e130cc500e3ffdde9a436216f8865d`, 46973 Bytes):

| Teilbehauptung | Messung | Ergebnis |
|----------------|---------|----------|
| byte identical zu `git show v0.1.10:appinfo/info.xml` | `cmp` | ohne Unterschied |
| langer Absatz einmal | `grep -c 'would be a chain if there were a way out'` | 1 |
| `<author mail>` als altes `k.cherif@outlook.de` | `grep -c '<author mail="k.cherif@outlook.de"'` gleich 1, `grep -c '<author mail="admin@infranode.dev"'` gleich 0 | stimmt |
| `admin@infranode.dev` dreimal, Enterprise-Kontakt in EN, DE und FR | `grep -c` gleich 3, Fundstellen `:79` (EN), `:124` (DE), `:171` (FR), jede im Enterprise-Kontaktsatz | stimmt |

Die drei übrigen Belege der Zeile halten am neuen HEAD unverändert: drei Commits an
`appinfo/info.xml`, einer an `CHANGELOG.md`, ein `<author>`-Paar im Diff, keine `<version>`-
oder `<image-tag>`-Zeile (rc=1). Querprobe über die Tabelle: Zeile 151 und Zeile 155 zählen
`admin@infranode.dev` im Asset jetzt beide mit drei, der Widerspruch aus dem zweiten Lauf ist
aufgelöst. Damit trägt die Nachweistabelle den Post-Tag-Drift vollständig, in der richtigen
Beweisrichtung und mit Befehlen, die ihr eigenes Ergebnis wiedergeben. **T-15-PT geschlossen.**

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-08-28 | 30 | 29 | 1 | gsd-security-auditor (Erstlauf, Stand `c12eab5`) |
| 2026-08-28 | 30 | 29 | 1 | gsd-security-auditor (Nachprüfung nur T-15-PT, Stand `560e2e3`) |
| 2026-08-28 | 30 | 30 | 0 | gsd-security-auditor (Nachprüfung nur T-15-PT, Stand `86c0f55`) |

**Nachtrag zum zweiten Lauf.** Geprüft wurde ausschließlich T-15-PT. Die Nachbesserung
`560e2e3` schloss den ursprünglichen Befund fast vollständig: Commit-Zählung, zweite
betroffene Datei, `<author>`-Wechsel und die Einschränkung der 05:40Z-Zeile waren korrekt und
nachfahrbar. Offen blieb ein falscher Zählwert im vierten Beleg der neuen Zeile.

**Nachtrag zum dritten Lauf.** Geprüft wurde ausschließlich der korrigierte Halbsatz aus
`86c0f55`. Alle vier Teilbehauptungen fahren gegen die veröffentlichten Bytes nach, die drei
übrigen Belege der Zeile halten unverändert, und die Querprobe gegen Zeile 151 ist
widerspruchsfrei. T-15-PT ist geschlossen, `threats_open` steht auf 0, `status` auf
`verified`. Der Rest des Registers wurde in den Läufen zwei und drei nicht neu auditiert und
behält die Belege des Erstlaufs (Stand `c12eab5`); die Nachbesserungen `560e2e3` und
`86c0f55` berühren ausschließlich `docs/store-submission.md` und damit keinen anderen
Threat-Beleg.

Register: 26 numerierte Threats (T-15-01 bis T-15-26), drei Instanzen von `T-15-SC`
(Pläne 01, 02, 03, 04, wobei die Pläne 01 und 02 dieselbe Lieferketten-Disposition
`mitigate` tragen und hier als `T-15-SC/01` zusammengefasst sind, die Pläne 03 und 04 je
`transfer`), plus die Register-Ergänzung `T-15-PT`.

---

## Sign-Off

- [x] Alle Threats haben eine Disposition (mitigate / accept / transfer)
- [x] Akzeptierte Risiken im Accepted Risks Log dokumentiert (R-15-01, R-15-02, R-15-03)
- [x] `threats_open: 0` bestätigt
- [x] `status: verified` in der Frontmatter gesetzt

Offen, aber ohne Blockerwirkung und ausdrücklich getragen: die zwei Unregistered Flags
UF-01 (`<author mail>` als öffentliche Store-Oberfläche, sichtbar bereinigt mit 0.1.11) und
UF-02 (kein `## Threat Flags`-Abschnitt in den vier SUMMARY-Dokumenten), sowie R-15-03
(Action-Pinning auf bewegliche Major-Tags), dessen Owner-Bestätigung noch aussteht.

**Approval:** verified 2026-08-28
