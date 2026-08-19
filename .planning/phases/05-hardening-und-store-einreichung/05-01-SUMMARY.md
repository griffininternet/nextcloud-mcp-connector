---
phase: 05-hardening-und-store-einreichung
plan: 01
subsystem: infra
tags: [appapi, declarative-settings, exapp-config, ocs, admin-settings, one-click-install]

# Dependency graph
requires:
  - phase: 03-oauth-2-1
    provides: "der gemessene ExApp-Config-Lesepfad (POST /ex-app/config/get-values, Kleinschreibung der Antwortfelder) und die drei AUTH-07-Schalter in oauth/registry.py"
  - phase: 04-per-user-verwaltung-und-prepare-context
    provides: "die erste Declarative-Settings-Form samt fire-and-forget-Registrierung im enabled=1-Zweig und der Textkatalog exapp/ui/strings.py"
provides:
  - "exapp/config_values.py: Mehrschluessel-Lesepfad der ExApp-Konfiguration (read_values) plus Overlay in NC_MCP_-Schreibweise (admin_overlay), fail soft"
  - "exapp/admin_settings.py: zweite Declarative-Settings-Form mit section_type admin und vier echten Feldern, Feld-Ids gleich CONFIG_KEYS"
  - "Haken im enabled=1-Zweig: beide Formulare werden registriert, jedes im eigenen try"
  - "Textkonstanten fuer die Admin-Form und fuer den Setup-Zustand, den Plan 05-04 anzeigt"
affects: [05-04, 05-06, store-einreichung, docs/oauth-setup]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Mehrschluessel-Lesepfad der ExApp-Konfiguration, fail soft statt fail hard"
    - "Feld-Id einer Admin-Declarative-Settings-Form ist der Config-Schluessel (Single Source: CONFIG_KEYS)"
    - "Overlay in Env-Schreibweise statt Signaturaenderung an config.public_url"

key-files:
  created:
    - src/mcp_connector/exapp/config_values.py
    - src/mcp_connector/exapp/admin_settings.py
    - tests/unit/test_exapp_config_values.py
    - tests/unit/test_exapp_admin_settings.py
  modified:
    - src/mcp_connector/exapp/lifecycle.py
    - src/mcp_connector/exapp/ui/strings.py

key-decisions:
  - "Der Admin-Lesepfad faellt weich aus: jeder Fehler ist ein leeres Dict plus eine Logzeile, weil ein fehlender Admin-Wert nur 'nichts gesetzt' bedeutet, waehrend crypto._read_key hart scheitert, weil ein erfundener Data Key jede Autorisierung unlesbar macht"
  - "Eine unlesbare OCS-Antwort gilt nie als 'kein Wert': sie ist ein Fehler mit Logzeile, danach gilt die Deploy-Env weiter (fail closed beim Parsen, fail soft im Ergebnis)"
  - "Die Vorrangregel entsteht durch Auslassen: ein leerer oder ungueltiger Wert erscheint nicht im Overlay, also gewinnt NC_MCP_*-Env und danach der Code-Default"
  - "public_url wird zweifach geprueft (config.normalize_base_url plus die harte Regel nach registry.redirect_uri_allowed), weil dieser Wert zum issuer der AS-Metadaten und zur resource der PRM wird"
  - "Ein unbekannter Checkbox-Wert wird verworfen und geloggt, nie still auf einen Default gesetzt (dieselbe Begruendung wie registry._switch)"
  - "Die vier Feld-Ids der Admin-Form werden aus config_values.CONFIG_KEYS abgeleitet, damit Form und Lesepfad nicht auseinanderlaufen koennen; ein Test haelt die Gleichheit"
  - "Kein Feld traegt sensitive: AppAPI verschluesselt solche Werte zusaetzlich mit ICrypto und die ExApp bekaeme einen unlesbaren Blob"
  - "Jedes Feld traegt einen default, und die zwei Schalter zeigen den ausgelieferten Zustand (DCR an, Allowlist aus)"
  - "Die zweite Registrierung liegt in einem eigenen try-Block, nicht als zweite Anweisung im ersten: ein Fehlschlag der einen Form darf die andere nicht kosten"
  - "Ein JSON-Boolean als Checkbox-Wert wird beim Parsen zu 'true'/'false' normalisiert, damit der Schalterleser genau eine Sprache kennt"

