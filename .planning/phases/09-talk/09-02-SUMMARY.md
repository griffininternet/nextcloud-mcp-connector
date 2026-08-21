---
phase: 09-talk
plan: 02
subsystem: config
tags: [talk-04, declarative-settings, exapp-config, admin-switch, os-environ]

# Dependency graph
requires:
  - phase: 05-hardening-und-store-einreichung
    provides: "Die Declarative-Settings-Kette der fünf bestehenden Admin-Werte: form_scheme, CONFIG_KEYS, KEY_TO_ENV, SWITCH_KEYS, _switch, read_values, _resolved_env"
  - phase: 01-server-kern
    provides: "config.py als Env-Leser mit dem Signaturvorbild dns_rebinding_protection, D-20 und ALLOWED_MODULE_STATE"
provides:
  - "config.ENV_TALK_SEND und config.talk_send_enabled: der eine Leser des Schalters, Default an, ein unverständlicher Wert schaltet nichts ab"
  - "config._FALSE_VALUES neben _TRUE_VALUES, per Test deckungsgleich mit config_values und oauth/registry"
  - "Sechster Admin-Wert talk_send: Formularfeld (Checkbox, default True, kein sensitive), Overlay-Lesepfad, Manifest-Deklaration"
  - "ADMIN_FIELD_TALK_SEND_LABEL und ADMIN_FIELD_TALK_SEND_DESCRIPTION"
  - "Genau eine Schreibstelle auf os.environ im Produktionscode: der aufgelöste Schalterwert vor dem ersten Socket"
affects: [09-03 tools/talk.py, 09-04 docs/oauth-setup.md, 09-05 Ende-zu-Ende-Nachweis TALK-04, 10 SEC-01]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ein aufgelöster Admin-Wert wird beim Start in die Prozessumgebung exportiert, damit ein Werkzeug ihn pro Aufruf lesen kann (neu in dieser Codebasis, genau ein Schlüssel)"
    - "Ein Default-an-Schalter prüft die Falsch-Wertmenge, nicht die Wahr-Wertmenge, damit ein Tippfehler nichts still abschaltet"
    - "Die Zahl im Prosatext ist Teil des Vertrags: jede Stelle, die die Anzahl der Werte nennt, wird mit dem Wert nachgezogen"

key-files:
  created: []
  modified:
    - src/mcp_connector/config.py
    - src/mcp_connector/exapp/config_values.py
    - src/mcp_connector/exapp/admin_settings.py
    - src/mcp_connector/exapp/ui/strings.py
    - src/mcp_connector/entry_exapp.py
    - appinfo/info.xml
    - vulture_whitelist.py
    - tests/unit/test_config.py
    - tests/unit/test_exapp_config_values.py
    - tests/unit/test_exapp_admin_settings.py
    - tests/unit/test_exapp_entry.py
    - tests/unit/test_exapp_env_setup.py

key-decisions:
  - "Weg A der Recherche umgesetzt: der aufgelöste Wert wird beim Start nach os.environ geschrieben (entry_exapp.py Zeile 323), und talk_send_enabled liest ihn pro Aufruf; Weg B (pro Sendevorgang aus Nextcloud lesen) und Weg C (Wert per Header) sind im Kommentar über der Zeile namentlich verworfen"
  - "talk_send_enabled gibt value not in _FALSE_VALUES zurück und nicht value in _TRUE_VALUES: der Default ist an, also darf ein leerer und ein unverständlicher Wert nicht zu einem stillen Aus führen (T-09-13)"
  - "_FALSE_VALUES steht als eigene Konstante in config.py statt als Import aus config_values: config_values importiert config, die andere Richtung wäre ein Zirkelbezug; ein Test hält alle drei Modulpaare gleich"
  - "talk_send ist der sechste und letzte Eintrag von CONFIG_KEYS: die vier OAuth-Werte bleiben beieinander, weil registry.client_policy zwei davon als eine Antwort liest"
  - "ALLOWED_MODULE_STATE in tests/contract/test_no_destructive_calls.py bleibt bei zwei Einträgen und die Datei ist unverändert: os.environ ist die Prozessumgebung und kein Modul-Dictionary, und genau diese Abgrenzung steht im Kommentar über der Schreibstelle"
  - "TALK-04 bleibt Pending: der Wortlaut verlangt die Wirkung am Werkzeug samt Fehlersatz, und das Werkzeug entsteht erst mit Plan 09-03; dieser Plan liefert Schicht 1 und 2 von Erfolgskriterium 5"
  - "talk_send_enabled steht vorübergehend in vulture_whitelist.py und verlässt die Liste mit Plan 09-03, nach dem Vorbild von Plan 08-02 und 09-01"

