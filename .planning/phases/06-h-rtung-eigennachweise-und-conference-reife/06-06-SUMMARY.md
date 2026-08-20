---
phase: 06-h-rtung-eigennachweise-und-conference-reife
plan: 06
subsystem: exapp-ui
tags: [consent-screen, cimd, loopback, display-duty, escaping, docs, changelog]

# Dependency graph
requires:
  - phase: 06-02
    provides: "cimd.is_cimd_client_id als Formtest einer Dokument-Identitaet, ohne Store-Zugriff"
  - phase: 06-03
    provides: "registry.LOOPBACK_HOSTS als die Menge, die D-35 schon zulaesst"
  - phase: 06-05
    provides: "der CIMD-Zweig in provider.get_client, der eine URL-client_id ueberhaupt bis zur Zustimmungsseite bringt"
provides:
  - "strings.CONSENT_DETAIL_CLIENT_HOST, strings.CONSENT_LOOPBACK_TITLE, strings.CONSENT_LOOPBACK_BODY"
  - "consent_page(..., client_host=None, loopback_only=False): der Hostname als vierter detail_list-Eintrag, die Loopback-Warnung als zweiter callout"
  - "oauth/consent._identifier_host und _loopback_only: die zwei Flags am Aufrufer, ohne zusaetzlichen Store- oder Nextcloud-Roundtrip"
  - "docs/oauth-setup.md, Abschnitt 'Client ID Metadata Documents': der Weg, der Schalter samt Kopplung, die Allowlist-Begruendung, die SSRF-Grenze mit Zahlen, die zwei Anzeigepflichten"
  - "docs/oauth-setup.md, Pitfall 6 ersetzt: RFC 8252 7.3 als MUST, D-35 unveraendert"
affects: [AUTH-08, CLIENT-05, 06-07, 06-09]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Eine neue Anzeigepflicht wird ein weiterer Eintrag einer bestehenden Liste und ein zweiter Aufruf eines bestehenden Primitivs: kein neues Rendering-Primitiv heisst keine zweite Escaping-Stelle"
    - "Der Aufrufer rechnet, die Seite rendert: dasselbe Keyword-Muster wie unverified, mit Defaults, die jeden bestehenden Aufrufer unveraendert lassen"
    - "Ein Feldname, der nicht vorkommen darf, wird auch in Docstrings nicht genannt, wenn ein Grep-Gate ihn sucht: der Docstring beschreibt die Sache, das Gate sucht das Wort"
    - "Ein Ehrlichkeitstext nennt, was belegt ist, und was nicht; das Wort 'verified' bleibt dem bestehenden Negativsatz vorbehalten"
    - "Ein ueberholter Doku-Absatz wird ersetzt, nicht geloescht: der alte Befund bleibt datiert stehen, der neue nennt seinen offenen Rest"

key-files:
  created:
    - .planning/phases/06-h-rtung-eigennachweise-und-conference-reife/06-06-SUMMARY.md
  modified:
    - src/mcp_connector/exapp/ui/strings.py
    - src/mcp_connector/exapp/ui/consent.py
    - src/mcp_connector/oauth/consent.py
    - tests/unit/test_oauth_ui.py
    - tests/unit/test_oauth_consent.py
    - docs/oauth-setup.md
    - CHANGELOG.md
    - .planning/STATE.md
    - .planning/ROADMAP.md

key-decisions:
  - "Die Herkunft wird aus der Form der client_id erkannt (cimd.is_cimd_client_id), nicht aus der Store-Spalte cimd_fetched_at: eine CIMD-client_id ist per Draft eine https-URL mit Pfad, eine DCR-client_id eine Zufalls-UUID. Damit bleibt es bei genau einem Nextcloud-Roundtrip pro Request (SC 5 der Phase 3)"
  - "Das Loopback-Flag wird auch fuer DCR-Clients berechnet: Cursor registriert http://localhost:8787/callback, und die Impersonationsgefahr haengt an der Rueckadresse und nicht am Registrierungsweg (T-06-35)"
  - "_is_loopback liest Host UND Port, nach dem Muster von registry._comparable_host: urlsplit wirft erst beim Port, also haette eine Adresse mit unmoeglichem Port sonst als Loopback gegolten"
  - "Eine leere redirect_uris-Liste ist NICHT 'nur Loopback': ein Client ohne Rueckadresse ist ein anderer Fall und endet vor diesem Screen auf der Redirect-Seite. Als Parametrize-Fall belegt, weil die Route ihn nicht bis zur Seite bringen kann"
  - "Der Docstring von exapp/ui/consent.py nennt das verbotene Feld nicht namentlich: das Grep-Kriterium des Plans zaehlt Vorkommen in der Datei, also beschreibt der Docstring die Sache ('eine Logo-Adresse aus fremder Domaene') und ein Test haelt das Wort heraus"
  - "Der Abschnitt in docs/oauth-setup.md ist ein eigener ##-Abschnitt vor '## Evidence', mit einem Verweis aus dem AUTH-07-Schalterblock: der bestehende Titel 'The three switches of AUTH-07' bleibt richtig, weil der vierte Schalter zu AUTH-08 gehoert"
  - "Die drei READMEs, appinfo/info.xml und die Version bleiben unberuehrt (Dreisprachigkeit ist 06-07); der Live-Nachweis-Satz bleibt in beiden neuen Doku-Abschnitten offen stehen, bis 06-09 ihn ersetzt"

