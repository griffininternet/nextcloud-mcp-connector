---
phase: 06-h-rtung-eigennachweise-und-conference-reife
plan: 04
subsystem: oauth
tags: [cimd, rfc8414, discovery, advertising, policy-switch, appapi-manifest]

# Dependency graph
requires:
  - "06-03: registry.ClientPolicy.cimd_enabled und registry.ENV_CIMD"
provides:
  - "metadata.metadata_routes(env, *, dcr_enabled, cimd_enabled): das Advertising ist eine Funktion des Schalters, keine Konstante"
  - "client_id_metadata_document_supported im AS-Dokument, per or None abwesend statt false, wenn der Schalter aus ist"
  - "entry_exapp verdrahtet policy.cimd_enabled aus derselben Policy, die provider.get_client befragt"
  - "appinfo/info.xml deklariert NC_MCP_OAUTH_CIMD, damit der Deploy-Daemon die Variable ueberhaupt durchreicht"
  - "Ein Manifest-Gate als Mengengleichheit: jede Variable, die der Code liest, ist deklariert, und umgekehrt"
affects: [AUTH-08]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ein optionales Dokumentfeld wird als `wert or None` gesetzt, weil exclude_none=True die Abwesenheit erzeugt: bei einem Protokollfeld ist abwesend etwas anderes als false"
    - "Ein Manifest-Gate als Mengengleichheit gegen die Konstanten des Codes statt als Wortliste: ein neuer Schalter kann nicht undeklariert bleiben und eine deklarierte Variable nicht ungelesen"
    - "Zwei Schalter, zwei unabhaengige Felder im Dokument; die Kopplung lebt in der Policy und nicht im Dokumentbauer, damit ein Policy-Fehler sichtbar bleibt statt kaschiert zu werden"

key-files:
  created:
    - .planning/phases/06-h-rtung-eigennachweise-und-conference-reife/06-04-SUMMARY.md
  modified:
    - src/mcp_connector/oauth/metadata.py
    - src/mcp_connector/entry_exapp.py
    - appinfo/info.xml
    - tests/unit/test_oauth_metadata.py
    - tests/unit/test_exapp_entry.py
    - tests/unit/test_exapp_env_setup.py
    - vulture_whitelist.py
    - .planning/STATE.md

key-decisions:
  - "Das Feld wird als `cimd_enabled or None` gesetzt und nicht als Bool: exclude_none=True laesst ein None aus dem Dokument verschwinden, und genau diese Abwesenheit ist der Zustand, in dem die Spec einem Client den Rueckfall auf DCR erlaubt. Ein false waere eine eigene Ankuendigung"
  - "Die Kopplung CIMD-an-DCR wird im Dokumentbauer NICHT wiederholt: sie lebt in ClientPolicy (06-03). Ein Matrixtest schreibt das unmoegliche Paar (dcr aus, cimd an) trotzdem auf, weil ein Bauer, der das registration_endpoint ueber den anderen Schalter fallen liesse, einen Policy-Fehler verstecken wuerde statt ihn zu zeigen"
  - "Der neue Manifest-Eintrag steht direkt hinter NC_MCP_OAUTH_DCR und nennt dessen Namen woertlich in der description: die zwei Registrierungswege stehen im Deploy-Dialog nebeneinander, und die Kopplung ist damit lesbar, ohne sich auf ein 'above' zu verlassen"
  - "Ein neues Gate prueft die deklarierten Variablennamen als Mengengleichheit gegen config.ENV_PUBLIC_URL und die vier registry-Konstanten, statt nur den neuen Namen zu suchen: das ist die Form, die den naechsten Schalter mitnimmt, und die teuerste stille Fehlerklasse dieses Pakets"
  - "Kein CHANGELOG-Eintrag und keine Doku-Aenderung in diesem Plan: der Schalter steht bereits unter [Unreleased] (06-03), und docs/oauth-setup.md gehoert laut Plan-Zuschnitt zu 06-06, das die CIMD-Strecke nach aussen beschreibt. Eine zweite Formulierung derselben Sache waere eine zweite Wahrheit"
  - "AUTH-08 bleibt offen: dieser Plan liefert die Ankuendigung, der aufloesende Zweig in provider.get_client ist 06-05 und die Zustimmungsseite 06-06"

patterns-established:
  - "Bei einem Protokollfeld ist die Abwesenheit eine Aussage: wer ein optionales Capability-Feld setzt, entscheidet zwischen 'nicht angekuendigt' und 'ausdruecklich verneint', und im Discovery-Dokument ist nur das erste ein Rueckfallpfad"
  - "Manifest-Deklarationen werden gegen die Konstanten des Codes geprueft, nicht gegen eine gepflegte Liste"