patterns-established:
  - "Die eine begründete Ausnahme: eine Zeile, die einem Kommentar zwei Zeilen darüber widerspricht, benennt den Widerspruch, die Abgrenzung zur verletzten Regel, ihre Beschränkung und ihren Preis, und ein Quelltext-Test hält den Kommentarblock fest"
  - "Ein Test, der die Prozessumgebung verändern lässt, zeichnet die Variable vor dem Lauf mit monkeypatch auf (setenv plus delenv), weil monkeypatch nur zurücknimmt, was es selbst angefasst hat"

requirements-completed: []

# Metrics
duration: 17 min
completed: 2026-08-21
---

# Phase 9 Plan 02: Der Admin-Schalter des Sendewegs Summary

**Sechster Admin-Wert `talk_send` in der ganzen Declarative-Settings-Kette (Formularfeld als Checkbox mit Default an, Overlay-Lesepfad, Manifest-Deklaration ohne `<default>`), plus `config.talk_send_enabled` mit `not in _FALSE_VALUES` statt `in _TRUE_VALUES` und der einen begründeten Schreibstelle auf `os.environ`, über die ein Werkzeug den Schalter pro Aufruf lesen kann.**

## Performance

- **Duration:** 17 min
- **Started:** 2026-08-21T11:12:00Z
- **Completed:** 2026-08-21T11:29:00Z
- **Tasks:** 3
- **Files modified:** 12 (0 neu, 12 geändert)

## Accomplishments

- Es gibt genau einen Leser für den Schalter, und er kann nichts still abschalten. `config.talk_send_enabled` (config.py Zeile 329 bis 348) antwortet True ohne Variable, bei leerem Wert, bei einem Wert aus Leerzeichen und bei einem unverständlichen Wert wie `vielleicht`; nur eine Schreibweise aus `_FALSE_VALUES` antwortet False, unabhängig von Groß- und Kleinschreibung. Die eine Zeile, die nicht aus `dns_rebinding_protection` kopiert werden durfte, ist `return value not in _FALSE_VALUES`, und der Docstring sagt ausdrücklich, dass hier nicht `in _TRUE_VALUES` steht und warum (T-09-13).
- Die Schreibweisen sind jetzt per Test über drei Module gleichgesetzt: `config._TRUE_VALUES`/`_FALSE_VALUES` gegen `config_values.TRUE_VALUES`/`FALSE_VALUES` und gegen `registry._TRUE_VALUES`/`_FALSE_VALUES`. Bis heute war die Gleichheit nur als Kommentar in `config_values.py` behauptet und zwischen zwei der drei Module geprüft.
- Das Formular trägt sechs Felder in der Reihenfolge von `CONFIG_KEYS`, das sechste ist eine Checkbox mit `default: True` und ohne `sensitive` in irgendeiner Schreibweise (Schicht 1 von Erfolgskriterium 5). Die Entpackzeile in `form_scheme` nimmt sechs Namen aus `CONFIG_KEYS`, die Ids werden also weiterhin nicht ein zweites Mal geschrieben.
- Der Overlay-Lesepfad versteht den neuen Schalter ohne eine Zeile neuen Validierungscode: `talk_send` liegt in `SWITCH_KEYS`, `_usable_value` verzweigt schon darauf und `_switch` ist die fertige Prüfung. Eine OCS-Antwort mit `configvalue: "0"` ergibt `{"NC_MCP_TALK_SEND": "off"}`, ein unverständlicher Wert landet in `refused`, lässt die Umgebung stehen und die Logzeile nennt den Feldnamen und nie den Wert (Schicht 2, T-09-10).
- `NC_MCP_TALK_SEND` ist im Manifest deklariert, mit `display-name` und `description` und **ohne** `<default>`-Element, und die Mengengleichheit des bestehenden Gates ist um `config.ENV_TALK_SEND` erweitert. `<version>` und `<image-tag>` sind unberührt (`git diff appinfo/info.xml` zeigt keine Zeile mit einem der beiden Elemente).
- Der aufgelöste Wert erreicht die Prozessumgebung vor dem ersten Socket, mit genau einer Schreibstelle und einem 19-zeiligen Kommentarblock, der vier Dinge sagt (Widerspruch zum Kommentar darüber, Abgrenzung zu D-20, Beschränkung auf einen Schlüssel, Preis des Aktivierungszyklus) und Weg B sowie Weg C namentlich verwirft. Zwei Quelltext-Tests halten beides fest.
- Kein neuer Modulzustand: `tests/contract/test_no_destructive_calls.py` ist unverändert und `ALLOWED_MODULE_STATE` hat weiterhin genau zwei Einträge (`nextcloud/http.py::_clients`, `nextcloud/capabilities.py::_cache`).

