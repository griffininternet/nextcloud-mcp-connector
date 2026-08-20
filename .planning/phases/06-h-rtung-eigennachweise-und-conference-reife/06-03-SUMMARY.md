---
phase: 06-h-rtung-eigennachweise-und-conference-reife
plan: 03
subsystem: oauth
tags: [rfc8252, loopback, redirect-uri, policy-switch, fail-closed, cimd]

# Dependency graph
requires: []
provides:
  - "registry.ENV_CIMD als vierter Admin-Schalter, Default an"
  - "ClientPolicy.cimd_enabled, fail-closed aus dem CIMD-Schalter UND dem DCR-Schalter abgeleitet (T-06-15)"
  - "registry.loopback_match(requested, registered) -> str | None: die RFC-8252-7.3-Portregel als reine Funktion"
  - "provider.NextcloudOAuthProvider.also_accepting(address): eine Sicht auf den Provider fuer genau eine Anfrage, damit die Lockerung auch am SDK-Handler ankommt, ohne etwas zu schreiben"
affects: [CLIENT-05, AUTH-08, CLIENT-04]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ein abgeleitetes Policy-Feld statt eines zweiten gelesenen Schalters: cimd_enabled = _switch(env, ENV_CIMD, default=True) and dcr, ein Parser bleibt die einzige Wahrheit"
    - "Die Lockerung ist eine Sicht, keine Eintragung: model_copy fuer eine Anfrage, die Store-Zeile bleibt unberuehrt (T-06-19)"
    - "Ein Hilfsprediker (_comparable_host) fuer beide Seiten eines Vergleichs, damit eine Absage nicht auf der registrierten Seite vergessen werden kann"

key-files:
  created:
    - .planning/phases/06-h-rtung-eigennachweise-und-conference-reife/06-03-SUMMARY.md
  modified:
    - src/mcp_connector/oauth/registry.py
    - src/mcp_connector/oauth/consent.py
    - src/mcp_connector/oauth/provider.py
    - tests/unit/test_oauth_registry.py
    - tests/unit/test_oauth_consent.py
    - CHANGELOG.md
    - .planning/STATE.md

key-decisions:
  - "Die Portregel wirkt in consent.py an genau einer Stelle, aber der SDK-Handler vergleicht die Adresse ein zweites Mal (mcp/server/auth/handlers/authorize.py:180). Damit die eine Entscheidung dort ankommt, bekommt der Provider also_accepting(address): eine flache Kopie fuer eine Anfrage, deren get_client die eine bereits gematchte Adresse an das Client-Objekt haengt. Nichts wird gespeichert, die naechste Anfrage sieht die Registrierung wie vorher"
  - "loopback_match benutzt LOOPBACK_HOSTS (127.0.0.1, localhost, ::1) und nicht nur die IP-Literale aus RFC 8252 7.3: eine buchstabengetreue Umsetzung liesse Claude Code draussen, das zur Laufzeit localhost schickt, und D-35 laesst alle drei Namen ohnehin registrieren"
  - "Das Schema wird verglichen und nicht eingeschraenkt: welche Schemata ueberhaupt zulaessig sind, entscheidet D-35 in redirect_uri_allowed, das nach der Lockerung unveraendert auf der angefragten Adresse laeuft (T-03-41)"
  - "cimd_enabled ist ein eigener Schalter mit harter Kopplung an DCR statt derselbe Schalter: CIMD ist der Vorzugsweg der Spec 2026-07-28, darf aber ein abgeschaltetes DCR nicht umgehen; die Kopplung schlaegt den explizit gesetzten Schalter"
  - "__all__ wird per Gruppe auf Sortierung geprueft (Konstanten, dann Klasse, dann Funktionen) statt mit einem nackten sorted(): letzteres widerspricht der Ordnung, die ruff RUF022 in diesem Repo schreibt"
  - "CHANGELOG-Eintrag unter [Unreleased] fuer beides: die Portregel ist ab sofort nach aussen wirksam (ein lokaler Client verbindet sich, der vorher abgewiesen wurde), der Schalter ist eine neue Admin-Variable"

