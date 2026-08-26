# Phase 13: CIMD-Nachmessung und Release 0.1.9 - Pattern Map

**Mapped:** 2026-08-25
**Files analyzed:** 12 (9 geändert, 2 neu im Repo, 1 neu im Scratchpad)
**Analogs found:** 11 / 12 (eine Stelle ohne Vorbild: `uv.lock`, siehe "No Analog Found")

Diese Phase schreibt keine Zeile Produktivcode. Alle Artefakte sind Text: Versionszeichenketten,
ein Changelog-Block, vier Fake-Door-Texte, zwei Beweisdokumente und Proof-Zeilen. Genau dafür
hat dieses Repository ein durchgemessenes Vorbild pro Datei, meist aus dem 0.1.8-Release
(Commit `8392680`, `33cae32`, `08e960e`) und aus dem gelöschten Messprotokoll
`06-09-MEASUREMENTS.md` (per `git show 02dd6e1^:...` rekonstruierbar).

## File Classification

| Neu/Geändert | Rolle | Datenfluss | Nächstes Analog | Match |
|--------------|-------|------------|-----------------|-------|
| `pyproject.toml:3` | config/version | text-edit | Commit `8392680` (Bump 0.1.7 -> 0.1.8) | exakt |
| `src/mcp_connector/__init__.py:7` | config/version | text-edit | Commit `8392680` | exakt |
| `appinfo/info.xml:171,245` | config/manifest | text-edit | Commit `8392680` (`4 +--`, genau zwei Zeilen) | exakt |
| `appinfo/info.xml` 3x `<description>` | config/store-metadata | text-edit unter Gate | Abschnitt `### Under your control` / `### In Ihrer Hand` / `### Sous votre contrôle` (Zeilen 70-76, 111-117, 154-160) | exakt |
| `README.md:27` + neuer `## Enterprise` | doc/status + doc/marketing | text-edit | Statuszeile: `33cae32`; Abschnitt: `## Known limitations` (481-511) | exakt |
| `README.de.md:29` + neuer `## Enterprise` | doc | text-edit | `## Bekannte Einschränkungen` (495-526) | exakt |
| `README.fr.md:31` + neuer `## Enterprise` | doc | text-edit | `## Limitations connues` (511-544) | exakt |
| `CHANGELOG.md:12` + 2 Link-Referenzen | doc/release-notes | append-vor-Kopf | Block `## [0.1.8] - 2026-08-25` (12-95), speziell `### Changed` 68-74 | exakt |
| `docs/oauth-setup.md:279-288, 314-315` | doc/evidence | text-edit | derselbe Absatz in seiner 2026-08-20-Fassung | exakt |
| `docs/store-submission.md` Zeile 132 ff. | doc/evidence-table | append-nach-Ereignis | Zeilen 123-132 (die zehn 0.1.8-Proof-Zeilen) | exakt |
| `.planning/phases/13-.../13-MEASUREMENTS.md` **NEU** | doc/measurement-protocol | append-nach-Messung | `06-09-MEASUREMENTS.md` aus `git show 02dd6e1^:...` | exakt |
| `docs/contrib/enterprise-signals-issue.md` **NEU** | doc/draft (nicht veröffentlicht) | text | `docs/contrib/227-pr-body.md` | rollen-gleich |
| Scratchpad-Treiber (Pseudo-Konsole bzw. HTTP) **NEU, ausserhalb des Repos** | script/test-driver | request-response | `scripts/oauth_flow_check.py:sign_in` | rollen-gleich |
| `uv.lock:472` | config/version | text-edit | keins mit Absicht, siehe unten | **kein Analog** |

## Pattern Assignments

### `pyproject.toml:3`, `src/mcp_connector/__init__.py:7`, `appinfo/info.xml:171,245` (config/version, text-edit)

**Analog:** Commit `8392680` "release(11-09): prepare 0.1.8 in four places, with the changelog of this phase"
(`CHANGELOG.md | 69 ++`, `appinfo/info.xml | 4 +--`, `pyproject.toml | 2 +-`, `src/mcp_connector/__init__.py | 2 +-`, `uv.lock | 2 +-`).

**Ist-Zustand, wörtlich (alle vier in dieser Sitzung gelesen):**

```toml
# pyproject.toml:1-3
[project]
name = "nextcloud-mcp-connector"
version = "0.1.8"
```