patterns-established:
  - "Fail soft mit Logzeile: ein optionaler Konfigurationswert haelt niemals eine Installation an"
  - "Overlay-Vertrag: eine Abbildung NC_MCP_* auf String, damit bestehende Leser ohne Signaturaenderung Admin-Werte sehen"
  - "Textkatalog zuerst: die Texte fuer den Folgeplan entstehen im Katalog-Modul und sind ueber __all__ veroeffentlicht"

requirements-completed: []  # EXAPP-04 bleibt Pending, siehe Abschnitt "Requirements"

# Metrics
duration: 14min
completed: 2026-08-19
---

# Phase 05 Plan 01: Admin-Werte lesbar machen Summary

**Eine Admin-Declarative-Settings-Form mit vier echten Feldern plus ein Mehrschluessel-Lesepfad, der die gespeicherten Werte als Overlay in `NC_MCP_`-Schreibweise zurueckgibt und bei jedem Ausfall auf die Deploy-Env zurueckfaellt.**

## Performance

- **Duration:** 14 min
- **Started:** 2026-08-19T15:18:36Z
- **Completed:** 2026-08-19T15:32:40Z
- **Tasks:** 2 von 2
- **Files modified:** 6 (4 neu, 2 geaendert)

## Accomplishments

- Die vier Werte, die eine Store-Installation braucht (oeffentliche Adresse, Selbstregistrierung, Allowlist-Modus, erlaubte Clients), sind in Nextcloud setzbar und aus der ExApp lesbar, ohne dass eine Signatur im bestehenden Code sich aendert.
- Der Lesepfad haelt eine unerreichbare, langsame, ablehnende oder unlesbare Nextcloud aus: das Ergebnis ist dann leer, die Deploy-Env gilt weiter, und die Installation laeuft durch.
- Die gefaehrlichste der vier Eingaben ist die am haertesten gepruefte: eine Adresse mit Fragment, mit `user:pass@`, ohne Schema, ohne Host oder mit unmoeglichem Port wird verworfen und ohne ihren Inhalt geloggt, bevor sie zum `issuer` werden koennte.
- Der Sicherheitshinweis aus BL-06 steht im Beschreibungstext des Selbstregistrierungs-Feldes selbst, dort wo der Admin den Schalter sieht.
- 90 neue Tests, volle Suite 1633 gruen, alle Gates gruen (ruff, format, pyright, vulture, Tool-Budget, Manifest-Gate), `uv.lock` unberuehrt.

## Task Commits

Beide Tasks liefen als TDD-Zyklus, also je ein RED- und ein GREEN-Commit:

1. **Task 1: Mehrschluessel-Lesepfad und Overlay mit Vorrangregel** - `3609b90` (test), `b4a7f05` (feat)
2. **Task 2: Admin-Form mit vier Feldern und ihr Haken im enabled=1-Zweig** - `51eb484` (test), `ef755ed` (feat)

Ein REFACTOR-Commit war in beiden Zyklen nicht faellig: die GREEN-Fassung entstand direkt in der Form, die der Plan beschreibt.

## Files Created/Modified