patterns-established:
  - "Wenn das SDK dieselbe Pruefung ein zweites Mal macht, wird die eigene Entscheidung als Objekt-Sicht fuer eine Anfrage weitergegeben, nicht als zweite Lockerung an der zweiten Stelle"

requirements-completed: []

# Metrics
duration: 25min
completed: 2026-08-20
---

# Phase 06 Plan 03: Loopback-Port und CIMD-Schalter Summary

Die RFC-8252-Paragraf-7.3-Portregel und der vierte Admin-Schalter stehen in der Policy-Schicht,
die es schon gab: `loopback_match` liefert die registrierte Adresse, auf die eine
Loopback-Anfrage passt, wenn ausschliesslich der Port frei ist, und `cimd_enabled` ist mit
abgeschaltetem DCR nachweislich `False`, auch wenn der CIMD-Schalter ausdruecklich auf `on`
steht.

## Was entstanden ist

| Datei | Inhalt |
|-------|--------|
| `src/mcp_connector/oauth/registry.py` | `ENV_CIMD = "NC_MCP_OAUTH_CIMD"` im Konstantenblock, viertes Feld `cimd_enabled` auf der unveraenderlichen `ClientPolicy` mit fail-closed-Ableitung, `loopback_match` neben `redirect_uri_allowed`, `_comparable_host` als gemeinsamer Praedikat-Helfer beider Vergleichsseiten, Modul-Docstring um die Begruendung des abgeleiteten Feldes erweitert |
| `tests/unit/test_oauth_registry.py` | 28 Tests mehr (67 -> 95): vier zum Schalter samt Kopplung und Tippfehlerfall, ein Unveraenderlichkeitstest fuer das abgeleitete Feld, ein Katalog aus 6 positiven und 21 negativen Loopback-Faellen, ein Test dass auf einen Treffer nichts geschrieben wird, ein `__all__`-Test; der Namens-Gate zaehlt jetzt `4` |
| `src/mcp_connector/oauth/consent.py` | `_refuse` liefert zwei Werte: die Seite und die eine Adresse, die die Portregel durchgelassen hat; die Regel wird an genau einer Stelle angewandt, im `except InvalidRedirectUriError`-Zweig, und `redirect_uri_allowed` laeuft danach unveraendert auf der angefragten Adresse |
| `src/mcp_connector/oauth/provider.py` | `also_accepting(address)` plus die eine Stelle in `get_client`, an der die Sicht wirkt: nach allen Pruefungen, damit Allowlist und Verfall die Registrierung sehen, wie sie auf der Platte steht |
| `tests/unit/test_oauth_consent.py` | 6 Tests mehr: der gemessene Claude-Code-Fall bis zur Zustimmungsseite samt gespeicherter Adresse, der Beleg dass die Registrierung unberuehrt bleibt, Host-Wechsel, nicht-Loopback mit abweichendem Port, D-35 nach der Lockerung, und eine Loopback-Anfrage ohne passende Registrierung |
| `CHANGELOG.md` | Zwei Eintraege unter `## [Unreleased]`: die Portregel (Changed) und der neue Schalter (Added) |

## Wie die Regel gebaut ist

**Nur der Port ist frei.** Schema, Host, Pfad und Query werden exakt verglichen, der Host
case-insensitiv wie im Nachbarn. Ein Host-Wechsel ist kein Port-Wechsel: `localhost` gegen
`127.0.0.1` bleibt eine Absage, und zwar in beide Richtungen. Fragment, Userinfo, ein
unparsbarer Host, ein Port ausserhalb 1 bis 65535 sind Absagen, und `_comparable_host` prueft
das auf beiden Seiten, damit eine Registrierung, die anders geschrieben wurde, nicht
stillschweigend milder behandelt wird als eine Anfrage.