```python
# src/mcp_connector/__init__.py:7
__version__ = "0.1.8"
```

```xml
<!-- appinfo/info.xml:171 -->
<version>0.1.8</version>
<!-- appinfo/info.xml:245 -->
			<image-tag>0.1.8</image-tag>
```

**Halter-Pattern (der Gate, den der Plan nicht neu bauen darf)** aus `tests/unit/test_exapp_env_setup.py:173-179`:

```python
    version = (root.findtext("version") or "").strip()
    if version != mcp_connector.__version__:
        problems.append(f"version {version!r} is not the package version")

    image_tag = (root.findtext(".//docker-install/image-tag") or "").strip()
    if image_tag != version:
        problems.append(f"image tag {image_tag!r} does not follow the version {version!r}")
```

**Prüfschritt-Pattern (aus 11-09, Bedrohung T-11-62): der Bump-Plan behauptet, dass kein Tag existiert.**

```bash
grep -c '0\.1\.9' pyproject.toml src/mcp_connector/__init__.py
grep -o '<version>[^<]*' appinfo/info.xml
grep -o '<image-tag>[^<]*' appinfo/info.xml
grep -n '^Version 0\.1\.9\.' README.md README.de.md README.fr.md
test -z "$(git tag --list v0.1.9)" && echo "kein Tag, korrekt"
```

---

### `README.md:27` / `README.de.md:29` / `README.fr.md:31` (doc/status, text-edit)

**Analog:** `33cae32` "fix(11): WR-03 raise the README status line to 0.1.8 and add it to runbook step 1".
Dieser Commit ist der Beweis, warum die Stelle in denselben Task gehört wie die vier Codestellen:
`git tag --contains 33cae32` nennt nur `milestone-v1.2`, nicht `v0.1.8`, die Statuszeile 0.1.7 ist
also im veröffentlichten Tarball unveränderlich drin.

**Zu ändernde Zeilen, wörtlich:**

```markdown
<!-- README.md:25-27 -->
## Status

Version 0.1.8. The app is listed in the Nextcloud App Store and installable as a Nextcloud ExApp
```

```markdown
<!-- README.de.md:27-29 -->
## Status

Version 0.1.8. Die App ist im Nextcloud App Store gelistet und als Nextcloud-ExApp über AppAPI
```

```markdown
<!-- README.fr.md:29-31 -->
## Statut

Version 0.1.8. L'application est référencée dans l'App Store de Nextcloud et installable comme
```

**Nur die Versionszahl ändern.** Die drei Statusabschnitte nennen jeweils "All 21 tools" /
"Alle 21 Tools" / "Les 21 outils": diese Zahl steht unter dem Gate aus
`tests/contract/test_tool_surface.py:752-774` und bleibt 21, weil kein Werkzeug angefasst wird.

---

### `README.md` / `.de.md` / `.fr.md`: neuer Abschnitt `## Enterprise` (doc/marketing, text)

**Analog für Ton, Platzierung und Aufbau:** `## Known limitations` (README.md:481-511),
`## Bekannte Einschränkungen` (README.de.md:495-526), `## Limitations connues` (README.fr.md:511-544).
Der neue Abschnitt kommt direkt DAHINTER und vor `## Development` / `## Entwicklung` / `## Développement`
(README.md:512, README.de.md:527, README.fr.md:545).

**Einleitungs-Pattern der Analogstelle (README.md:483-484), das der Enterprise-Text spiegeln soll:
erst die Erwartung setzen, dann die Tabelle oder Liste.**

```markdown
## Known limitations

Things that are not defects but will surprise you once. Each of them is a deliberate trade, and
each one is visible in the answer the tool gives rather than hidden behind an empty result.
```

**Deutsche Fassung derselben Stelle (README.de.md:497-498), Vorbild für Umlaute und Satzbau:**

```markdown
Dinge, die keine Mängel sind, Sie aber einmal überraschen werden. Jede davon ist ein bewusster Kompromiss,
und jede ist in der Antwort sichtbar, die das Tool gibt, statt hinter einem leeren Ergebnis verborgen.
```

**Ehrlichkeits-Pattern, das der Enterprise-Text kopieren muss** (README.md:495, Spalte "What to do"):
eine Aussage, die die Grenze benennt statt sie zu beschönigen.

```markdown
| **Nothing can be deleted or overwritten** | ... | Pick another name. This is the design constraint, not a missing feature |
```