## Task Commits

Each task was committed atomically:

1. **Task 1: ENV_TALK_SEND und talk_send_enabled in config.py** - `ce9f1fa` (feat)
2. **Task 2: Sechster Schlüssel, sechstes Formularfeld, zwei Texte und die Manifest-Variable** - `48a6b58` (feat)
3. **Task 3: Der aufgelöste Wert erreicht den Tool-Lesepfad** - `07817c0` (feat)

## Der genaue Ort der `os.environ`-Zeile

Für Plan 09-03, weil dort der Fehlersatz des Werkzeugs auf denselben Ort zeigt, und für Plan 09-05, weil dort der Ende-zu-Ende-Nachweis daran hängt:

`src/mcp_connector/entry_exapp.py`, in `main()`:

- Zeile 302: `resolved, refused = _resolved_env()`
- Zeile 304 bis 322: der Kommentarblock der Ausnahme
- Zeile 322: `if config.ENV_TALK_SEND in resolved:`
- Zeile 323: `os.environ[config.ENV_TALK_SEND] = resolved[config.ENV_TALK_SEND]`
- Zeile 325: `try:` mit `config.exapp_settings(resolved)`, also allen Prüfungen

Die Zeile liegt damit nach der Auflösung und vor jeder Prüfung und vor dem Bau der App. `grep -rn "os.environ\[" src/mcp_connector` liefert genau diese eine Zeile.

Der Ort, den ein Fehlersatz nennen soll, ist unverändert `strings.ADMIN_SETTINGS_PLACE` (`"Administration settings, Security, MCP Connector"`, strings.py Zeile 562), einmal buchstabiert, damit ein Umzug eine Änderung ist.

## Wortlaut der beiden neuen Texte

Für Plan 09-04, das die sechste Zeile der Feldtabelle in `docs/oauth-setup.md` daraus schreibt, und für Plan 09-03, dessen Fehlersatz denselben Ton treffen muss:

`strings.ADMIN_FIELD_TALK_SEND_LABEL` (Zeile 625):

```
Let assistant apps send Talk messages
```

`strings.ADMIN_FIELD_TALK_SEND_DESCRIPTION` (Zeile 632 bis 636), drei Aussagen und nichts mehr:

```
With this off, no assistant can send a Talk message through this connector, whatever an
account is allowed to do in Talk itself. Reading is not affected: conversations and their
history stay readable. A change takes effect after you disable and enable this app again.
```

Der letzte Satz ist der wörtlich schon dreimal vorhandene Aktivierungszyklus-Satz, unverändert übernommen.

`ADMIN_SETTINGS_DESCRIPTION` hat einen Satz dazubekommen, damit die Seite nicht nur von OAuth spricht: "The first five fields are about connecting an assistant app; the last one is not, it decides whether an assistant may send a Talk message through this app."

Die Manifest-Beschreibung folgt dem Ton der fünf bestehenden ("On unless set to off"):

```
The outgoing Talk channel of this app. On unless set to off. With it off no assistant can
send a Talk message through this connector, whatever an account is allowed to do in Talk
itself; reading conversations and their history is not affected.
```

## Die vier Testfälle des Weges

In `tests/unit/test_exapp_entry.py`, damit die Zeile beim nächsten Refactor nicht verschwindet:

1. `test_a_stored_talk_switch_of_off_reaches_the_process_environment`: Overlay mit `talk_send: "0"` ergibt nach dem Start `os.environ[config.ENV_TALK_SEND] == config_values.SWITCH_OFF` und `config.talk_send_enabled() is False`.
2. `test_a_stored_talk_switch_of_on_reaches_the_process_environment`: Overlay mit `"1"` ergibt `SWITCH_ON` und True, damit True nie nur die Abwesenheit der Schreibstelle ist.
3. `test_a_start_without_a_stored_talk_switch_leaves_the_variable_alone`: ohne Overlay-Wert ist die Variable nach dem Start nicht in `os.environ`, und die Antwort bleibt True.
4. `test_a_stored_talk_switch_wins_over_the_deploy_variable`: ein in der Deploy-Umgebung gesetztes `"1"` wird von einem gespeicherten `"0"` überschrieben, weil `_resolved_env` genau diese Rangfolge herstellt.

Dazu zwei Quelltext-Behauptungen: `test_the_entry_point_writes_exactly_one_key_into_the_process_environment` (genau eine Schreibstelle, sie schreibt `config.ENV_TALK_SEND`, und mindestens vier Kommentarzeilen stehen darüber) und `test_the_write_happens_before_the_application_is_built` (die Reihenfolge Auflösung, Export, `uvicorn.run`).

Alle sechs laufen über die bestehende `start`-Hilfsfunktion. `deployed()` zeichnet `config.ENV_TALK_SEND` vor dem Lauf mit `monkeypatch.setenv` plus `monkeypatch.delenv` auf, weil `monkeypatch` nur zurücknimmt, was es selbst angefasst hat: ohne diese zwei Zeilen hätte ein Wert, den `main` schreibt, den nächsten Test dieser Datei beeinflusst.

## Files Created/Modified

- `src/mcp_connector/config.py` - `ENV_TALK_SEND` (Zeile 47) in der ersten `NC_MCP_`-Gruppe, `_FALSE_VALUES` (Zeile 78) mit `#:`-Kommentar über beide Wertmengen, `talk_send_enabled` (Zeile 329 bis 348) nach der Signatur von `dns_rebinding_protection`.
- `src/mcp_connector/exapp/config_values.py` - `"talk_send"` als sechster Eintrag von `CONFIG_KEYS` mit Begründung der Position im `#:`-Kommentar, `KEY_TO_ENV["talk_send"] = config.ENV_TALK_SEND`, `SWITCH_KEYS` auf vier Schalter. Modul-Docstring, `_public_url` und `_config_values` nennen nicht mehr die Zahl fünf.
- `src/mcp_connector/exapp/admin_settings.py` - Entpackzeile auf sechs Namen (mehrzeilig, weil eine Zeile die Zeilenlänge gerissen hätte), sechster Feld-Block als Checkbox mit `default: True` und einer fünfzeiligen Begründung des Zustands. Modul-Docstring, `form_scheme`-Docstring und der `#:`-Kommentar über `ADMIN_SECTION_ID` nachgezogen.
- `src/mcp_connector/exapp/ui/strings.py` - `ADMIN_FIELD_TALK_SEND_LABEL` und `ADMIN_FIELD_TALK_SEND_DESCRIPTION`, beide sortiert in `__all__` (sonst schlägt das vulture-Gate zu), in Dateireihenfolge hinter dem `allowed_clients`-Paar, also in der Reihenfolge des Formulars. `ADMIN_SETTINGS_DESCRIPTION` um einen Satz erweitert.
- `src/mcp_connector/entry_exapp.py` - die eine Schreibstelle samt Kommentarblock in `main()`, plus ein Absatz im Docstring von `_resolved_env`, der auf sie verweist.
- `appinfo/info.xml` - sechster `<variable>`-Block ohne `<default>`-Element, plus ein Absatz im erklärenden Kommentar über `<environment-variables>`. `<version>` und `<image-tag>` unberührt.
- `vulture_whitelist.py` - Block für `talk_send_enabled` mit dem Plan, der ihn wieder entfernt. Ausserdem zwei stale Planangaben korrigiert (siehe Abweichungen).
- `tests/unit/test_config.py` - neun neue Testfunktionen zum Schalter (parametrisiert über beide Wertmengen, Groß- und Kleinschreibung, fehlend, leer, Leerzeichen, unverständlich, Prozessumgebung ohne Mapping) plus der Gleichsetzungstest über die drei Module.
- `tests/unit/test_exapp_config_values.py` - drei Tests auf sechs gezogen, `talk_send in SWITCH_KEYS` festgehalten, drei neue Fälle: `"0"` wird `off`, `"1"` wird `on`, fünf unverständliche Werte landen in `refused` und die Logzeile dieses Moduls nennt den Wert nicht.
- `tests/unit/test_exapp_admin_settings.py` - `test_the_five_fields_...` auf `test_the_six_fields_...` umbenannt und um `talk_send`/`checkbox` erweitert, plus zwei neue Tests: das sechste Feld einzeln (Typ, Default, Texte, kein `sensitive` im serialisierten Feld) und die zwei Aussagen seiner Beschreibung.
- `tests/unit/test_exapp_entry.py` - vier Wege-Tests plus zwei Quelltext-Behauptungen, `deployed()` zeichnet die Variable auf, zwei Kommentare auf sechs Werte nachgezogen.
- `tests/unit/test_exapp_env_setup.py` - `config.ENV_TALK_SEND` in der Mengengleichheit des Manifest-Gates, Docstring des Default-Gates auf sechs.