requirements-completed: []

# Metrics
duration: 20min
completed: 2026-08-20
---

# Phase 06 Plan 04: CIMD-Advertising am Schalter Summary

Das AS-Metadatendokument kuendigt Client ID Metadata Documents genau dann an, wenn der
Schalter an ist, und laesst das Feld sonst weg statt `false` zu sagen; der Schalter reist von
der Umgebung ueber die Manifest-Deklaration und die eine Policy des Prozesses bis in das
Dokument, mit Belegen am gebauten ASGI-Baum.

## Was entstanden ist

| Datei | Inhalt |
|-------|--------|
| `src/mcp_connector/oauth/metadata.py` | `metadata_routes` nimmt `cimd_enabled: bool = True` im Stil von `dcr_enabled` und reicht es an `_authorization_server_document` weiter; dort wird nach `build_metadata` und neben dem RFC-9207-Feld `metadata.client_id_metadata_document_supported = cimd_enabled or None` gesetzt. Der Funktions-Docstring traegt den Grund (Sackgasse ohne Rueckfall), der Kommentar an der Zuweisung traegt das Mittel (`exclude_none` erzeugt die Abwesenheit) |
| `src/mcp_connector/entry_exapp.py` | Eine Zeile Verdrahtung: `*metadata_routes(env, dcr_enabled=policy.dcr_enabled, cimd_enabled=policy.cimd_enabled)`, plus ein Absatz im Kommentarblock darueber, warum es dieselbe `policy` sein muss, die `provider.get_client` befragt |
| `appinfo/info.xml` | Fuenfter `<variable>`-Eintrag direkt hinter `NC_MCP_OAUTH_DCR`, mit `name`, `display-name` und `description`, ohne `<default>`-Element; der Erklaerkommentar darueber zaehlt jetzt fuenf Variablen und nennt den 500er des Stores bei leerem `<default>` |
| `tests/unit/test_oauth_metadata.py` | 11 Tests mehr (28 -> 39): Abwesenheit statt `false`, Ankuendigung bei eingeschaltetem Schalter, der Parameter-Default von der Signatur gelesen, `none` in `token_endpoint_auth_methods_supported` und der zeichengleiche `issuer` ueber beide Schalterstellungen, und eine Vier-Zeilen-Matrix, die `registration_endpoint` allein am DCR-Schalter haelt. `AS_FIELDS` traegt das neue Feld, also bleibt die Mengengleichheit gegen ein SDK-Upgrade scharf |
| `tests/unit/test_exapp_entry.py` | 4 Tests mehr (90 -> 94) am gebauten ASGI-Baum: `NC_MCP_OAUTH_CIMD=off` laesst das Feld fehlen, der Lieferzustand kuendigt es an, `NC_MCP_OAUTH_DCR=off` schliesst beide Wege, und die beiden Schalterpaare ergeben dasselbe Dokument. `registry.ENV_CIMD` steht jetzt in der `delenv`-Liste von `deployed`, damit eine Variable auf dem Entwicklungsrechner keinen Lauf verfaelscht |
| `tests/unit/test_exapp_env_setup.py` | 3 Gates mehr (143 -> 146): die deklarierten Namen als Mengengleichheit gegen die fuenf Konstanten des Codes, `name`/`display-name`/`description` je Eintrag nicht leer, und die `description` des CIMD-Eintrags nennt `NC_MCP_OAUTH_DCR` |
| `vulture_whitelist.py` | Das dritte nur geschriebene Feld des SDK-Modells, im bestehenden Block und mit erweiterter Begruendung |

## Warum `or None` und nicht `False`

Ein Client waehlt seinen Registrierungsweg in einer festen Reihenfolge: Vorregistrierung,
dann CIMD, wenn dieses Feld es anbietet, dann DCR, wenn ein `registration_endpoint`
existiert. Der Rueckfall auf den dritten Weg greift laut Spec nur, solange die Faehigkeit
**abwesend** ist. Ein Server, der `true` sagt und dann `invalid_client` antwortet, schickt
einen Client also in eine Sackgasse, aus der es keinen vorgesehenen Ausweg gibt, und ein
`false` waere eine eigene Ankuendigung statt eines Schweigens. `exclude_none=True` in
`model_dump` ist das etablierte Verhalten dieser Funktion, und `or None` benutzt es: bei
abgeschaltetem Schalter existiert der Schluessel im JSON nicht. Ein Test prueft `not in
document` und zusaetzlich, dass die Zeichenkette weder im Dokument noch als `false` im
Antworttext auftaucht.