patterns-established:
  - "Zwei Warnungen auf einer Zustimmungsseite sind zwei callout-Bloecke und werden im Test ueber die Anzahl der gerenderten Boxen gezaehlt, nicht ueber eine Teilzeichenkette der Copy: eine Teilzeichenkette wuerde auch passen, wenn die zweite Box nie erschien"

requirements-completed: []

# Metrics
duration: 40min
completed: 2026-08-20
---

# Phase 06 Plan 06: Die zwei Anzeigepflichten der Zustimmungsseite Summary

**Die Zustimmungsseite nennt den Hostnamen einer Dokument-`client_id` als vierten
Detaileintrag und warnt in einem zweiten `callout`, wenn alle Rueckadressen eines Clients auf
dem Rechner der Nutzerin liegen; beide Flags rechnet der Aufrufer aus vorhandenen Werten,
ohne zusaetzlichen Store- oder Nextcloud-Roundtrip, und `docs/oauth-setup.md` beschreibt den
CIMD-Weg samt SSRF-Grenze und ersetzt den ueberholten Loopback-Absatz.**

## Performance

- **Duration:** 40 min
- **Tasks:** 3 von 3
- **Files modified:** 3 Quelldateien, 2 Testdateien, Doku und CHANGELOG, plus Zustand und Roadmap

## Task Commits

1. **Task 1: Texte und Rendering fuer Herkunft und Loopback-Warnung** , `79b0d19` (feat)
2. **Task 2: Die zwei Flags werden am Aufrufer berechnet** , `13f74b9` (feat)
3. **Task 3: docs/oauth-setup.md und CHANGELOG** , `5bed3ee` (docs)

## Was entstanden ist

| Datei | Inhalt |
|-------|--------|
| `src/mcp_connector/exapp/ui/strings.py` | `CONSENT_DETAIL_CLIENT_HOST` ("Client ID host"), `CONSENT_LOOPBACK_TITLE` ("Comes back to this computer") und `CONSENT_LOOPBACK_BODY`; alle drei alphabetisch in `__all__`, jede mit dem Spec-Satz als Begruendung im Kommentar |
| `src/mcp_connector/exapp/ui/consent.py` | `consent_page` nimmt `client_host: str \| None = None` und `loopback_only: bool = False`; der Hostname ist ein vierter Eintrag derselben `detail_list`, die Warnung ein zweiter `layout.callout("warning", ...)` neben dem bestehenden |
| `src/mcp_connector/oauth/consent.py` | `_decision` uebergibt die zwei Werte; `_identifier_host` (Form der `client_id`) und `_loopback_only`/`_is_loopback` (die registrierten Adressen gegen `registry.LOOPBACK_HOSTS`) |
| `tests/unit/test_oauth_ui.py` | 6 neue Tests auf `consent_page`: vier statt drei `dt`-Eintraege mit Hostname, drei ohne, zwei `callout`-Boxen bei Loopback, die Warnung allein fuer einen gelisteten Client, ein Escaping-Test ueber Elementanzahlen, ein Bild- und Grep-Gate |
| `tests/unit/test_oauth_consent.py` | 3 Routen-Tests (CIMD-Client mit Host und beiden Warnungen, DCR mit https, DCR auf Loopback) plus zwei Parametrize-Kataloge fuer die zwei Rechnungen, insgesamt 15 Faelle |
| `docs/oauth-setup.md` | neuer Abschnitt "Client ID Metadata Documents: accepted since this build, next to registration"; Pitfall 6 ersetzt; ein Verweis auf den vierten Schalter im AUTH-07-Block |
| `CHANGELOG.md` | die Anzeigepflichten als `Added`-Eintrag, und die Grenzen des Abrufs im bestehenden CIMD-Eintrag ausgeschrieben (fuenf Kilobyte, fuenf Sekunden, kein Redirect, kein gemerkter Fehlschlag) |