## Decisions Made

- **Weg A, nicht B und nicht C.** Der Kommentarblock über der Schreibstelle verwirft beide Alternativen namentlich: Weg C (Wert per Header durch die Middleware) scheitert daran, dass ein Header von aussen setzbar ist, Weg B (pro Sendevorgang aus Nextcloud lesen) an einem zusätzlichen Roundtrip je Sendevorgang, einem zweiten Fehlermodus und daran, dass die Antwort auf einen gescheiterten Lesevorgang fail closed sein müsste, was "an per Default" bei jeder Netzwerkstörung widerspricht.
- **`not in _FALSE_VALUES`.** Die Umkehrung von `dns_rebinding_protection`, und der Docstring benennt sie als solche. Dort schaltet die Variable eine standardmässig aktive Prüfung ab, hier schaltet sie eine standardmässig vorhandene Fähigkeit ab; in beiden Fällen darf ein unverständlicher Wert nicht die schärfere Richtung wählen, und "schärfer" heisst hier "an lassen".
- **Position von `talk_send` in `CONFIG_KEYS`: hinten.** Begründung im `#:`-Kommentar, in beiden Richtungen lesbar: `oauth_cimd` steht neben `oauth_dcr`, weil `registry.client_policy` die zwei als eine Antwort liest, und `talk_send` steht hinter allen vier OAuth-Werten, weil es von ihnen unabhängig ist.
- **Kein `sensitive`, geprüft am serialisierten Feld.** Der neue Einzeltest prüft `"sensitive" not in json.dumps(talk_send).lower()` und nicht nur `not in talk_send`, damit keine Schreibweise und keine Verschachtelung durchkommt. Der bestehende Test über den ganzen Körper bleibt zusätzlich.
- **`ADMIN_FIELD_TALK_SEND_*` in Formularreihenfolge in der Datei, in Sortierreihenfolge in `__all__`.** Der erste Entwurf legte die beiden Konstanten zwischen die `allowlist`- und die `allowed_clients`-Texte; das las sich wie ein OAuth-Feld. Sie stehen jetzt am Ende der Feldtexte, wie im Formular.
- **TALK-04 bleibt Pending.** Der Wortlaut der Anforderung verlangt ausdrücklich alle drei Schichten, einschliesslich "mit abgeschaltetem Schalter antwortet das Tool mit einem Fehlersatz samt nächstem Schritt". Das Werkzeug gibt es erst mit Plan 09-03. Gleiches Vorgehen wie bei TALK-01 bis TALK-03 in Plan 09-01 und bei TOOL-09 und SRV-03 in Phase 1.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `talk_send_enabled` ohne Produktionsaufrufer liess das vulture-Gate reissen**