**Die Reihenfolge in `consent.py` bleibt.** Erst der exakte SDK-Vergleich, dann, nur wenn der
mit `InvalidRedirectUriError` faellt, die Portregel; danach unveraendert
`redirect_uri_allowed(str(address))` auf der ANGEFRAGTEN Adresse (T-03-41). Ein Test belegt
diese Reihenfolge mit einer Registrierung, die ein von D-35 verbotenes Schema traegt: die
Portregel matcht, D-35 lehnt ab, das Ergebnis ist `E5`. Das Fehlerbild bleibt fuer jeden
Redirect-Fehler dasselbe, es gibt keinen neuen Code und keine Auskunft darueber, welche
Haelfte fiel (T-03-47, T-06-18).

**Weiter reist die angefragte Adresse samt Port.** Sie landet im Flow-Datensatz und damit im
Auth-Code, was der Grund ist, warum der Token-Endpunkt des SDK ohne Aenderung stimmt: er
vergleicht die `redirect_uri` der Token-Anfrage gegen den gespeicherten Wert des Codes
(`mcp/server/auth/handlers/token.py:164-183`), nicht gegen die Registrierung. Ein Test liest
den geschriebenen Flow-Datensatz nach und belegt `http://localhost:3118/callback`. Eine zweite
Lockerung im Token-Pfad gibt es nicht (T-06-20, Grep-Beleg unten).

**Nichts wird eingetragen.** Der Anti-Pattern des Plans ist im Docstring benannt und durch
zwei Tests abgedeckt: die uebergebene Liste bleibt unveraendert, und nach einem erfolgreichen
Lauf enthaelt `clients.metadata_json` weiter nur die portlose Adresse (kein `3118`).

## Der Schalter

`cimd_enabled = _switch(env, ENV_CIMD, default=True) and dcr`. Vier Faelle, jeder mit eigenem
Test und einem Namen, der den Satz traegt:

| Umgebung | `dcr_enabled` | `cimd_enabled` |
|----------|---------------|----------------|
| leer | True | True |
| `NC_MCP_OAUTH_CIMD=off` | True | False |
| `NC_MCP_OAUTH_DCR=off` | False | False |
| `NC_MCP_OAUTH_DCR=off`, `NC_MCP_OAUTH_CIMD=on` | False | False |
| `NC_MCP_OAUTH_CIMD=vielleicht` | True | True, plus Warnung mit dem Variablennamen |

`_switch` wurde nicht angefasst; der Tippfehlerfall und der Leerwert kommen von dort. Die
Deklaration im Manifest (`appinfo/info.xml`) gehoert zu 06-04, das sie in seinen
Akzeptanzgrenzen fuehrt: ohne sie reicht der Deploy-Daemon die Variable nicht durch.

## Zur CONTEXT.md-Bedingung von CLIENT-05

Die Bedingung lautet "erst messen, dann entscheiden". Die Messung, die sie erfuellt, ist der
in 06-RESEARCH.md dokumentierte Live-Abruf von Claude Codes echtem CIMD-Dokument (zwei
portlose Loopback-Adressen, Laufzeit-Port 3118, ueberschreibbar per
`MCP_OAUTH_CALLBACK_PORT`) plus der zitierte Upstream-Befund, nicht erst ein Rundlauf gegen
unsere Instanz: ein Rundlauf ohne die Portregel kann konstruktionsbedingt nur scheitern und
wuerde nichts Neues messen. Diese Auslegung ist bewusst. Der Live-Rundlauf in 06-09 bestaetigt
sie und liefert die Portspalte je Lauf in die Messdatei; erst dann wird CLIENT-05 abgehakt.

## Verifikation

| Prueflauf | Ergebnis |
|-----------|----------|
| `uv run --no-sync pytest tests/unit` | 2003 passed in 53,57 s |
| `uv run --no-sync pytest tests/unit/test_oauth_registry.py -q` | 95 gruen |
| `uv run --no-sync pytest tests/unit/test_oauth_consent.py -q` | 81 gruen |
| `uv run --no-sync ruff check .` | All checks passed |
| `uv run --no-sync ruff format --check .` | 171 files already formatted |
| `uv run --no-sync pyright` | 0 errors, 0 warnings, 0 informations |
| `uv run --no-sync vulture src scripts vulture_whitelist.py` | keine Ausgabe, Exit 0 |
| Vokabular-Gate | "archiv" in keiner geaenderten Datei, auch nicht im CHANGELOG-Eintrag |
| `pyproject.toml`, `uv.lock` | unveraendert (T-06-SC) |

