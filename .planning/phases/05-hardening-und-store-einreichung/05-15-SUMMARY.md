---
phase: 05-hardening-und-store-einreichung
plan: 15
subsystem: exapp
tags: [gap-closure, wr-01, wr-02, wr-03, purge, fail-closed, bootstrap, validation]

# Dependency graph
requires:
  - phase: 05-hardening-und-store-einreichung
    plan: 06
    provides: "den Purge-Pfad selbst: Reihenfolge Rueckgabe vor Leeren vor Schluessel loeschen, _guard, _forced, die Antwortfelder"
  - phase: 05-hardening-und-store-einreichung
    plan: 08
    provides: "die live gemessene Wire-Form der occ-Invocation, die Untergrenze jeder Verengung der Flag-Erkennung"
  - phase: 02-exapp-shell
    plan: 04
    provides: "scripts/bootstrap_exapp.sh mit json_info und den Validatoren require_port_number und require_registry_shape (IN-07)"
provides:
  - "purge.REVOKE_HINT plus der Abbruchzweig: Verbindungen vorhanden und keine einzige Rueckgabe gelungen laesst Tabellen und Datenschluessel unangetastet und antwortet purged: false"
  - "purge.TRUE_WORDS plus fail-closed _is_set: ein unbekanntes Wort ist ein Tippfehler, kein Sicherheitsschalter, und erzeugt genau eine Logzeile"
  - "_forced liest den Flag nur noch aus dem JSON-Body; der Query-Parameter-Zweig ist entfernt"
  - "require_url_shape in scripts/bootstrap_exapp.sh, aufgerufen im Hauptlauf vor jedem Weg zu json_info"
  - "docs/uninstall.md: Abschnitt 'When the purge stops on purpose' mit Bedeutung und Weg zurueck"
affects: [EXAPP-04, src/mcp_connector/exapp/purge.py, scripts/bootstrap_exapp.sh, docs/uninstall.md]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Die destruktivste Aktion einer App bricht ehrlich ab, wenn ihre Vorbedingung fehlt, statt halb zu laufen: die Zuordnung Verbindung zu App-Passwort ist mehr wert als ein abgeschlossener Lauf"
    - "Fail-closed als Positivliste: ein Schalter kennt die Werte, die ihn scharf stellen, und alles andere ist ein Tippfehler mit Logzeile (registry._switch, config_values._switch, jetzt auch purge._is_set)"
    - "Eine gemessene Wire-Form ist die Untergrenze jeder Verengung: der Regressionstest der Messung steht neben der neuen Regel, nicht an ihrer Stelle"
    - "grep -Eqz statt grep -Eq bei Shell-Validatoren: ohne -z passiert ein Wert mit Zeilenumbruch die Pruefung auf seiner ersten Zeile"

key-files:
  created: []
  modified:
    - src/mcp_connector/exapp/purge.py
    - tests/unit/test_exapp_purge.py
    - docs/uninstall.md
    - scripts/bootstrap_exapp.sh
    - tests/unit/test_exapp_env_setup.py

key-decisions:
  - "Die Grenze des Abbruchs liegt bei null gelungenen Rueckgaben und nicht bei einem Fehlschlag: ein Teilfehlschlag laeuft weiter und wird gezaehlt, sonst blockierte eine einzige kaputte Verbindung jede Deinstallation"
  - "Ein leerer Store bleibt ein vollstaendiger Lauf: revoked gleich 0 ohne Zeilen ist keine Stoerung, sondern nichts zurueckzugeben"
  - "FALSE_WORDS bleibt erhalten und wechselt die Rolle: es entscheidet nicht mehr ueber den Flag, sondern trennt die bewusste Absage (keine Logzeile) vom Tippfehler (eine Logzeile)"
  - "Der unbekannte Wert selbst steht nicht im Log (V7): die Zeile nennt den Optionsnamen und die verstandenen Schreibweisen"
  - "require_url_shape laeuft mit grep -Eqz, obwohl die Nachbarvalidatoren grep -Eq nutzen: das Muster soll den ganzen Wert sehen, sonst waere ein Wert mit Zeilenumbruch genau die Luecke, die WR-03 beschreibt"
  - "Die Fehlermeldung von require_url_shape nennt nur den Variablennamen, nicht den Wert: die oeffentliche Adresse kann aus einer Staging-Umgebungsdatei stammen"

patterns-established:
  - "Advisory-Funde eines Phasen-Reviews werden in einem eigenen Gap-Closure-Plan geschlossen, jeder mit einem Test, der ohne den Fix rot ist, und einem Kommentar, der den Fund beim Namen nennt"

requirements-completed: [EXAPP-04]

# Metrics
duration: 30min
completed: 2026-08-20
---

# Phase 05 Plan 15: Gap Closure WR-01, WR-02, WR-03 Summary