**Inhaltliche Pflichtteile (D-05):** die drei Bausteine (Audit-Log, Gruppen-Policies, SSO/IdP),
das Wort "planned"/"geplant"/"prévu", der ausdrückliche Satz, dass heute keiner davon existiert,
Kontakt `k.cherif@outlook.de`. Kein Preis, kein Datum, keine Zusage.
Die drei READMEs sind strukturell deckungsgleich, der Abschnitt entsteht dreimal parallel im selben Task.

---

### `appinfo/info.xml`: Enterprise-Absatz in drei `<description>`-Blöcken (config/store-metadata, text-edit unter Gate)

**Analog:** der Abschnitt `### Under your control` (Zeilen 70-76) und seine zwei Übersetzungen.
Der Enterprise-Abschnitt kommt zwischen diesen Abschnitt und `### Resources` (77) beziehungsweise
`### Weiterführendes` (118) und `### Pour aller plus loin` (161).

**Analogstelle wörtlich (info.xml:70-76), das ist die Kürze und die Fettschrift-Form, die zu treffen ist:**

```markdown
### Under your control

- **Real sign in**: OAuth through Nextcloud, no app password in a configuration file
- **Your own switch**: pause access or disconnect one assistant, per account
- **Nothing in the background**: no scheduled job, no indexing, no telemetry
- **Your data stays yours**: what an assistant reads goes to that assistant, in most cases a hosted provider
```

**Deutsche Analogstelle (info.xml:111-116):**

```markdown
### In Ihrer Hand

- **Echte Anmeldung**: OAuth über Nextcloud, kein App-Passwort in einer Konfigurationsdatei
- **Ihr eigener Schalter**: Zugang pausieren oder eine einzelne Assistenz trennen, pro Konto
```

**Französische Analogstelle (info.xml:154-157), inklusive der Leerzeichen vor dem Doppelpunkt:**

```markdown
### Sous votre contrôle

- **Une vraie authentification** : OAuth via Nextcloud, aucun mot de passe d'application dans un fichier de configuration
```

**Harte Gate-Regeln für diesen Text** (`description_problems` in `tests/unit/test_exapp_env_setup.py`,
Runbook Schritt 3 nennt sie wörtlich in `docs/store-submission.md:200-203`):
kein Backtick, kein `|` (auch nicht in Prosa), kein Bild, keine horizontale Linie, kein HTML-Element,
mindestens zwei durch Leerzeilen getrennte Absätze pro Sprache, kein `archiv` im Elementtext.
`<summary>` (Zeilen 18-20) und `<environment-variables>` werden NICHT angefasst
(Pitfall 8: ein leeres Element antwortet mit HTTP 500).