- `src/mcp_connector/exapp/config_values.py` (neu) - `CONFIG_KEYS`, `KEY_TO_ENV`, `TRUE_VALUES`/`FALSE_VALUES`, `read_values` (ein POST fuer alle vier Schluessel) und `admin_overlay` (Validierung je Schluessel, Rueckgabe in Env-Schreibweise). Pfad, Verb und Feldname kommen per Import aus `oauth/crypto.py`, es gibt keine zweite Kopie.
- `src/mcp_connector/exapp/admin_settings.py` (neu) - `ADMIN_FORM_ID`, `form_scheme(env)` mit `section_type: "admin"`, `section_id: "security"`, `priority` 10 und vier Feldern, `register_admin_form(*, env=None)` mit dem Transportmuster von `settings_form.py` (App-Kontext, ein Versuch, wirft nie).
- `src/mcp_connector/exapp/lifecycle.py` (geaendert) - der `enabled=1`-Zweig registriert jetzt beide Formulare, jedes in seinem eigenen `try`; der Kommentar nennt Pitfall 11 der Phase 2 als Grund.
- `src/mcp_connector/exapp/ui/strings.py` (geaendert) - 14 neue Konstanten (Admin-Form plus Setup-Zustand fuer 05-04), alle in `__all__`.
- `tests/unit/test_exapp_config_values.py` (neu) - 57 Tests: Draht, drei Envelope-Formen, alle Fehlerpfade, Log-Hygiene, Validierung je Feld.
- `tests/unit/test_exapp_admin_settings.py` (neu) - 33 Tests: Schema Feld fuer Feld, `sensitive` nirgends im Rumpf, Feld-Ids gleich `CONFIG_KEYS`, beide Registrierungen bei `enabled=1`, Fehlertoleranz in beide Richtungen, Copy-Regeln.

## Verification

Alle Kommandos aus dem Plan, in derselben Reihenfolge:

| Gate | Ergebnis |
|------|----------|
| `pytest tests/unit/test_exapp_config_values.py -q` | 57 passed |
| `pytest tests/unit/test_exapp_admin_settings.py -q` | 33 passed |
| `pytest -q` (volle Suite) | 1633 passed, 82 deselected |
| `ruff check .` | All checks passed |
| `ruff format --check .` | 159 files already formatted |
| `pyright` | 0 errors, 0 warnings |
| `vulture src scripts vulture_whitelist.py` | leer |
| `python scripts/check_tool_budget.py` | gruen (Budget unberuehrt, dieser Plan legt kein Tool an) |
| `pytest tests/unit/test_exapp_env_setup.py -q` | gruen (Manifest-Gate unberuehrt, keine neue Route) |
| `git diff --stat uv.lock` | leer |

Jedes Akzeptanzkriterium beider Tasks ist durch mindestens einen Test belegt, darunter namentlich: genau ein POST mit `{"configKeys": [alle vier]}` auf einem Pfad, der auf `/ex-app/config/get-values` endet; `configkey`/`configvalue` in Kleinschreibung; Transportfehler, Timeout, 500, 401, Nicht-JSON und Muell-Envelope jeweils leeres Dict ohne Ausnahme; `public_url` mit Fragment, mit `userinfo`, ohne Schema, ohne Host und mit Port 0 bzw. 99999 nicht im Overlay; caplog auf DEBUG ohne App-Secret und ohne einen gelesenen Wert; `section_type` gleich `admin` mit den vier Feld-Ids in Reihenfolge und den Typen `url`, `checkbox`, `checkbox`, `text`; die Zeichenkette `sensitive` fehlt im gesendeten Rumpf; `/enabled?enabled=1` antwortet `{"error": ""}` mit `cache-control: no-store` auch wenn eine der beiden Registrierungen wirft; `/enabled?enabled=0` registriert nichts.

## Decisions Made

Die Entscheidungen stehen vollstaendig im Frontmatter (`key-decisions`). Drei davon sind die tragenden:

1. **Fail soft, aber fail closed beim Parsen.** Eine unlesbare Antwort ist kein leeres Ergebnis im Sinne von "nichts gesetzt", sondern ein Fehler mit Logzeile. Das Ergebnis nach draussen ist in beiden Faellen leer, der Unterschied ist die Logzeile, und genau die unterscheidet einen Ausfall von einer Konfiguration, die es nicht gibt (T-05-02).
2. **Die Vorrangregel entsteht durch Auslassen.** `admin_overlay` traegt nur Schluessel, deren Wert brauchbar ist. Damit ist "Admin-Wert vor Env vor Default" keine Bedingung an einer Stelle, sondern eine Eigenschaft der Datenstruktur, die Plan 05-04 nur noch anwenden muss.
3. **Die Feld-Ids der Form kommen aus `CONFIG_KEYS`.** Ein Formular, dessen Ids von den gelesenen Schluesseln abweichen, ist ein Formular, dessen Werte niemand liest, und der Fehler waere unsichtbar: die Registrierung gelingt, das Speichern gelingt, nur das Lesen findet nichts.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] Jedes Feld traegt einen `default`**

- **Found during:** Task 2
- **Issue:** Der Plan nennt je Feld Id, Typ, Label und Beschreibung. Die dokumentierte Feldform der Declarative Settings fuehrt zusaetzlich `default`, und AppAPIs `GetValueListener` liest genau dieses Feld als Rueckfallwert. Ohne `default` waere die Registrierung von der Kulanz der Server-Validierung abhaengig und der angezeigte Ausgangswert unbestimmt.
- **Fix:** `"default": ""` fuer die zwei Textfelder, `True` fuer `oauth_dcr` und `False` fuer `oauth_allowlist_only`, also der ausgelieferte Zustand aus D-35. Ein Test haelt fest, dass jedes Feld Titel, Beschreibung und `default` traegt.
- **Files modified:** `src/mcp_connector/exapp/admin_settings.py`
- **Verification:** `test_every_field_carries_a_title_a_description_and_a_default`
- **Committed in:** `ef755ed`

**2. [Rule 2 - Missing critical functionality] `register_admin_form` faengt auch eine unvollstaendige Deploy-Env**

- **Found during:** Task 2
- **Issue:** `config.exapp_settings` wirft `ToolError`, wenn eine AppAPI-Variable fehlt (IN-02). Das Vorbild `settings_form.register_settings_form` faengt das nicht selbst ab, verlaesst sich also auf den `try` im Lifecycle. Der Plan verlangt aber woertlich, dass diese Funktion "unter keinen Umstaenden" wirft.
- **Fix:** Ein `try` um `exapp_settings` mit einer Logzeile ohne Werte und `return`.
- **Files modified:** `src/mcp_connector/exapp/admin_settings.py`
- **Verification:** `test_a_broken_deploy_environment_is_not_an_exception`
- **Committed in:** `ef755ed`

**3. [Rule 3 - Blocking issue] Ein JSON-Boolean als Checkbox-Wert**

- **Found during:** Task 1
- **Issue:** Der Plan verlangt, dass `admin_overlay` die Formen `True`/`False` erkennt. `read_values` gibt aber Strings zurueck, und ein strikter String-Parser haette einen JSON-Boolean als unlesbare Antwort verbucht, also alle vier Werte verworfen.
- **Fix:** `_as_text` normalisiert einen Boolean beim Parsen zu `"true"`/`"false"`; jede andere Form ausser String bleibt unlesbar. Die Kleinschreibung erledigt zugleich die Grossschreibvarianten `"True"`/`"False"`.
- **Files modified:** `src/mcp_connector/exapp/config_values.py`
- **Verification:** `test_a_json_boolean_is_read_as_a_switch_value`, plus die Parametrisierung ueber alle 13 Schreibweisen
- **Committed in:** `b4a7f05`

### Bewusste Abweichung in der Testform (keine Verhaltensabweichung)

Der Plan schlaegt fuer den Beweis "`enabled=1` registriert BEIDE Formulare" zwei respx-Routen vor. Beide Registrierungen laufen ueber dieselbe OCS-Route, wo eine zweite respx-Route nie greifen wuerde. Der Beweis liegt deshalb auf dem Draht: zwei Aufrufe derselben Route, deren `formScheme.id` in der Reihenfolge `mcp_connector_settings`, `mcp_connector_admin` stehen. Das ist die stärkere Aussage, weil sie zusätzlich die Identitaet und die Reihenfolge festhält.