- **Found during:** Task 1
- **Issue:** Das Akzeptanzkriterium von Task 3 verlangt ein grünes `uv run vulture src/mcp_connector vulture_whitelist.py`. Der einzige Produktionsaufrufer von `talk_send_enabled` ist die erste Zeile von `tools.talk.send`, und die entsteht erst mit Plan 09-03; vulture läuft in diesem Projekt bei voller Konfidenz und meldete die Funktion mit 60 Prozent.
- **Fix:** Ein Block in `vulture_whitelist.py` nach dem wörtlichen Vorbild der Blöcke aus Plan 08-02 und 09-01, mit Begründung und mit dem Plan, der den Namen wieder entfernt (09-03).
- **Files modified:** vulture_whitelist.py
- **Verification:** `uv run vulture src/mcp_connector vulture_whitelist.py` mit Exit-Code 0; ohne den Block meldet es genau diesen Namen.
- **Committed in:** `ce9f1fa` (Task 1)

**2. [Rule 1 - Bug] Zwei Blöcke der vulture-Whitelist nannten den falschen auflösenden Plan**

- **Found during:** Task 1
- **Issue:** Die Blöcke aus Plan 09-01 sagen wörtlich, dass `spreed_features`, `spreed_chat_max_length`, `get_rooms`, `get_messages` und `send_message` "leave this list with plan 09-02, the plan that adds tools/talk.py". `tools/talk.py` liegt aber in Plan 09-03 (Frontmatter von `09-03-PLAN.md`), und dieser Plan ändert an den fünf Namen nichts. Nach diesem Plan wäre die Aussage nachweislich falsch, und die Regel dieser Datei ist, dass jeder Eintrag seinen Auftrag richtig benennt.
- **Fix:** Beide Angaben auf `plan 09-03` korrigiert, Aussage sonst unverändert.
- **Files modified:** vulture_whitelist.py
- **Verification:** `grep -n "plan 09-0" vulture_whitelist.py` nennt nur noch 09-03 als auflösenden Plan; `uv run vulture ...` weiterhin Exit-Code 0.
- **Committed in:** `ce9f1fa` (Task 1)

**3. [Rule 3 - Blocking] Der Negativbeweis der Logzeile scheiterte an einer fremden Logzeile**

- **Found during:** Task 2
- **Issue:** Der neue Test "ein unverständlicher Wert wird abgelehnt und die Logzeile nennt den Wert nicht" las alle Records von `caplog`. Darin steht auch die INFO-Zeile von `httpx` mit der vollständigen Anfrage-URL (`/ocs/v2.php/apps/app_api/api/v1/...`), und die enthält Ziffern: der parametrisierte Fall `"2"` war rot, obwohl die Zeile unseres Moduls den Wert nicht nennt. Ein erster Versuch mit `record.getMessage() % record.args` scheiterte zusätzlich mit `TypeError`, weil `getMessage` die Argumente schon einsetzt.
- **Fix:** Der Test filtert die Records auf `record.name == "mcp_connector.exapp.config_values"`, mit einem Kommentar, der sagt warum. Die Behauptung ist damit über die Zeile dieses Moduls und nicht über das Logbuch des Testlaufs.
- **Files modified:** tests/unit/test_exapp_config_values.py
- **Verification:** `uv run pytest tests/unit/test_exapp_config_values.py -q` grün über alle fünf parametrisierten Werte.
- **Committed in:** `48a6b58` (Task 2)

**4. [Rule 3 - Blocking] Die Entpackzeile mit sechs Namen riss die Zeilenlänge**

- **Found during:** Task 2
- **Issue:** `public_url_field, dcr_field, cimd_field, allowlist_field, allowed_field, talk_send_field = CONFIG_KEYS` ist länger als die konfigurierte Zeilenlänge, `ruff format` hätte die Zeile ohnehin umgebrochen.
- **Fix:** Mehrzeilige Klammerform mit einem Namen pro Zeile. Die Aussage der Zeile bleibt: die Feld-Ids kommen aus `CONFIG_KEYS` und werden nicht ein zweites Mal geschrieben.
- **Files modified:** src/mcp_connector/exapp/admin_settings.py
- **Verification:** `uv run ruff check .` und `uv run ruff format --check .` grün.
- **Committed in:** `48a6b58` (Task 2)

**5. [Rule 2 - Missing critical] Ein Test, der `os.environ` verändert, hätte den nächsten Test beeinflusst**