Die drei Advisory-Funde des Phasen-Reviews sind geschlossen: der Purge bricht ehrlich ab,
wenn keine einzige Rueckgabe eines App-Passworts gelang, er nimmt den Force-Flag nur noch in
den Formen an, die vorkommen, und die oeffentliche Adresse ist im Bootstrap so gepinnt wie
Port und Registry.

## WR-Funde

| Fund | Fix | Test |
|------|-----|------|
| WR-01: Purge leert Tabellen und loescht den Schluessel auch bei komplettem Rueckgabe-Fehlschlag | Abbruchzweig zwischen `_hand_back_every` und `_empty`: `rows` nicht leer und `revoked == 0` antwortet `purged: false` mit `connections`, `revoked`, `revoke_failures` und `REVOKE_HINT`, plus Fehlerzeile im Log; `_empty` und `crypto.delete_key` bleiben ungerufen | `test_a_failed_revocation_does_not_stop_the_loop_and_is_a_number` (Spion-Fixture `destructive`), `test_a_revocation_that_never_reaches_nextcloud_stops_the_purge_too`, Gegenproben `test_a_partly_failed_revocation_purges_and_counts_the_failure` und `test_a_purge_of_an_empty_deployment_is_a_clean_zero` |
| WR-02: `--force`-Erkennung zu permissiv | `TRUE_WORDS` als Positivliste, `_is_set` wertet nur `True`, `None`, Integer ungleich 0 und diese Woerter als gesetzt, unbekannte Woerter erzeugen genau eine Logzeile; der Query-Parameter-Zweig in `_forced` ist ersatzlos entfallen | `test_a_value_nobody_understands_is_not_a_yes_and_says_so_once`, `test_a_spelled_out_no_needs_no_log_line`, `test_the_flag_in_the_query_string_runs_nothing` (drei Faelle), vier neue Faelle in `test_a_body_without_the_force_flag_changes_nothing`, Regressionsschutz `test_every_shape_of_the_flag_appapi_may_send_is_accepted` |
| WR-03: `PUBLIC_URL` ungeprueft im JSON-Registrierungs-Payload | `require_url_shape` neben `require_registry_shape`, Muster `^https?://[A-Za-z0-9._:-]+(/[A-Za-z0-9._/-]*)?$` mit `grep -Eqz`, Aufruf im Hauptlauf direkt neben den beiden bestehenden Validatoren | neun neue Faelle in `test_the_registration_inputs_are_pinned_before_json_info`, `test_the_bootstrap_calls_every_registration_validator`, `test_every_registration_validator_runs_before_json_info_is_built` |

## Die uebernommene Wire-Form aus 05-08-MEASUREMENTS.md

Die live gemessene Invocation von AppAPI 34.0.0 transportiert den Flag als JSON-Boolean:
`{"occ": {"arguments": null, "options": {"force": true}}}` (Abschnitt 6.2 des Messprotokolls,
Quelle `ExAppOccService::buildCommand` plus `AppAPIService::prepareRequestToExApp`). Diese
Form beantwortet `_is_set` im Boolean-Zweig, also bevor `TRUE_WORDS` ueberhaupt befragt wird;
`TRUE_WORDS` traegt deshalb die Schreibweisen aus `oauth/registry.py` und
`exapp/config_values.py` (`1`, `true`, `yes`, `on`) als Untergrenze um die Messung herum und
nicht an ihrer Stelle. Der parametrisierte Fall "the measured shape of AppAPI 34.0.0" haelt
genau das fest.

## Tasks Completed

| Task | Name | Commit | Dateien |
|------|------|--------|---------|
| 1 | WR-01 und WR-02 im Purge-Pfad | `739848e` | `src/mcp_connector/exapp/purge.py`, `tests/unit/test_exapp_purge.py`, `docs/uninstall.md` |
| 2 | WR-03, die oeffentliche Adresse im Bootstrap pinnen | `9e21dc2` | `scripts/bootstrap_exapp.sh`, `tests/unit/test_exapp_env_setup.py` |

## Was ein Administrator jetzt sieht

Antwort bei komplettem Rueckgabe-Fehlschlag:

```
$ occ mcp_connector:purge --force
{"purged":false,"connections":2,"revoked":0,"revoke_failures":2,"hint":"Nothing was deleted. ..."}
```

`docs/uninstall.md` erklaert im neuen Abschnitt "When the purge stops on purpose", was das
bedeutet (Nextcloud war nicht erreichbar oder hat jede Rueckgabe verweigert, geloescht wurde
nichts) und was zu tun ist (Erreichbarkeit pruefen, Kommando erneut ausfuehren, erst danach
`app_api:app:unregister --rm-data`). Die Zeile `purged` der Feldtabelle nennt den dritten
Grund fuer `false` jetzt mit.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Fehlende kritische Funktionalitaet] `grep -Eqz` statt `grep -Eq` in `require_url_shape`**