**Präzedenz, dass ein Store-Text ein eigenes Release rechtfertigt:** `CHANGELOG.md:84-85`
("the store reads the manifest at upload time, which is why the correction becomes visible with
this release") und `CHANGELOG.md:132-140` (0.1.5/0.1.6, die zwei verbrannten Versionen).

---

### `CHANGELOG.md`: neuer Block `## [0.1.9]` (doc/release-notes, append-vor-Kopf)

**Analog:** der Block `## [0.1.8] - 2026-08-25` (Zeilen 12-95). Der neue Block kommt direkt
darüber, ab Zeile 12. Kein `## [Unreleased]`-Abschnitt existiert, nur die Link-Referenz.

**Einleitungsabsatz-Pattern (0.1.8, Zeilen 14-20): ein Absatz Prosa ohne Aufzählung, der sagt,
worum dieses Release geht, bevor die Rubriken kommen.** Für ein Pflege-Release ist
`## [0.1.7]` (Zeilen 97-101) die genauere Vorlage:

```markdown
## [0.1.7] - 2026-08-22

Another release about being found, and again not a line of the server changed. The app was
in one category and reachable under one spelling of its own subject, which is why people
looking for the thing it is did not find it.
```

**Format-Änderungs-Pattern, wörtlich vorgegeben durch die Übergabe aus 12-01
(`12-01-SUMMARY.md`: "Vorlage für den Wortlaut: der 0.1.8-Eintrag zu `preview_truncated`"),
CHANGELOG.md:66-74:**

```markdown
### Changed

- A change of the answer format, named here because a reader of the old key has to be
  updated: in an answer of `mail_browse` on the message level, the key `truncated` of a
  single entry is now called `preview_truncated`. The same word meant two things in the same
  answer, and only one of them was about the entry: on the answer level `truncated` says that
  the page of messages was cut and that there may be a next one, on a single entry it says
  that the preview text of that message was cut. The answer level keeps `truncated`
  unchanged, and no other tool is affected.
```

Für 0.1.9 tritt `talk_browse(level="messages")` und `message_truncated` an dieselbe Stelle,
plus der Hinweis auf die persistierte Werkzeugliste (Übergabe 12-01).

**Doku-Korrektur-Pattern (Übergabe 12-04, Formulierungsvorschlag wörtlich aus dem SUMMARY):**
"the `unified_search` example in the READMEs named `spreed`, which was never a provider id;
it now names `talk-conversations`".

**Store-Text-Änderung als eigener Eintrag, Präzedenz CHANGELOG.md:121-124:**

```markdown
- The store description is now a short list of what an assistant can do, one line per
  family, next to what it deliberately cannot do and what an account controls itself. The
  long form lives in [docs/faq.md](docs/faq.md) and
  [docs/privacy.md](docs/privacy.md), which the description links.
```

**Link-Referenzen am Dateiende, Ist-Zustand:**

```markdown
[Unreleased]: https://github.com/street1983nk/nextcloud-mcp-connector/compare/v0.1.8...HEAD
[0.1.8]: https://github.com/street1983nk/nextcloud-mcp-connector/compare/v0.1.7...v0.1.8
```

Zu tun: `[Unreleased]` auf `compare/v0.1.9...HEAD` umschreiben, `[0.1.9]: .../compare/v0.1.8...v0.1.9`
darüber ergänzen.

**Achtung, neu seit Phase 12:** `CHANGELOG.md` liegt jetzt im Vokabular-Gate. Das Wort `archiv`
darf im 0.1.9-Block nicht vorkommen, in keiner Sprache und in keinem Kompositum.

---

### `docs/oauth-setup.md`: dauerhafte CIMD-Proof-Zeile + toter Verweis (doc/evidence, text-edit)

**Analog:** derselbe Absatz in seiner heutigen Fassung, Zeilen 282-288. Die neue Zeile ersetzt sie
nicht, sie tritt daneben oder darüber, denn die 0.1.3-Aussage bleibt wahr.

```markdown
**Measured live on 2026-08-20 against Claude Code 2.1.233**, on a Nextcloud 34.0.3 instance
running this build: the client identifies itself with the document address alone, no row is
ever registered by a `/register` call, the consent screen names `claude.ai` as the host of
that client id, the code exchange answers `200`, and `files_list` comes back with the real
content of the signed in account. The written row carries an empty secret and the two
portless return addresses of the document, with a freshness window of five minutes taken
from the `Cache-Control` of the answer.
```

Das ist die Form, die die neue Zeile treffen muss: **fettes Datum plus Client-Version plus
Instanz**, dann ein Satz, der jede Behauptung des Erfolgskriteriums einzeln nennt
(Identifikation über die Dokumentadresse, kein `/register`, Consent nennt den Host,
Token 200, echter Werkzeuginhalt).

**Gegenproben-Pattern derselben Datei (Zeilen 293-312), drei Aufzählungspunkte mit gezählten
ausgehenden Sockets.** Für Phase 13 verlangt die globale Regel "alle Paths" mindestens eine davon,
Empfehlung `NC_MCP_OAUTH_CIMD=0`:

```markdown
- **This switch alone does not touch registration.** With `NC_MCP_OAUTH_CIMD=0` the document
  address is refused and no request goes out, while `/register` still answers `201` and the
  client it mints reaches the consent screen.
```

**Der tote Verweis, der im selben Edit geschlossen wird (Zeilen 314-315):**

```markdown
The raw numbers are in
[06-09-MEASUREMENTS.md](../.planning/phases/06-h-rtung-eigennachweise-und-conference-reife/06-09-MEASUREMENTS.md).
```

Ziel existiert nicht mehr (`02dd6e1` hat die v1.1-Phasenverzeichnisse entfernt). Die neue Zeile
muss ohne Nachbardokument tragen, sonst entsteht beim v1.3-Abschluss derselbe tote Link ein
zweites Mal (Pitfall 14).

**Zwei Gates auf dieser Datei:** Vokabular (`rglob` über `docs/**`) und Werkzeugzahl
(`DOCS.glob("*.md")`, nicht rekursiv). Eine Zahl ungleich 21 braucht den Halter-Pfad
`tests/contract/test_tool_surface.py` in derselben Datei.

---

### `docs/store-submission.md`: Proof-Zeilen der Schritte 1 bis 8 (doc/evidence-table, append-nach-Ereignis)

**Analog:** die zehn 0.1.8-Zeilen, Zeilen 123-132. Tabellenkopf steht auf Zeile 78-79
(`| Date | Fact | Checked with |`), die neuen Zeilen kommen nach Zeile 132, vor
`### The update keeps the connections` (134).

**Gates-Zeile (Runbook Schritt 3), Vorbild Zeile 123:**

```markdown
| 2026-08-24 22:36Z | All six gates of step 3 are green locally for 0.1.8: 2766 tests passed with 163 deselected, no lint finding, 197 files already formatted, no type error, no dead code, and the tool surface measures 15657 bytes across 21 tools against a budget of 18000 | `uv run --no-sync` in front of each of `pytest -q`, `ruff check .`, `ruff format --check .`, `pyright`, `vulture src scripts vulture_whitelist.py` and `python scripts/check_tool_budget.py`, the last one exit 0 |
```

**Archiv-Probelauf als Strukturprüfung, Vorbild Zeile 124** (enthält wörtlich den Satz, der
verhindert, dass das lokale Artefakt für das signierte gehalten wird):

```markdown
| 2026-08-24 22:39Z | The store archive of 0.1.8 has exactly one top level folder, `mcp_connector`, ... This is a structure check and nothing else: the locally built archive is not the artifact that gets signed, and the 31909 against 32168 bytes of the 2026-08-20 row above are the measurement that says so | `scripts/build_store_release.sh`, then `tar -tzf dist/mcp_connector-0.1.8.tar.gz` |
```

**Tag/Workflow-Zeile (Schritte 4 und 5), Vorbild Zeile 125:**

```markdown
| 2026-08-25 02:54Z | The release workflow of the tag `v0.1.8` is green in every step, run `32803041518`: the multi arch image was built and pushed, the store archive was built and attached to the GitHub release. The 42 commits of this phase were pushed to `main` immediately before the tag ... | `git push origin main`, then `git tag v0.1.8` and `git push origin v0.1.8`, then `gh run watch 32803041518 --exit-status`, exit 0, job `publish` success in 1m29s |
```

**Signatur-Zeile (Schritt 6), Vorbild Zeile 126** (nennt beide Grössen und beide sha256, das ist
der Beleg, dass das heruntergeladene Asset signiert wurde):

```markdown
| 2026-08-25 02:55Z | The download of 0.1.8 answers 200 with 45546 bytes, the size that was signed, and the signature over exactly those bytes verifies against the certificate. The published asset is again not the locally built one: 45546 bytes against 45710, `2769c587…` against `15fc8719…` | `curl -sSIL .../v0.1.8/mcp_connector-0.1.8.tar.gz` gives 302 then 200; `openssl x509 -in mcp_connector.crt -pubkey -noout`, then `openssl dgst -sha512 -verify` over the downloaded asset: `Verified OK`; `sha256sum` of both files |
```

**Store-Annahme (Schritt 7), Vorbild Zeile 127**, und die vier Nachweise (Schritt 8),
Vorbilder Zeilen 128 bis 131: Release-Liste, `curl -I` auf das Asset (Zeile 129 sagt ausdrücklich
"This row is not optional"), OCI-Index mit beiden Plattformen, vollständige Tagliste.

**Form-Regel (Pattern 3 der Recherche, Bedrohung T-11-63):** Datum in UTC mit `Z`, dann die
Behauptung im Präsens, dann der Befehl. Geschrieben wird die Zeile erst NACH dem Ereignis.
Diese Datei ist die einzige mit Vokabular-Gate-Ausnahme
(`VOCABULARY_EXCEPTION = ROOT / "docs" / "store-submission.md"`, `test_exapp_env_setup.py:1978`),
und die Begründung im Gate-Docstring ist genau diese Beweisrichtung: "rewriting a dated proof
line afterwards would turn a record into a claim".

---

### `.planning/phases/13-.../13-MEASUREMENTS.md` **NEU** (doc/measurement-protocol)

**Analog:** `06-09-MEASUREMENTS.md`, abrufbar mit

```bash
git show 02dd6e1^:.planning/phases/06-h-rtung-eigennachweise-und-conference-reife/06-09-MEASUREMENTS.md
```

**Kopf-Pattern wörtlich aus dem Analog (die drei Konventionen sind zu übernehmen, nicht neu zu erfinden):**

```markdown
# 06-09 Messprotokoll: Claude Code per Metadatendokument, und die Loopback-Portfrage

Datum des Laufs: **2026-08-20, 15:48 bis 16:12 UTC** (Abschnitte 1 bis 6). ...

Drei Konventionen für dieses Protokoll, übernommen aus 06-07 und 06-08:

* `occ` steht für `docker exec -u www-data nc-mcp-exapp-nc php occ`. Nicht
  `docker compose exec`: jeder compose-Aufruf gegen `compose.exapp.yml` verlangt
  `HP_SHARED_KEY` in der Umgebung (WR-11) ...
* Kein Credential steht in diesem Dokument, auch kein Wegwerf-Credential (T-05-39). Kein
  Token, kein Autorisierungscode, kein `code_challenge`, kein `state`, kein App-Passwort.
  Wo eine Logzeile solche Werte trug, stehen sie als `<gekürzt>`.
* Die Version einer Instanz ist immer die Zeile aus `occ status`, nie ein Docker-Tag
  (Pitfall 6). Für den Connector ist die Pflichtangabe Version **und** Image-Digest.
```

**Topologie-Tabelle als erster Abschnitt, Pflichtzeilen aus dem Analog:**

```markdown
## Topologie des Laufs

| Was | Wert |
|-----|------|
| Compose-Datei, Projekt | `compose.exapp.yml`, Projekt `nc-mcp-exapp`, erreichbar unter `http://127.0.0.1:8081` (Caddy, nur Loopback) |
| Nextcloud | **34.0.3 (34.0.3.2)** laut `occ status`, `installed: true`, `maintenance: false` |
| Connector | `mcp_connector` **0.1.2 [enabled]** laut `occ app_api:app:list`; Image `127.0.0.1:5000/mcp_connector:0.1.2`, Digest `sha256:3ba4a2ce…`, `RestartCount` 0 |
| **Gemessener Client** | **Claude Code 2.1.233** (`claude --version`) |
| Messkonto | `alice`, Fixture-Konto aus `scripts/bootstrap_exapp.sh` |
| Owner-Instanzen | `nc-mcp-test` und `findling-nextcloud` liefen durch, unberührt |
```

Für Phase 13 stehen dort 0.1.9 und der Digest aus
`docker buildx imagetools inspect 127.0.0.1:5000/mcp_connector:0.1.9 --format '{{.Manifest.Digest}}'`.

**Abschnitts-Pattern: eine Frage als Überschrift mit Uhrzeit, dann die Antwort in Fettschrift,
dann der Rohbeleg.**

```markdown
## 1. Trägt das AS-Dokument der laufenden Instanz beide Felder? (15:48Z)

**Antwort: ja, beide.** Ohne beide wählt der Client den CIMD-Weg nicht ...
```

Diese Datei liegt unter `.planning/` und damit ausserhalb jeder Gate-Reichweite: Werkzeugzahlen
und Wortwahl sind hier frei, die Credential-Regel gilt trotzdem.

---

### `docs/contrib/enterprise-signals-issue.md` **NEU** (doc/draft, nicht veröffentlicht)

**Analog:** `docs/contrib/227-pr-body.md`. Gleicher Ordner, gleiche Rolle: ein fertiger
öffentlicher Text, der im Repo liegt und den ein Mensch absendet.

**Kopf-Pattern wörtlich (227-pr-body.md:1-12): ein HTML-Kommentar mit den Metadaten, dann eine
Zeile, die die Grenze zwischen Metadaten und Fremdtext markiert.**

```markdown
<!--
Prepared pull request body for nextcloud/context_agent#227.

Target repo:  nextcloud/context_agent
Head branch:  street1983nk:fix/stateless-http-session-compat
Commit:       def1425 (single functional change, Signed-off-by / DCO)
Title:        fix(mcp): make stateless_http configurable and session-capable by default
PR URL:       https://github.com/nextcloud/context_agent/pull/230
Submitted:    2026-08-15

Everything below this comment is the PR body as it will be rendered on GitHub.
-->
```

Für den Issue-Entwurf: `Target repo: street1983nk/nextcloud-mcp-connector`,
`Title: Enterprise features: what would your org need before allowing MCP access?`,
statt `Submitted:` eine Zeile "Not published. Publishing this issue is an owner decision (D-07)."
plus das Go-Kriterium (mindestens fünf qualifizierte Org-Signale mit über 100 Nutzern in sechs
Wochen, oder ein Ankerkunde mit Pilotwunsch), damit später messbar ist, wofür der Entwurf da war.

**Zwei Kopplungen dieses Ordners:**
1. `docs/contrib/**` liegt in der `rglob`-Reichweite des Vokabular-Gates
   (`public_markdown_pages()`, `test_exapp_env_setup.py:2009-2025`).
2. Ein Selbsttest desselben Gates behauptet ausdrücklich die Existenz von
   `docs/contrib/227-pr-body.md` als Beleg, dass der Walk rekursiv ist (Docstring Zeile 2017-2020).
   Diese Datei darf nicht verschoben oder umbenannt werden.

Kein `gh issue create` in dieser Phase.

---

### Messtreiber im Scratchpad **NEU, ausserhalb des Repos** (script/test-driver, request-response)

**Analog:** `scripts/oauth_flow_check.py`, Funktion `sign_in`. Das ist der eine wiederverwendbare
Browser-Schenkel; der Rest des Skripts fährt über dynamische Registrierung und ist für CIMD
gerade nicht das Vorbild.

**Nicht selbst bauen:** ein Nextcloud-Login im Treiber. Ein Gate verbietet dasselbe unter `src/`
(`test_no_module_under_src_automates_a_nextcloud_sign_in`).

**Ablage-Pattern aus 06-09:** die Treiberskripte lagen bewusst im Scratchpad und nicht im
Repository. Für Weg A kommt der Pseudo-Konsolen-Teil dazu (`CreatePseudoConsole` per `ctypes`,
Windows-Bordmittel, kein Paket-Install), weil `claude mcp login` ohne tty mit
`stdin isn't a terminal` endet. `claude mcp add ... -s local` nur aus einem
Scratchpad-Projektverzeichnis, und `C:\Users\Student\.claude.json` vorher ausserhalb des Repos
sichern.

## Shared Patterns

### Fünf Versionsstellen in einem Task, plus die Behauptung, dass kein Tag existiert
**Quelle:** `docs/store-submission.md:174-187` (Runbook Schritt 1), Commit `8392680` + `33cae32`.
**Gilt für:** `pyproject.toml`, `__init__.py`, `appinfo/info.xml` (2x), drei READMEs.
Zwei Gates halten vier Stellen, die fünfte reist ungegatet mit. Der Prüfschritt behauptet alle
fünf UND `git tag --list v0.1.9` leer.

### Sechs Gates, wörtlich in dieser Reihenfolge
**Quelle:** `docs/store-submission.md:191-199`.
**Gilt für:** jeden Plan dieser Phase, der eine Textdatei anfasst.

```bash
uv run --no-sync pytest -q
uv run --no-sync ruff check .
uv run --no-sync ruff format --check .
uv run --no-sync pyright
uv run --no-sync vulture src scripts vulture_whitelist.py
uv run --no-sync python scripts/check_tool_budget.py
```

Zwischenlauf für die Textgates allein:
`uv run --no-sync pytest tests/unit/test_exapp_env_setup.py -k "vocabulary or description" -q`.

### Vokabular-Gate: eine Ausnahme, rekursive Reichweite
**Quelle:** `tests/unit/test_exapp_env_setup.py:1686`, `:1978`, `:2009-2025`, `:2035-2053`.
**Gilt für:** `CHANGELOG.md`, drei READMEs, `docs/**/*.md` (rekursiv), `appinfo/info.xml`-Elementtext.

```python
FORBIDDEN_VOCABULARY = "archiv"
VOCABULARY_EXCEPTION = ROOT / "docs" / "store-submission.md"

docs = sorted(page for page in (ROOT / "docs").rglob("*.md") if page != VOCABULARY_EXCEPTION)
pages = [*PUBLIC_MARKDOWN, *docs]
```

Manifest-Kommentare sind ausgenommen (der Check läuft über den geparsten Baum), Beschreibungstext
nicht. `.planning/**` liegt vollständig ausserhalb.

### Werkzeugzahl-Gate: nicht rekursiv, anderer Umfang als das Vokabular-Gate
**Quelle:** `tests/contract/test_tool_surface.py:752-774`.
**Gilt für:** `docs/*.md` (nur oberste Ebene) plus `README.md`.

```python
    holder = "tests/contract/test_tool_surface.py"
    current = len(EXPECTED_TOOLS)
    for page in [*sorted(DOCS.glob("*.md")), README]:
        text = page.read_text(encoding="utf-8")
        explained = holder in text
```

Eine Zahl ungleich 21 braucht den Halter-Pfad in derselben Datei. `docs/contrib/` liegt hier
ausserhalb, im Vokabular-Gate drin: zwei Reichweiten, nicht eine.

### Proof-Zeile nach dem Ereignis, mit Datum und Befehl
**Quelle:** `docs/store-submission.md:76` ("Every line was measured, not assumed. No fact without
its check.") und die Zeilen 123-132.
**Gilt für:** `docs/store-submission.md`, `docs/oauth-setup.md`, `13-MEASUREMENTS.md`.

### Kein Credential im Beweisdokument
**Quelle:** Konvention 2 aus `06-09-MEASUREMENTS.md` (T-05-39).
**Gilt für:** `13-MEASUREMENTS.md`, `docs/oauth-setup.md`, `docs/store-submission.md`.
Kein Token, kein Autorisierungscode, kein `code_challenge`, kein `state`, kein App-Passwort,
auch kein Wegwerf-Wert. Gekürzte Werte als `<gekürzt>`.

### Drei Sprachfassungen im selben Task
**Quelle:** die drei READMEs sind strukturell deckungsgleich (Überschriften-Offsets 481/495/511,
512/527/545), die drei `<description>`-Blöcke ebenso (70/111/154, 77/118/161).
**Gilt für:** Statuszeile, Enterprise-Abschnitt, Manifest-Beschreibung.
Deutsch mit echten Umlauten, Französisch mit Accents und Leerzeichen vor dem Doppelpunkt,
keine Em-Dashes in keiner Fassung.

### Der Release-Plan ist nicht autonom
**Quelle:** Frontmatter von 11-10 (`git show 568346c:.planning/phases/11-.../11-10-PLAN.md`).
**Gilt für:** den Plan, der Runbook-Schritte 4 bis 8 ausführt: `autonomous: false` plus die
must-have-Wahrheit "Der Tag v0.1.9 entsteht erst nach einer ausdrücklichen Owner-Freigabe".
Zwei menschliche Tore: Freigabe vor Schritt 4, angemeldete Store-Sitzung in Schritt 7.

## No Analog Found

| Datei | Rolle | Datenfluss | Grund |
|-------|-------|------------|-------|
| `uv.lock:472` | config/version | text-edit | **Sechste Versionsstelle, von keinem Gate und von keinem Runbook-Schritt gehalten.** `uv.lock` trägt `name = "nextcloud-mcp-connector"` / `version = "0.1.8"` (Zeilen 471-472), und Commit `8392680` hat sie beim 0.1.8-Bump mitgeändert (`uv.lock \| 2 +-`). `docs/store-submission.md` nennt sie in keinem der acht Schritte, und `grep -rn "uv.lock" tests/ scripts/ .github/workflows/` findet nichts. Die Recherche schreibt "uv.lock bleibt unangetastet"; das steht im Widerspruch zum belegten Verhalten des letzten Bumps. Der Planer muss das entscheiden: entweder die Zeile im Bump-Task mitziehen (wie 0.1.8 es tat) oder ausdrücklich stehen lassen und begründen. Ein Dependency-Block wird in keinem Fall angefasst |

Für alles Weitere gilt: kein Kandidat ohne Analog. Selbst die zwei neuen Dateien haben ein
Vorbild im Repo beziehungsweise in der Git-Historie.

## Metadata

**Analog search scope:** `pyproject.toml`, `src/mcp_connector/__init__.py`, `appinfo/info.xml`,
`README.md`, `README.de.md`, `README.fr.md`, `CHANGELOG.md`, `docs/`, `docs/contrib/`,
`tests/unit/test_exapp_env_setup.py`, `tests/contract/test_tool_surface.py`,
`git log`/`git show` (Commits `8392680`, `33cae32`, `08e960e`, `eb05a6f`, `02dd6e1`)
**Files scanned:** 14 gelesen, 1 aus der Git-Historie rekonstruiert
**Pattern extraction date:** 2026-08-25