Die Grep-Grenzen des Plans einzeln nachgezaehlt:

| Grenze | Ergebnis |
|--------|----------|
| `grep -c "NC_MCP_OAUTH_CIMD" src/mcp_connector/oauth/registry.py` | 1 |
| `grep -c "def loopback_match" src/mcp_connector/oauth/registry.py` | 1 |
| `grep -c "loopback_match" src/mcp_connector/oauth/consent.py` | 1 (der Aufruf; die Kommentarstelle nennt die Regel jetzt in Prosa) |
| `grep -rn "loopback_match" --include=*.py src/mcp_connector/ \| grep -v registry.py \| grep -v consent.py \| wc -l` | 0 |
| `grep -n "redirect_uris" src/mcp_connector/oauth/consent.py` | zwei Lesestellen, keine Zuweisung |

## Abweichungen vom Plan

### Automatisch behoben

**1. [Rule 3 - Blocker] Der SDK-Handler vergleicht ein zweites Mal, also brauchte die eine
Entscheidung einen Weg dorthin**

- **Gefunden bei:** Task 3, beim Lesen des SDK-Handlers vor der Implementierung
- **Problem:** Der Plan geht davon aus, dass `consent.py:236` die einzige Stelle ist, an der
  ein Request-Wert gegen die Registrierung verglichen wird. Fuer *unseren* Code stimmt das.
  Der Ablauf ist aber: `_refuse` laesst durch, danach laeuft
  `AuthorizationHandler.handle(request)`, und dieser Handler laedt den Client selbst
  (`self.provider.get_client(...)`) und ruft `client.validate_redirect_uri(...)` erneut
  (`.venv/Lib/site-packages/mcp/server/auth/handlers/authorize.py:180`). Eine Lockerung nur in
  `_refuse` haette also nichts bewirkt: die Anfrage waere durch unsere lesbare Pruefung
  gekommen und danach vom SDK mit `invalid_request` abgewiesen worden. Die Akzeptanzgrenze
  "erreicht die Zustimmungsseite statt E5" waere unerfuellbar gewesen.
- **Fix:** `NextcloudOAuthProvider.also_accepting(address)` in `provider.py`: eine flache
  Kopie des Providers fuer genau eine Anfrage, deren `get_client` die eine bereits gematchte
  Adresse per `model_copy` an das Client-Objekt haengt. `consent.py` baut damit fuer diese eine
  Anfrage einen `AuthorizationHandler`. Nichts wird geschrieben, die Store-Zeile bleibt
  unberuehrt (Test), die Ergaenzung passiert erst nach Allowlist- und Verfallspruefung, und die
  Regel selbst bleibt an einer Stelle. Die Alternative, die angefragte Adresse in
  `client.redirect_uris` zu schreiben, ist der vom Plan verbotene Anti-Pattern und wurde nicht
  gewaehlt.
- **Dateien:** `src/mcp_connector/oauth/provider.py` (nicht in `files_modified` des Plans),
  `src/mcp_connector/oauth/consent.py`
- **Commit:** 7b6eeaf

**2. [Rule 1 - Bug im Testentwurf] `__all__`-Sortierung wird per Gruppe geprueft**

- **Gefunden bei:** Task 1, erster Testlauf
- **Problem:** Die Akzeptanzgrenze "die Liste ist alphabetisch sortiert" als nacktes
  `sorted(registry.__all__)` geschrieben faellt, weil ruff RUF022 in diesem Repo die
  isort-Ordnung schreibt: Konstanten zuerst, dann Klassen, dann Funktionen. Ein Test, der die
  Formatierungsregel des Repos widerlegt, ist der falsche Test.