## Wie die Seite jetzt aussieht

Zwei `if`-Bloecke und eine Liste, die einen Eintrag mehr haben kann:

```python
    if unverified:
        blocks.append(layout.callout("warning", strings.CONSENT_WARNING_TITLE, ...))
    if loopback_only:
        blocks.append(layout.callout("warning", strings.CONSENT_LOOPBACK_TITLE, ...))
    details = [
        (strings.CONSENT_DETAIL_APP_NAME, name),
        (strings.CONSENT_DETAIL_REDIRECT, redirect_uri),
        (strings.CONSENT_DETAIL_CLIENT_ID, client_id),
    ]
    if client_host:
        details.append((strings.CONSENT_DETAIL_CLIENT_HOST, client_host))
```

Kein neues Rendering-Primitiv, also auch keine zweite Escaping-Stelle: alles laeuft weiter
durch `layout.detail_list`, `layout.callout` und `layout.page`, und damit durch die eine
CSP-mit-Nonce-Stelle. Die `redirect_uri` bleibt vollstaendig, der Hostname reiht sich daneben
ein statt sie zu ersetzen.

Fuer einen DCR-Client aendert sich nichts: `client_host` ist `None`, `loopback_only` ist
`False`, die Liste hat drei Eintraege und die Seite genau eine Warnung. Ein Test prueft
genau das, damit die Aenderung dem bestehenden Weg nichts kostet.

## Wie die zwei Flags entstehen

Die Herkunft steckt in der Form der `client_id`, nicht in der Datenbank:

```python
def _identifier_host(client_id: str) -> str | None:
    if not cimd.is_cimd_client_id(client_id):
        return None
    try:
        return urlsplit(client_id).hostname
    except ValueError:
        return None
```

Eine CIMD-`client_id` ist per Draft eine https-URL mit Pfad, eine DCR-`client_id` eine
Zufalls-UUID; die Spalte `cimd_fetched_at` aus 06-05 haette dieselbe Antwort gegeben und
einen zweiten Store-Zugriff auf einem Pfad gekostet, dessen ganzer Punkt ein Roundtrip pro
Request ist (T-06-39). Der Kommentar an der Aufrufstelle sagt das, damit hier niemand einen
zweiten Roundtrip einbaut.

Das Loopback-Flag fragt die registrierten Adressen und nicht den Registrierungsweg. Beleg
dafuer, dass das nicht Theorie ist: Cursors gemessener Body enthaelt
`http://localhost:8787/callback`, also bekommt auch ein DCR-Client die Warnung, wenn er
nichts anderes registriert hat. Ein leerer Adressensatz ist dabei bewusst `False`.

## Die Doku

Der neue Abschnitt folgt der Form des Cursor-Absatzes: der Zustand steht im Titel
("accepted since this build, next to registration"), der Stand ist datiert, es steht
ausdruecklich drin, was sich NICHT geaendert hat (DCR unberuehrt, Claude.ai und ChatGPT
bleiben dort), die Zahlen und Kopiertexte stehen in Code-Bloecken, und der letzte Satz nennt
den offenen Rest ("the live proof ... is still open and follows in this phase"). Inhalt:
der Weg, `NC_MCP_OAUTH_CIMD` mit der Kopplung an `NC_MCP_OAUTH_DCR`, warum die Allowlist mit
einer veroeffentlichten URL besser funktioniert als mit einer Zufalls-UUID (mit dem
Kopierbeispiel im Code-Block), die SSRF-Grenze als Stichpunkte mit 5120 Bytes, 5 Sekunden,
kein Redirect, keine gecachten Fehler, und die zwei Anzeigepflichten samt Ehrlichkeitsgrenze.

Pitfall 6 war ab dieser Phase falsch und ist ersetzt statt getilgt: der alte Befund steht
datiert ("Up to and including 0.1.2 ..."), der neue nennt RFC 8252 7.3 im Wortlaut als MUST,
sagt, dass ausschliesslich der Port frei ist, haelt fest, dass D-35 unveraendert gilt und die
gelockerte Adresse nie in die Registrierung geschrieben wird, und nennt den offenen
Live-Nachweis. Dieser Satz ist der, den 06-09 loescht und durch die Messung ersetzt.

## Verifikation