- **Found during:** Task 3
- **Issue:** `main` schreibt jetzt in `os.environ`, und `monkeypatch` nimmt nur zurück, was es selbst angefasst hat. `monkeypatch.delenv(name, raising=False)` auf eine nicht gesetzte Variable zeichnet nichts auf, also wäre ein in einem Test geschriebenes `off` in allen folgenden Tests dieser Datei und aller danach laufenden Dateien noch gesetzt gewesen, mit `config.talk_send_enabled()` gleich False als Nebenwirkung.
- **Fix:** `deployed()` zeichnet die Variable vor dem Start mit `monkeypatch.setenv(config.ENV_TALK_SEND, "")` plus `monkeypatch.delenv(config.ENV_TALK_SEND)` auf; der Teardown stellt damit den ungesetzten Zustand wieder her. Kommentar mit der Begründung steht darüber.
- **Files modified:** tests/unit/test_exapp_entry.py
- **Verification:** `test_a_start_without_a_stored_talk_switch_leaves_the_variable_alone` ist auch bei umgekehrter Testreihenfolge grün; `uv run pytest -q` über die ganze Default-Auswahl grün.
- **Committed in:** `07817c0` (Task 3)

**6. [Rule 2 - Missing critical] Zwei Quelltext-Behauptungen statt nur der Plan-Verifikation**

- **Found during:** Task 3
- **Issue:** Die Akzeptanzkriterien "genau eine Schreibstelle" und "mindestens vier Kommentarzeilen darüber" standen nur als einmalige `verify`-Kommandos im Plan. Ein Kriterium, das kein Test hält, gilt beim nächsten Refactor nicht mehr, und genau diese Zeile ist die, die verschwindet.
- **Fix:** `test_the_entry_point_writes_exactly_one_key_into_the_process_environment` und `test_the_write_happens_before_the_application_is_built` in `tests/unit/test_exapp_entry.py`, nach dem Quellcode-Behauptungs-Muster der Familie.
- **Files modified:** tests/unit/test_exapp_entry.py
- **Verification:** Beide grün; die erste wird rot, wenn eine zweite Schreibstelle dazukommt oder der Kommentarblock entfällt.
- **Committed in:** `07817c0` (Task 3)

---

**Total deviations:** 6 auto-fixed (3 blockierend, 1 Bug, 2 fehlende kritische Absicherung)
**Impact on plan:** Kein Scope-Zuwachs. Drei Punkte sind Gates dieses Repos, die der Plan nicht vorhergesehen hat (vulture bei voller Konfidenz, die fremde `httpx`-Logzeile im `caplog`, die Zeilenlänge). Einer war eine falsche Aussage im Repo, die dieser Plan sichtbar gemacht hat. Zwei sind Absicherungen, die der Plan als einmalige Prüfung formuliert hatte und die jetzt Tests sind. Die einzige Abweichung von einem Akzeptanzkriterium ist der neue Whitelist-Eintrag, und er folgt dem dokumentierten Vorbild aus Plan 08-02 und 09-01.

## Issues Encountered

- Der Schalter-Export war der einzige Punkt der Phase ohne Vorbild in dieser Codebasis, und die Schwierigkeit lag nicht in der Zeile, sondern in ihrer Begründung: sie widerspricht einem Kommentar zwei Zeilen darüber ("never os.environ again"). Gelöst mit einem Kommentarblock, der den Widerspruch zuerst benennt, und mit einem Test, der genau diesen Block festhält, damit der nächste Leser die Zeile nicht als Schlamperei entfernt.
- `docs/oauth-setup.md` sagt weiterhin wörtlich "carries five fields" und hat eine Feldtabelle mit fünf Zeilen. Das ist bewusst nicht Teil dieses Plans (Plan 09-04 schreibt die sechste Zeile), aber es ist bis dahin eine falsche Zahl in der Dokumentation. Kein Test prüft sie heute.

## Known Stubs

Keine. Alle drei Schichten dieses Plans sind verdrahtet und getestet; die dritte Schicht von Erfolgskriterium 5 (die Wirkung am Werkzeug) ist ausdrücklich kein Stub dieses Plans, sondern der Inhalt von Plan 09-03, weil es dort erst ein Werkzeug gibt.

## Threat Flags

Keine neue sicherheitsrelevante Oberfläche gegenüber dem `<threat_model>` des Plans: kein neuer Netzwerkendpunkt, kein neuer Auth-Pfad, kein Dateizugriff und keine Schema-Änderung an einer Vertrauensgrenze. Die eine neue Grenze, der Übergang von der Prozessumgebung zum Werkzeug, ist als T-09-11 im Plan geführt und mit Weg A behandelt.