**4. [Rule 1 - Bug] EXAPP-04 wurde nicht abgehakt**

- **Found during:** Statusfortschreibung nach Task 2
- **Issue:** Die Plan-Frontmatter fuehrt `requirements: [EXAPP-04]`, und der State-Schritt hat den Haken in `.planning/REQUIREMENTS.md` gesetzt. EXAPP-04 ist aber die Store-Einreichung selbst, die dieser Plan nicht leistet.
- **Fix:** Die Aenderung an `.planning/REQUIREMENTS.md` zurueckgenommen, Begruendung im Abschnitt "Requirements" dieses Summaries.
- **Files modified:** keine (Ruecknahme)
- **Verification:** `grep EXAPP-04 .planning/REQUIREMENTS.md` zeigt weiter `[ ]` und `Pending`
- **Committed in:** dieser Plan-Metadaten-Commit

---

**Total deviations:** 4 (2x Rule 2, 1x Rule 3, 1x Rule 1) plus eine Testform-Praezisierung
**Impact on plan:** Kein Scope-Zuwachs. Alle drei Korrekturen betreffen Korrektheit gegenueber Komponenten, die wir nicht besitzen (AppAPI-Feldform, AppAPI-Deploy-Env, AppAPI-Antwortform).

## Issues Encountered

- `ruff` verlangte drei Nacharbeiten, alle im Test- und Katalogumfeld: RET501 (`return None` als einziger Rueckgabewert), RUF022 (`__all__` unsortiert nach dem Einfuegen des ADMIN-Blocks) und RUF001 (der En-Dash im Copy-Regel-Test war selbst ein mehrdeutiges Zeichen im Quelltext). Der letzte Punkt ist jetzt als `chr(0x2014)` bzw. `chr(0x2013)` geschrieben, damit der Test die verbotenen Zeichen pruefen kann, ohne sie zu enthalten.
- Kein Zirkelimport, obwohl `exapp/config_values.py` aus `oauth/registry.py` und `oauth/crypto.py` importiert: die `oauth`-Module, die ihrerseits `exapp` importieren (`consent`, `connections`, `connect`, `provider`, `metadata`, `throttle`), liegen nicht auf diesem Pfad, und `oauth/__init__.py` re-exportiert bewusst nichts. Geprueft, nicht angenommen.

## Requirements

**EXAPP-04 bleibt Pending, bewusst und gegen die Plan-Frontmatter.** Der Plan fuehrt
`requirements: [EXAPP-04]`, aber EXAPP-04 lautet "App ist im Nextcloud App Store eingereicht
(Zertifikat via CSR-PR, Signatur, info.xml-Validierung, Datenweitergabe-Disclosure)". Dieser
Plan liefert die erste Haelfte der Ein-Klick-Tauglichkeit, also eine Voraussetzung der
Einreichung, nicht die Einreichung. Ein Haken hier waere eine Zusicherung, die ein Blick in
den Store sofort widerlegt. `.planning/REQUIREMENTS.md` bleibt deshalb unveraendert; der
Haken gehoert an den Plan, der einreicht (dieselbe Linie wie AUTH-01, AUTH-05 und TOOL-06 in
den Phasen 1 und 2).


## Threat Flags

Der Threat-Register des Plans, Ist-Zustand nach diesem Plan:

| Threat ID | Kategorie | Disposition | Ist-Zustand |
|-----------|-----------|-------------|-------------|
| T-05-01 | Spoofing, Tampering | mitigate | **Umgesetzt.** `_public_url` prueft `config.normalize_base_url` plus Schema, Fragment, `userinfo`, Host und Portbereich; ein verworfener Wert erscheint nicht im Overlay und wird ohne seinen Inhalt geloggt. Acht Negativfaelle als Test. |
| T-05-02 | Tampering | mitigate | **Umgesetzt.** `_config_values` gibt `None` fuer jede Form zurueck, die es nicht sicher lesen kann; der Aufrufer macht daraus ein leeres Ergebnis MIT Logzeile, nie ein stilles "kein Wert". Sieben Fehlerformen als Test. |
| T-05-03 | Information Disclosure | mitigate | **Umgesetzt.** Keine Logzeile beider Module wiederholt einen Wert der Anfrage oder der Antwort; caplog-Tests auf DEBUG in beiden Testdateien pruefen App-Secret, base64-Token und gelesene Werte. |
| T-05-04 | Denial of Service | mitigate | **Umgesetzt.** Ein Versuch je Aufruf, keine Retry-Schleife, Timeouts aus `shared_client()`, jede Registrierung im eigenen `try`; `/enabled` antwortet in jedem Fall `{"error": ""}` mit `no-store`. |
| T-05-05 | Information Disclosure | mitigate | **Umgesetzt.** Kein Feld traegt `sensitive`; der Draht-Test prueft den gesamten Rumpf als Zeichenkette in Kleinschreibung, dazu ein Test auf die vollstaendige Typenliste und auf das Fehlen eines Buttons. |
| T-05-06 | Elevation of Privilege | mitigate | **Teilweise, wie geplant.** Der Hinweis steht im Beschreibungstext des `oauth_dcr`-Feldes ("On a public instance, either switch the allow list below on or switch this off"). Die Durchsetzung folgt in Plan 05-04. |
| T-05-SC | Tampering | accept | **Unveraendert.** Kein Paket installiert, `git diff --stat uv.lock` leer. |

Kein neuer Threat-Flag: dieser Plan legt keine Route an, keinen Auth-Pfad, keinen Dateizugriff und keine Schema-Aenderung. Die einzige neue eingehende Datenrichtung ist die OCS-Antwort des Lesepfades, und die ist als T-05-02 gefuehrt.

## Vertrag fuer 05-04

Woertlich, damit 05-04 nichts raten muss.

**Signatur des Overlays:**

```python
async def admin_overlay(*, env: Mapping[str, str] | None = None) -> dict[str, str]
```

- Schluessel sind Variablennamen, nicht Feld-Ids: `NC_MCP_PUBLIC_URL`, `NC_MCP_OAUTH_DCR`, `NC_MCP_OAUTH_ALLOWLIST_ONLY`, `NC_MCP_OAUTH_ALLOWED_CLIENTS` (die Abbildung ist `config_values.KEY_TO_ENV`).
- Enthalten ist nur, was gesetzt UND brauchbar ist. Ein leerer, ein unlesbarer und ein ungueltiger Wert fehlen; damit gewinnt die Deploy-Env, danach der Code-Default.
- Die zwei Schalter kommen als `"on"` oder `"off"` (`config_values.SWITCH_ON` / `SWITCH_OFF`), also in Schreibweisen, die `registry._switch` und `config._TRUE_VALUES` beide verstehen. Die Client-Liste kommt unveraendert (nur `strip()`), weil `registry._entries` die Zerlegung macht.
- Leeres Dict bei jedem Fehler. Diese Funktion wirft nicht, auch nicht bei unvollstaendiger Deploy-Env.
- Der Aufruf kostet genau einen Nextcloud-Roundtrip. `read_values(*, env=None) -> dict[str, str]` ist der rohe Weg dorthin, falls 05-04 die Feld-Ids statt der Variablennamen braucht.

**Weitere veroeffentlichte Namen:** `config_values.CONFIG_KEYS` (Tupel in Feld-Reihenfolge), `KEY_TO_ENV`, `TRUE_VALUES`, `FALSE_VALUES`, `SWITCH_ON`, `SWITCH_OFF`; `admin_settings.ADMIN_FORM_ID`, `form_scheme`, `register_admin_form`.

**Neue Textkonstanten in `exapp/ui/strings.py`,** alle in `__all__`:

| Name | Zweck |
|------|-------|
| `ADMIN_SETTINGS_TITLE` | Titel der Admin-Form |
| `ADMIN_SETTINGS_DESCRIPTION` | Beschreibung der Admin-Form (nennt Vorrang und den Wiederaktivieren-Schritt) |
| `ADMIN_SETTINGS_PLACE` | Ort der Form in Worten: "Administration settings, Security, MCP Connector" |
| `ADMIN_PUBLIC_URL_EXAMPLE` | `https://cloud.example.com/exapps/mcp_connector` |
| `ADMIN_FIELD_PUBLIC_URL_LABEL` / `ADMIN_FIELD_PUBLIC_URL_DESCRIPTION` | Feld 1 |
| `ADMIN_FIELD_DCR_LABEL` / `ADMIN_FIELD_DCR_DESCRIPTION` | Feld 2, traegt den BL-06-Hinweis |
| `ADMIN_FIELD_ALLOWLIST_LABEL` / `ADMIN_FIELD_ALLOWLIST_DESCRIPTION` | Feld 3 |
| `ADMIN_FIELD_ALLOWED_CLIENTS_LABEL` / `ADMIN_FIELD_ALLOWED_CLIENTS_DESCRIPTION` | Feld 4 |
| `SETUP_PUBLIC_URL_TITLE` | Setup-Zustand: Titel |
| `SETUP_PUBLIC_URL_BODY` | Setup-Zustand: nennt `ADMIN_SETTINGS_PLACE` und den Wiederaktivieren-Schritt |
| `SETUP_PUBLIC_URL_HINT` | Setup-Zustand: die Form der Adresse mit Beispiel |

Keiner dieser Texte traegt einen `str.format`-Platzhalter, es kommt also kein neunter Platzhalter in den Katalog.

## Known Stubs

Keine. Beide Module sind vollstaendig verdrahtet und getestet. Was fehlt, ist keine Attrappe, sondern der Vertragspartner: die gelesenen Werte wirken erst, wenn Plan 05-04 `admin_overlay` in die Umgebung der Leser legt. Bis dahin ist die Admin-Form ein Formular, dessen Werte gespeichert und lesbar sind, aber noch nichts umschalten. Das ist der im Plan beschriebene Schnitt ("Werte entstehen und sind lesbar. Plan 05-04 laesst sie wirken.") und keine offene Baustelle dieses Plans.

## User Setup Required

Keines fuer diesen Plan. Die Form erscheint nach dem naechsten `enabled=1`, also nach einem Deaktivieren und Aktivieren der App auf einer Instanz.

Der Live-Blick auf das gerenderte Formular ist noch nicht getan: die Aussagen dieses Plans sind auf dem Draht und in-process belegt, ein Browser war nicht beteiligt. Das gehoert zur Phase-5-Verifikation, zusammen mit dem schon vorhandenen offenen Punkt zu `/settings/user/security` aus Phase 4.

## Next Phase Readiness

Bereit fuer Plan 05-04: der Vertrag oben ist vollstaendig, die Textkonstanten fuer den Setup-Zustand liegen bereit, und die Vorrangregel ist getestet.

Bereit fuer Plan 05-06: `tests/unit/test_exapp_lifecycle.py` blieb absichtlich unangetastet, die Lifecycle-Aussagen dieses Plans leben in `tests/unit/test_exapp_admin_settings.py`. `appinfo/info.xml` wurde nicht angefasst, es gibt keine neue Route.

Ein Punkt fuer 05-04 zum Mitdenken: sobald ein Admin die Form einmal speichert, schreibt Nextcloud fuer beide Checkboxen einen konkreten Wert, der dann die Deploy-Env schlaegt. Das ist die gewollte Vorrangregel, aber eine Installation, die ihre Schalter bisher per `--env` gesetzt hat, sieht sie nach dem ersten Speichern aus der Form kommen. `docs/oauth-setup.md` sollte genau diesen Satz bekommen.

## Self-Check: PASSED

Alle vier neuen Dateien liegen auf der Platte, alle vier Task-Commits sind im Log, und die volle Suite laeuft gruen.

---
*Phase: 05-hardening-und-store-einreichung*
*Completed: 2026-08-19*