| Prueflauf | Ergebnis |
|-----------|----------|
| `uv run --no-sync pytest tests/unit/test_oauth_ui.py -q` | 92 gruen |
| `uv run --no-sync pytest tests/unit/test_oauth_consent.py -q` | 96 gruen |
| `uv run --no-sync pytest tests/unit/test_exapp_env_setup.py -q` | 146 gruen (Text- und Vokabular-Gates) |
| `uv run --no-sync pytest tests/unit -q` | gruen |
| `uv run --no-sync pytest` (Default-Auswahl) | 2183 passed, 92 deselected in 59,22 s |
| `uv run --no-sync ruff check .` | All checks passed |
| `uv run --no-sync ruff format --check .` | 171 files already formatted |
| `uv run --no-sync pyright` | 0 errors, 0 warnings, 0 informations |
| `uv run --no-sync vulture src scripts vulture_whitelist.py` | keine Ausgabe, Exit 0 |
| `pyproject.toml`, `uv.lock` | unveraendert (T-06-SC: dieser Plan installiert nichts) |

Die Grep-Akzeptanzgrenzen des Plans einzeln nachgezaehlt:

| Grenze | Ergebnis |
|--------|----------|
| `grep -rn "verified\|Verified" src/mcp_connector/exapp/ui/strings.py` | 2 Treffer, beide in `CONSENT_WARNING_TITLE`/`CONSENT_WARNING_BODY`, keiner im neuen Text |
| `grep -c "logo_uri\|<img" src/mcp_connector/exapp/ui/consent.py` | 0 |
| `grep -n "load_client\|store.load" src/mcp_connector/oauth/consent.py` | 3, genau wie vor der Aenderung (dreimal `load_authorization`/`load_flow`, kein `load_client`) |
| `grep -in "archiv" docs/oauth-setup.md CHANGELOG.md` | 0 |
| `grep -n "Em- oder En-Dash" docs/oauth-setup.md CHANGELOG.md` | 0 |
| ueberholter Loopback-Absatz ("deliberate limit of v1") | 0 |
| `grep -c "RFC 8252" docs/oauth-setup.md` | 2 |
| `grep -c "NC_MCP_OAUTH_CIMD" docs/oauth-setup.md` | 3, mit der Kopplung an `NC_MCP_OAUTH_DCR` im selben Absatz |
| `grep -c "5120" docs/oauth-setup.md` | 1 |
| `grep -n "^## \[0.1.3\]" CHANGELOG.md` | 0 (kein Release, keine Versionsanhebung) |
| `git diff README.md README.de.md README.fr.md appinfo/info.xml` | leer |

## Abweichungen vom Plan

### Automatisch behoben

**1. [Rule 1 - Bug] `_is_loopback` liess eine Adresse mit unmoeglichem Port als Loopback durch**

- **Gefunden bei:** Task 2, beim ersten Lauf des Parametrize-Katalogs
- **Problem:** `urlsplit("http://localhost:99999/callback").hostname` liefert `localhost`
  ohne zu werfen; die `ValueError` kommt erst beim Lesen von `.port`. Eine erste Fassung las
  nur den Host, also haette eine Adresse, die dieses Projekt an jeder anderen Stelle als
  unzerlegbar ablehnt, hier als Loopback gegolten.
- **Fix:** Host und Port werden gemeinsam gelesen, in der Form von
  `registry._comparable_host`, mit dem Grund im Docstring. Der Fall steht als eigener
  Parametrize-Eintrag im Katalog.
- **Dateien:** `src/mcp_connector/oauth/consent.py`, `tests/unit/test_oauth_consent.py`
- **Commit:** `13f74b9`

**2. [Rule 3 - Blocker] Das Grep-Gate des Plans faellt ueber den eigenen Docstring**

- **Gefunden bei:** Task 1, erster Testlauf
- **Problem:** Der neue Docstring von `consent_page` erklaerte namentlich, welches Feld
  bewusst nicht gerendert wird. Damit war das Akzeptanzkriterium
  (`grep -c "logo_uri\|<img" ... == 0`) unerfuellbar, und derselbe Konflikt hatte in 06-02
  und 06-05 schon zweimal zugeschlagen.
- **Fix:** Der Docstring beschreibt die Sache ("a logo address from a foreign domain") und
  nennt das Wort nicht; ein Test greppt das Modul auf beide Formen und haelt die Grenze.
- **Dateien:** `src/mcp_connector/exapp/ui/consent.py`, `tests/unit/test_oauth_ui.py`
- **Commit:** `79b0d19`

**3. [Rule 2 - fehlende Konsistenz] Der Doku-Satz "die drei Schalter" war nach 06-04 schief**