Die zwei Felder, an denen Claude CIMD ueberhaupt erst waehlt, bleiben unangetastet und sind
belegt: `token_endpoint_auth_methods_supported` traegt weiter `none`, und `issuer` bleibt
zeichengleich der konfigurierten `public_url`, ohne angehaengten Schraegstrich. Beide werden
ueber beide Schalterstellungen geprueft, nicht nur im Lieferzustand.

## Warum die Deklaration im Manifest kein Beiwerk ist

Der AppAPI-Deploy-Daemon injiziert eine Variable in den Container genau dann, wenn das
Manifest sie deklariert; in Phase 3 gegen AppAPI 34.0.0 gemessen. Eine undeklarierte
Variable nimmt `occ app_api:app:register --env` widerspruchslos an und verwirft sie, der
Schalter stuende dauerhaft auf seinem Code-Default, und ein Admin haette keinen Weg zu sehen,
warum. Deshalb ist das neue Gate eine Mengengleichheit und keine Suche nach dem einen neuen
Namen: der naechste Schalter fliegt ohne Testaenderung auf, und eine deklarierte Variable,
die niemand liest, ist ebenfalls ein Versprechen, das die App nicht haelt.

Das `<default>`-Element bleibt weg. Ein leeres `<default>` waere schlimmer als keines:
AppAPI 34.0.3 exportiert es als Zeichenkette `Array` und der Store antwortet dem
Release-Upload mit 500 (Phase-05-Befund). Das bestehende Variablen-Gate bleibt gruen, und der
Erklaerkommentar im Manifest sagt jetzt selbst, warum.

## Verifikation

| Prueflauf | Ergebnis |
|-----------|----------|
| `uv run --no-sync pytest tests/unit` | 2080 passed in 54,26 s |
| `uv run --no-sync pytest tests/unit/test_oauth_metadata.py` | 39 gruen |
| `uv run --no-sync pytest tests/unit/test_exapp_entry.py` | 94 gruen |
| `uv run --no-sync pytest tests/unit/test_exapp_env_setup.py` | 146 gruen |
| `uv run --no-sync ruff check .` | All checks passed |
| `uv run --no-sync ruff format --check .` | 171 files already formatted |
| `uv run --no-sync pyright` | 0 errors, 0 warnings, 0 informations |
| `uv run --no-sync vulture src scripts vulture_whitelist.py` | Exit 0 (nach dem Whitelist-Eintrag) |
| `python -c "...ElementTree.parse('appinfo/info.xml')"` | manifest wellformed |
| Vokabular-Gate | "archiv" in keinem neuen Text (Manifest, Code, Tests) |
| `pyproject.toml`, `uv.lock` | unveraendert (T-06-SC) |

Die Grep-Grenzen des Plans einzeln nachgezaehlt:

| Grenze | Ergebnis |
|--------|----------|
| `grep -c "client_id_metadata_document_supported = True" src/mcp_connector/oauth/metadata.py` | 0 (kein Literal) |
| `grep -c "cimd_enabled=policy.cimd_enabled" src/mcp_connector/entry_exapp.py` | 1 |
| `grep -c "client_policy" src/mcp_connector/entry_exapp.py` | 2 (Import und ein Aufruf, unveraendert: keine zweite Policy) |
| `grep -c "NC_MCP_OAUTH_CIMD" appinfo/info.xml` | 1 |
| `git diff appinfo/info.xml` gegen `<version>` | keine Fundstelle; die drei `<description>`-Bloecke des Store-Textes unberuehrt |

## Abweichungen vom Plan

### Automatisch behoben

**1. [Rule 3 - Blocker] `vulture` faellt ueber das neu geschriebene SDK-Feld**

- **Gefunden bei:** Task 2, beim Vollcheck vor dem Commit
- **Problem:** `client_id_metadata_document_supported` wird gesetzt und nie zurueckgelesen,
  genau wie die zwei Nachbarfelder. `vulture` meldet das mit 60 Prozent Konfidenz, und dieses
  Projekt laesst `vulture` bei voller Konfidenz mit annotierter Whitelist laufen, also war der
  Lauf rot.
- **Fix:** `_.client_id_metadata_document_supported` in den bestehenden Block von
  `vulture_whitelist.py`, dessen Begruendung nun drei statt zwei Felder nennt.
- **Dateien:** `vulture_whitelist.py` (nicht in `files_modified` des Plans)
- **Commit:** 8dc953c

**2. [Rule 2 - Fehlende kritische Absicherung] Manifest-Gates in `test_exapp_env_setup.py`**

- **Gefunden bei:** Task 2
- **Problem:** Die Akzeptanzgrenzen des Plans fordern fuenf Eintraege mit je drei
  Kindelementen und die Nennung von `NC_MCP_OAUTH_DCR` in der neuen `description`. Als
  einmalig ausgefuehrter Grep waere das nach dem naechsten Plan wieder unbelegt, und die
  Fehlerklasse "Variable nicht deklariert, Deploy-Daemon verwirft still" ist genau die, die
  T-06-22 als `mitigate` fuehrt.