- **Fix:** Der Test prueft Mitgliedschaft von `ENV_CIMD`, Sortierung innerhalb der beiden
  Gruppen und die Gruppenreihenfolge; die Begruendung steht im Docstring.
- **Dateien:** `tests/unit/test_oauth_registry.py`
- **Commit:** ed8ed98

**3. [Rule 2 - Owner-Regel] CHANGELOG-Eintrag ergaenzt**

- **Gefunden bei:** nach Task 3
- **Problem:** Der Plan nennt `CHANGELOG.md` nicht, die Owner-Regel verlangt aber jede
  nutzerrelevante Aenderung unter `## [Unreleased]`. Anders als in 06-01 (reine Bausteine ohne
  Aussenwirkung) wirkt hier ab sofort etwas nach aussen: ein lokaler Client, der vorher
  abgewiesen wurde, verbindet sich.
- **Fix:** Ein `Changed`-Eintrag zur Portregel und ein `Added`-Eintrag zum Schalter, ohne
  Em-Dashes und ohne das verbotene Vokabular.
- **Dateien:** `CHANGELOG.md`
- **Commit:** 1fc9cbe

### Bewusst nicht getan

`appinfo/info.xml` und `.env.exapp.example` bleiben unberuehrt: die Deklaration des Schalters
ist Gegenstand von 06-04 und dort in den Akzeptanzgrenzen verankert. Der Token-Endpunkt wurde
nicht angefasst. `redirect_uri_allowed` wurde nicht angefasst.

## Was dieser Plan nicht tut

Kein CIMD-Abruf, kein Netzwerkverkehr, kein neues Paket, keine Store-Spalte, keine neue Route,
kein Eintrag im AS-Metadatendokument. `cimd_enabled` hat noch keinen Leser im Produktionscode:
das Advertising ist 06-04, der Zweig in `get_client` ist 06-05. Das ist der Zuschnitt, und es
ist der Grund, warum dieser Plan vor dem CIMD-Zweig steht: ohne die Portregel ist der
Kandidat-Client fuer AUTH-08 nicht erreichbar.

## Known Stubs

Keine. `loopback_match` und `cimd_enabled` tun vollstaendig, was ihre Docstrings sagen. Was
`cimd_enabled` fehlt, ist ein Aufrufer, und der ist ausdruecklich Gegenstand von 06-04 und
06-05.

## Threat Flags

Keine neue Angriffsflaeche ausserhalb des Threat-Registers dieses Plans. Die eine Neuerung an
einer Vertrauensgrenze ist `also_accepting`, und sie liegt innerhalb von T-06-16 und T-06-19:
sie traegt genau die Adresse weiter, die `loopback_match` gegen dieselbe Registrierung schon
gematcht hat, sie schreibt nichts, und sie lebt eine Anfrage lang. T-06-17 (Port-Squatting auf
Loopback) bleibt das benannte akzeptierte Restrisiko; sichtbar gemacht wird es auf der
Zustimmungsseite in 06-06.

## Requirements

Beide Requirements bleiben offen und werden hier bewusst nicht abgehakt:

- **CLIENT-05** ist implementiert, aber der Nachweis dieses Projekts ist eine Messdatei mit
  dem genommenen Port je Lauf, mindestens drei Laeufen und einem Lauf mit gesetztem
  `MCP_OAUTH_CALLBACK_PORT`. Das ist 06-09.
- **AUTH-08** braucht den CIMD-Zweig (06-05) und das Advertising (06-04); dieser Plan liefert
  nur seine Voraussetzung.

## Self-Check: PASSED

`06-03-SUMMARY.md` liegt auf der Platte. Die vier Commits stehen im Log (`ed8ed98`, `198294f`,
`7b6eeaf`, `1fc9cbe`), alle sechs geaenderten Quell- und Testdateien sind darin enthalten, und
der volle Unit-Lauf (2003 passed) wurde nach dem letzten Quellcode-Commit wiederholt.