- **Gefunden bei:** Task 3
- **Problem:** `docs/oauth-setup.md` sagte in Abschnitt 1, das Manifest deklariere "this one
  and the three switches below", waehrend `appinfo/info.xml` seit 06-04 vier Schalter
  deklariert. Ein Leser haette den CIMD-Schalter fuer nicht durchgereicht gehalten, und
  genau das ist der teuerste stille Fehler dieser Phase.
- **Fix:** Der Satz nennt jetzt "every switch below", und unter der AUTH-07-Tabelle steht ein
  Verweis auf den vierten Schalter mit dem Abschnitt, der ihn beschreibt. Die Ueberschrift
  "The three switches of AUTH-07" bleibt, weil sie ueber AUTH-07 spricht und der vierte
  Schalter zu AUTH-08 gehoert.
- **Dateien:** `docs/oauth-setup.md`
- **Commit:** `5bed3ee`

**4. [Rule 2 - Owner-Regel] Die SSRF-Grenze stand im CHANGELOG nur halb**

- **Gefunden bei:** Task 3
- **Problem:** Der Plan verlangt vier Punkte unter `## [Unreleased]`; CIMD-Weg, Schalter und
  Loopback-Portregel standen seit 06-01 bis 06-05 dort, die SSRF-Grenze aber nur als "reads
  such a document from public addresses only ... never fetches an image". Die Zahlen und das
  Cache-Verbot fehlten.
- **Fix:** Der bestehende `Added`-Eintrag nennt jetzt fuenf Kilobyte, fuenf Sekunden, kein
  Redirect und "a failed read is not remembered", in Nutzersprache. Dazu der neue Eintrag zu
  den zwei Anzeigen dieses Plans.
- **Dateien:** `CHANGELOG.md`
- **Commit:** `5bed3ee`

### Bewusst nicht getan

Die drei READMEs, `appinfo/info.xml`, der Store-Text und die Version sind unberuehrt: die
Dreisprachigkeit zieht in 06-07 gemeinsam nach, und ein Store-Release braucht ohnehin
Owner-Freigabe. `docs/client-setup.md` bleibt ebenfalls liegen, obwohl der ersetzte
Pitfall-6-Absatz dorthin verweist: der Verweis ist weiterhin richtig (der App-Passwort-Weg
existiert), und die Client-Nachweise dieser Phase gehoeren zu 06-08 und 06-09.

## Was dieser Plan nicht tut

Kein neues Paket, kein `os.environ`, kein modul-globaler veraenderlicher Zustand, keine neue
Route, kein neuer Fehlercode, kein zusaetzlicher Store- oder Nextcloud-Zugriff. `unverified`
ist unveraendert. Der Live-Nachweis mit echtem Claude Code, der aus diesen zwei Anzeigen
einen gemessenen Screenshot macht, ist 06-09.

## Known Stubs

Keine. Beide Flags werden aus vorhandenen Werten berechnet und beide Anzeigen sind gerendert
und getestet; nichts an dieser Seite wartet auf einen spaeteren Plan.

## Threat Flags

Keine neue Angriffsflaeche ausserhalb des Threat-Registers dieses Plans: kein Endpunkt, kein
Auth-Pfad, keine Schema-Aenderung, kein Dateizugriff. Zwei Werte mehr erreichen das Markup,
beide durch dieselbe Escaping-Stelle, mit einem Escaping-Test ueber Elementanzahlen
(T-06-36). T-06-37 (kein Bild aus fremder Domaene) ist zusaetzlich per Grep-Test gehalten,
T-06-38 (kein "verified" im neuen Text) per Grep, T-06-39 (kein zweiter Roundtrip) per
Vergleich der Store-Aufrufe gegen den Stand vor der Aenderung.

## Requirements

**AUTH-08 und CLIENT-05 bleiben Pending, bewusst.** Beide Requirements sind im Code jetzt
vollstaendig (Schalter, Advertising, Zweig, Frische, Portregel, und mit diesem Plan die zwei
Anzeigepflichten), aber der Nachweis dieses Projekts fuer einen Verbindungssatz ist eine
Messdatei mit einem echten Client gegen eine laufende Instanz. Beide werden in 06-09
abgehakt, und derselbe Plan loescht die zwei "still open"-Saetze aus `docs/oauth-setup.md`.

## Self-Check: PASSED

`06-06-SUMMARY.md` liegt auf der Platte, die drei Task-Commits stehen im Log (`79b0d19`,
`13f74b9`, `5bed3ee`), alle sieben geaenderten Quell-, Test- und Doku-Dateien sind darin
enthalten, und der volle Default-Lauf wurde nach dem letzten Commit wiederholt
(2183 passed, 92 deselected).