- **Gefunden bei:** Task 2
- **Problem:** Das Verhalten des Plans verlangt ausdruecklich die Ablehnung eines Wertes mit
  Zeilenumbruch. `grep -Eq` prueft zeilenweise, also haette `https://ok.example.com\n"evil":1`
  auf seiner ersten Zeile bestanden und den Rest in den Payload getragen: genau die Luecke,
  die WR-03 beschreibt.
- **Fix:** `-z` liest den Wert als einen NUL-terminierten Datensatz, damit der Anker `$` das
  Ende des Wertes meint und nicht das Ende der ersten Zeile. Ein Testfall
  ("a public address with a second line") belegt es, der Kommentar an der Funktion nennt den
  Grund.
- **Dateien:** `scripts/bootstrap_exapp.sh`, `tests/unit/test_exapp_env_setup.py`
- **Commit:** `9e21dc2`

### Benannte Umbenennungen

**2. Zwei Testnamen sind gewandert, weil ihre alten Namen das neue Verhalten falsch
beschrieben hatten**

- `test_a_failed_revocation_does_not_stop_the_purge_and_is_a_number` heisst jetzt
  `test_a_failed_revocation_does_not_stop_the_loop_and_is_a_number`: die Schleife laeuft
  weiter (T-05-31), der Purge tut es bei null Rueckgaben ausdruecklich nicht mehr (WR-01).
  Der Docstring nennt WR-01 und was der Test vorher gepinnt hat.
- `test_a_revocation_that_never_reaches_nextcloud_is_a_number_too` heisst jetzt
  `..._stops_the_purge_too`.
- `test_the_bootstrap_calls_both_registration_validators` heisst jetzt
  `test_the_bootstrap_calls_every_registration_validator`, weil es drei Validatoren sind.

Keine weiteren Abweichungen: die informativen Funde IN-01 bis IN-06 wurden bewusst nicht
nebenbei mitgenommen und gehoeren nach Plan 05-16 als Backlog-Eintrag.

## Threat Flags

| Threat ID | Kategorie | Disposition | Umsetzung |
|-----------|-----------|-------------|-----------|
| T-05-57 | Repudiation, Denial of Service | mitigate | Abbruch mit `purged: false` und `REVOKE_HINT` bei `rows` nicht leer und `revoked == 0`; Spion-Test belegt, dass `_empty` und `crypto.delete_key` ungerufen bleiben; der Lauf ist nach Behebung der Stoerung wiederholbar |
| T-05-58 | Elevation of Privilege | mitigate | Positivliste `TRUE_WORDS`, Query-Parameter-Zweig entfernt, unbekannte Werte antworten `purged: false` mit Logzeile; die gemessene AppAPI-Form bleibt per Test angenommen |
| T-05-59 | Tampering | mitigate | `require_url_shape` vor `json_info`, Muster ohne Anfuehrungszeichen, Backslash, Leerzeichen und Zeilenumbruch, Test ueber den Skripttext und ueber die ausgefuehrte Funktion |
| T-05-60 | Information Disclosure | mitigate | `REVOKE_HINT` nennt nur den Weg, die Zahlen stehen als eigene Felder daneben; die Bestandstests `test_no_answer_names_an_account_a_client_or_a_credential` und ihr Log-Gegenstueck laufen auch ueber den neuen Abbruchpfad; der unbekannte Flag-Wert steht nicht im Log |
| T-05-SC | Tampering | accept | Keine Installation, `git diff --stat uv.lock` ist leer |

Keine neue Angriffsflaeche ausserhalb des Threat Models: es gibt keine neue Route, keinen
neuen Netzwerkpfad und keine Schemaaenderung. Beide Aenderungen verengen bestehende
Eingaben.

## Verification

| Gate | Ergebnis |
|------|----------|
| `uv run --no-sync pytest -q` | gruen (voller Lauf, keine Deselektion) |
| `uv run --no-sync pytest tests/unit/test_exapp_purge.py -q` | 61 gruen |
| `uv run --no-sync pytest tests/unit/test_exapp_env_setup.py -q` | 142 gruen |
| `uv run --no-sync ruff check .` | All checks passed |
| `uv run --no-sync ruff format --check .` | 166 files already formatted |
| `uv run --no-sync pyright` | 0 errors, 0 warnings |
| `uv run --no-sync vulture src scripts vulture_whitelist.py` | keine Meldung |
| `bash -n scripts/bootstrap_exapp.sh` | Exit 0 |
| `grep -n "query_params" src/mcp_connector/exapp/purge.py` | keine Fundstelle mehr |
| `git diff --stat uv.lock` | leer |

RED wurde vor jeder Implementierung belegt: neun rote Tests in `test_exapp_purge.py` vor
Task 1, neunzehn rote Faelle in `test_exapp_env_setup.py` vor Task 2.

## Self-Check: PASSED