## User Setup Required

None - no external service configuration required. Der neue Schalter ist an per Default, eine bestehende Installation ändert ihr Verhalten nicht. Wer ihn abschalten will, setzt ihn im Formular unter `Administration settings, Security, MCP Connector` oder als Deploy-Variable `NC_MCP_TALK_SEND=0` und deaktiviert und aktiviert die App einmal.

## Next Phase Readiness

- Plan 09-03 kann `config.talk_send_enabled()` als erste Zeile von `tools.talk.send` aufrufen, vor `require_app` und vor jedem Client-Aufruf (Falle 10). Der Fehlersatz nennt `strings.ADMIN_SETTINGS_PLACE` und den Aktivierungszyklus; der Wortlaut der Feldbeschreibung oben ist die Tonvorlage.
- Plan 09-03 entfernt `talk_send_enabled`, `get_rooms`, `get_messages`, `send_message`, `spreed_features` und `spreed_chat_max_length` aus `vulture_whitelist.py`, sobald `tools/talk.py` sie aufruft. Das steht in allen drei Blöcken als Auftrag.
- Plan 09-04 schreibt die sechste Zeile der Feldtabelle in `docs/oauth-setup.md` und zieht den Satz "carries five fields" nach; der Wortlaut von Label und Beschreibung steht oben, der Satz zum Aktivierungszyklus ist derselbe wie bei den fünf anderen Feldern.
- Plan 09-05 kann den Ende-zu-Ende-Nachweis von TALK-04 auf Schicht 3 beschränken: Schicht 1 (Formular) und Schicht 2 (Overlay-Lesepfad) sind hier per Unit-Test belegt, und der Weg des Wertes in die Prozessumgebung ist es auch.
- Nicht Teil dieses Plans und weiterhin offen: `tools/talk.py`, `server/reg_talk.py`, der Live-Nachweis mit einer laufenden Nextcloud und die Doku. TALK-01 bis TALK-04 bleiben deshalb Pending.

## Self-Check

- `src/mcp_connector/config.py` FOUND (`ENV_TALK_SEND` Zeile 47, `_FALSE_VALUES` Zeile 78, `talk_send_enabled` Zeile 329)
- `src/mcp_connector/exapp/config_values.py` FOUND (`"talk_send"` in `CONFIG_KEYS`, `KEY_TO_ENV`, `SWITCH_KEYS`)
- `src/mcp_connector/exapp/admin_settings.py` FOUND (sechstes Feld Zeile 161 ff.)
- `src/mcp_connector/exapp/ui/strings.py` FOUND (Zeile 625 und 632, beide in `__all__`)
- `src/mcp_connector/entry_exapp.py` FOUND (Schreibstelle Zeile 323)
- `appinfo/info.xml` FOUND (`NC_MCP_TALK_SEND` Zeile 386, sechs Variablen, kein `<default>`)
- Commit `ce9f1fa` FOUND
- Commit `48a6b58` FOUND
- Commit `07817c0` FOUND
- `uv run ruff check .`, `uv run ruff format --check .`, `uv run pyright` (0 errors), `uv run vulture src/mcp_connector vulture_whitelist.py` (Exit 0) alle grün
- `uv run pytest -q` grün über die ganze Default-Auswahl; `tests/unit/test_config.py`, `test_exapp_config_values.py`, `test_exapp_admin_settings.py`, `test_exapp_env_setup.py`, `test_exapp_entry.py` einzeln grün
- `uv run pytest tests/contract/test_no_destructive_calls.py -q` grün, `ALLOWED_MODULE_STATE` hat 2 Einträge, die Datei ist unverändert (`git diff` leer)
- `uv run python scripts/check_tool_budget.py` Exit-Code 0, unverändert 12801 Bytes bei 18 Werkzeugen
- `grep -rn "os.environ\[" src/mcp_connector` liefert genau eine Zeile
- `git diff appinfo/info.xml` ohne Zeile mit `<version>` oder `<image-tag>`
- Kein Em-Dash, kein En-Dash und kein Zeichen oberhalb U+2100 in einer der zwölf geänderten Dateien

## Self-Check: PASSED

---
*Phase: 09-talk*
*Completed: 2026-08-21*