- **Fix:** Drei Gates in der Datei, in der die Manifest-Gates leben: Mengengleichheit der
  deklarierten Namen gegen `config.ENV_PUBLIC_URL` und die vier `registry`-Konstanten,
  Nichtleere von `name`/`display-name`/`description` je Eintrag, und die Nennung des
  gekoppelten Schalternamens.
- **Dateien:** `tests/unit/test_exapp_env_setup.py` (nicht in `files_modified` des Plans)
- **Commit:** 8dc953c

**3. [Rule 2 - Testisolierung] `registry.ENV_CIMD` in die `delenv`-Liste**

- **Gefunden bei:** Task 2
- **Problem:** `deployed` in `test_exapp_entry.py` raeumt die drei AUTH-07-Schalter aus
  `os.environ`, damit ein Wert auf dem Entwicklungsrechner keinen `main`-Lauf verfaelscht. Der
  vierte Schalter fehlte in dieser Liste, und ein gesetztes `NC_MCP_OAUTH_CIMD=off` haette ab
  jetzt still ein anderes Dokument gemessen.
- **Fix:** Ein Listeneintrag.
- **Dateien:** `tests/unit/test_exapp_entry.py`
- **Commit:** 8dc953c

### Bewusst nicht getan

`CHANGELOG.md` bleibt unberuehrt: der Schalter selbst steht seit 06-03 unter `## [Unreleased]`
und beschreibt bereits den Weg, den dieses Plan-Stueck ankuendigt; ein zweiter Eintrag waere
eine zweite Formulierung derselben Sache. `docs/oauth-setup.md` bleibt unberuehrt, weil der
Plan-Zuschnitt der Phase diese Datei 06-06 und 06-08 zuweist. `.env.exapp.example` bleibt
unberuehrt (Plan-Vorgabe: die Datei fuehrt keinen der `NC_MCP_OAUTH_`-Schalter). Die
`<version>` im Manifest bleibt unberuehrt, ein Store-Release ist nicht Teil dieses Plans.

## Was dieser Plan nicht tut

Er loest keine `client_id`-URL auf. Zwischen diesem Plan und 06-05 kuendigt der
Lieferzustand die Faehigkeit an, waehrend `provider.get_client` sie noch nicht bedient: das
ist der Zustand, den Pitfall 5 beschreibt, und er ist hier ein Zwischenstand im Phasenlauf,
kein Auslieferungszustand. Kein Release, kein Store-Upload und keine Doku-Aussage nach aussen
haengt an diesem Commit; der Weg wird in 06-05 (Zweig in `get_client`) und 06-06
(Zustimmungsseite) begehbar, und erst danach ist AUTH-08 abhakbar. Ein Betreiber, der die
Zwischenzeit ueberbruecken muss, setzt `NC_MCP_OAUTH_CIMD=off`, und genau dafuer ist der
Schalter jetzt deklariert.

## Known Stubs

Keine. `metadata_routes` tut vollstaendig, was ihr Docstring sagt. Was fehlt, ist der
Aufloeser hinter der Ankuendigung, und der ist ausdruecklich Gegenstand von 06-05.

## Threat Flags

Keine neue Angriffsflaeche ausserhalb des Threat-Registers dieses Plans. Das Dokument nennt
weiter nur oeffentliche URLs, Scopes und Methodenlisten (T-06-23 accept, Mengengleichheit auf
die Feldnamen haelt das scharf). T-06-21 ist durch `or None` plus `not in document`-Test
adressiert, T-06-22 durch die Deklaration plus das neue Mengengleichheits-Gate, T-06-24 durch
die unveraenderte Anzahl der `client_policy`-Fundstellen, T-06-25 durch das fehlende
`<default>`-Element und das bestehende Variablen-Gate.

## Requirements

**AUTH-08** bleibt offen und wird hier bewusst nicht abgehakt: die Ankuendigung ist die eine
Haelfte, der Zweig in `provider.get_client` (06-05) und die Zustimmungsseite (06-06) sind die
andere. Ein Requirement, dessen Nachweis ein verbundener Client ist, wird nicht von einem
Dokumentfeld erfuellt.

## Self-Check: PASSED

`06-04-SUMMARY.md` liegt auf der Platte. Die zwei Task-Commits stehen im Log (`8c18626`,
`8dc953c`), alle sieben geaenderten Quell-, Manifest- und Testdateien sind darin enthalten,
und der volle Unit-Lauf (2080 passed) wurde nach dem letzten Quellcode-Commit wiederholt.
