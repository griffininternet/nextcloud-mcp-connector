---
phase: 05-hardening-und-store-einreichung
plan: 13
subsystem: exapp
tags: [gap-closure, appapi, 401, admin-values, logging, docs]

# Dependency graph
requires:
  - phase: 05-hardening-und-store-einreichung
    plan: 04
    provides: "die Startzeit-Aufloesung der Admin-Werte in entry_exapp._resolved_env, deren 401-Zeile hier ehrlich wird"
  - phase: 05-hardening-und-store-einreichung
    plan: 11
    provides: "den Stand 0.1.1 mit https-oder-Loopback-Regel und Rettungszweig, auf dem dieser Fix aufsetzt"
  - phase: 05-hardening-und-store-einreichung
    plan: 12
    provides: "die Messung, die Zweig N gewaehlt hat (M1, M2, M3, M3b, M3c, M4)"
provides:
  - "der 401 des Fensters vor der Aktivierung ist eine INFO-Zeile mit Ausweg statt einer ERROR-Zeile"
  - "jeder andere Fehlschlag desselben Lesevorgangs bleibt ERROR, gehalten durch einen 403-Test"
  - "Doku und Code nennen dieselbe, gemessene Zahl an Disable/Enable-Zyklen: einen"
affects: [EXAPP-04, BL-06]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ein erwarteter Fehlschlag bekommt eine eigene Log-Stufe, und die Abgrenzung wird durch einen Nachbarstatus (403) im Test festgehalten, damit aus 'genau 401' nie 'irgendein 4xx' wird"
    - "Eine Logzeile fuer einen Normalfall traegt immer den Ausweg und die eine Lesart, unter der dieselbe Zeile doch ein Defekt waere"

key-files:
  created:
    - .planning/phases/05-hardening-und-store-einreichung/05-13-SUMMARY.md
  modified:
    - src/mcp_connector/exapp/config_values.py
    - tests/unit/test_exapp_config_values.py
    - docs/oauth-setup.md
    - .planning/phases/05-hardening-und-store-einreichung/deferred-items.md

key-decisions:
  - "Zweig N ausgefuehrt, Zweig-R/H-Anteile bewusst nicht gebaut: Overlay-Cache (CACHE_FILE, write_cache, cached_overlay, refresh_cache), vierte Registrierung im enabled=1-Hook und die vierstufige Vorrangregel entfallen, weil die Messung sie als wirkungslos belegt"
  - "Die Abgrenzung laeuft ueber genau 401 (httpx.codes.UNAUTHORIZED), nicht ueber die Statusklasse 4xx: nur dieser eine Ausgang ist gemessen erwartet"
  - "Die INFO-Zeile nennt den Fall, in dem dieselbe Zeile doch ein Defekt ist (ein Start nach enable heisst falsches App-Secret), damit das Herabstufen keine Diagnosefaehigkeit kostet"
  - "Die Vorrangregel bleibt dreistufig (Admin-Wert, Deploy-Umgebung, Default im Code), weil ohne Cache keine vierte Stufe existiert"

patterns-established:
  - "Ein Plan, der einen Zweig offenlaesst, wird nach der Messung auf den gewaehlten Zweig zusammengestrichen; die entfallenen Artefakte werden namentlich als Abweichung protokolliert statt still gebaut"

requirements-completed: [EXAPP-04]

# Metrics
duration: 15min
completed: 2026-08-20
---

# Phase 05 Plan 13: Gap Closure, 401-Fix Summary

Der 401 des Fensters vor der Aktivierung ist jetzt eine INFO-Zeile, die den Ausweg nennt, statt
einer ERROR-Zeile, die eine funktionierende Installation kaputt aussehen lässt; jeder andere
Fehlschlag desselben Lesevorgangs bleibt ERROR.

## Was entstanden ist

| Datei | Änderung |
|-------|----------|
| `src/mcp_connector/exapp/config_values.py` | Eigener Zweig für `401` in `read_values`: eine INFO-Zeile mit Begründung und Ausweg, dazu ein Kommentar mit der Messstelle und ein Absatz im Modul-Docstring |
| `tests/unit/test_exapp_config_values.py` | Neuer Test für das erwartete 401, plus `403` statt `401` in der Liste der Fehlschläge, die weiter ERROR bleiben müssen |
| `docs/oauth-setup.md` | Zwei Absätze in "Administrator settings": ein Zyklus (gemessen, nie zwei) und was die allererste Startzeile bedeutet |
| `deferred-items.md` | Die 401-Zeile aus 05-08 ist mit Verweis auf Messung und Fix geschlossen |

Die Logzeile lautet sinngemäß: der Lesevorgang lieferte 401, das ist die erwartete Antwort,
solange AppAPI diese App noch nicht auf `enabled` hat; die Deploy-Umgebung bleibt in Kraft, die
Werte werden beim nächsten Start erneut gelesen, ein im Formular gesetzter Wert wirkt nach genau
einem Disable/Enable-Zyklus. Der letzte Satz der Zeile nennt die eine Lesart, unter der dieselbe
Zeile doch ein Defekt ist: erscheint sie bei einem Start nach `enable`, stimmt das App-Secret des
Containers nicht mit dem überein, das Nextcloud gespeichert hat.

## Gewählter Zweig

**Zweig N**, gewählt in `05-12-MEASUREMENTS.md`, Abschnitt 8, auf Grundlage der Messungen M1
(200 bei aktivierter App, ein gesetzter Wert kommt vollständig zurück), M2 (bloßer
Container-Neustart liest sauber), M3 (Disable/Enable stoppt und startet denselben Container, der
Start danach liest sauber), M3b und M3c (identischer Container und identisches Secret, nur
`enabled=0`, und die Antwort ist 401 mit `OCS 997`) sowie der Quelltext-Gegenprobe in AppAPI
34.0.0 (`AppAPIService::validateExAppRequestToNC`, Abschnitt 4.3).

Daraus folgt für den Fix: ein zweiter Lesevorgang am `enabled=1`-Hook samt persistentem Cache
wäre ohne Wirkung, weil jeder Start einer aktivierten App die Werte bereits vollständig liest.
Ein Selbstneustart (Zweig R) wäre technisch möglich (M4: `unless-stopped`, RestartCount 0 auf 1
nach einem Prozessende von innen), löst aber nichts, was M2 und M3 nicht schon lösen. Übrig
bleibt genau eine Fehlklassifikation im Log, und genau die ist behoben.

## Vorrangregel

Sie bleibt dreistufig und unverändert, weil Zweig N keine vierte Quelle einführt:

1. **Der in Nextcloud gespeicherte Admin-Wert** (frisch beim Start gelesen). Er gewinnt, weil er
   der Wert ist, den die Administratorin zuletzt gesetzt hat, und weil ein geleertes Feld sonst
   nie wieder verschwinden würde.
2. **Die `NC_MCP_*`-Variable der Deploy-Umgebung.** Sie trägt jede Installation, die per `--env`
   aufgesetzt wurde, und sie trägt auch jeden Start, dessen Lesevorgang nichts geliefert hat.
3. **Der Default im Code.**

Die im Plan vorgesehene vierte Stufe (zuletzt erfolgreich gelesener Wert aus dem persistenten
Volume, zwischen Stufe 1 und Stufe 2) entfällt mit Zweig N: sie existiert nur zusammen mit dem
Cache, und der Cache ist gemessen überflüssig, weil der Startzeit-Lesevorgang einer aktivierten
App trägt (M1, M2, M3). Ein Wert wirkt damit weiterhin nach genau einem Disable/Enable-Zyklus,
und dieser Zyklus ist gemessen (M3), nicht angenommen.

## Abweichungen vom Plan

### Bewusst nicht gebaut (Zweig-R/H-Anteile, Auftrag des Orchestrators)

**1. Der Overlay-Cache im persistenten Volume (Plan-Task 1 vollständig)**

- **Entfallen:** `CACHE_FILE`, `write_cache`, `cached_overlay`, `refresh_cache`, die gemeinsame
  Hilfsfunktion `_overlay` und alle zugehörigen Tests
- **Warum:** Der Cache überbrückt ein Fenster, das gemessen nicht existiert. Jeder Start einer
  aktivierten App liest die Werte vollständig (M1, M2, M3); der Cache wäre eine zweite Quelle
  ohne Aufgabe, dazu eine neue Datei im Volume und eine neue Angriffsfläche (T-05-48).
- **Dateien:** keine

**2. Die vierte Registrierung im `enabled=1`-Hook (Plan-Task 2, Lifecycle-Hälfte)**

- **Entfallen:** der vierte `try`-Block in `exapp/lifecycle.py` samt Vergleich gegen die
  Closure-Umgebung und die Tests dazu; `lifecycle.py` ist in diesem Plan unverändert
- **Warum:** Ohne Cache hat ein zweiter Lesevorgang nichts, wohin er sein Ergebnis legen könnte,
  und der Prozess löst seine Werte laut D-20 genau einmal beim Start auf. Die Hälfte, die dieser
  Hook tragen sollte (die Nennung des Disable/Enable-Zyklus), steht jetzt dort, wo der Fehlschlag
  entsteht: in der Logzeile des Lesevorgangs selbst.
- **Dateien:** keine

**3. Die erweiterte Startauflösung in `entry_exapp` (Plan-Task 2, Entry-Hälfte)**

- **Entfallen:** `{**os.environ, **cached, **live}`, das Schreiben des Cache beim Start und die
  Quellenangabe in der INFO-Zeile; `entry_exapp.py` ist in diesem Plan unverändert
- **Warum:** Folgt aus 1. Es gibt keine gecachte Quelle, also auch keine Quelle zu benennen.
- **Dateien:** keine

**4. Die vierstufige Vorrangregel in der Doku (Plan-Task 3, halb)**

- **Entfallen:** die Cache-Stufe und der Satz über das Schicksal der Cache-Datei beim
  Deinstallieren
- **Ergänzt stattdessen:** die gemessene Zahl der Zyklen (einer) und eine Erklärung der
  allerersten Startzeile, die es vor diesem Plan nicht gab
- **Dateien:** `docs/oauth-setup.md`

### Automatisch ergänzt

**5. [Rule 2 - Diagnosefähigkeit] Die INFO-Zeile nennt den Fall, in dem sie doch ein Defekt ist**

- **Gefunden bei:** Task 1, beim Herabstufen von ERROR auf INFO
- **Problem:** Ein falsches App-Secret erzeugt denselben 401. Ein blindes Herabstufen hätte einen
  echten Konfigurationsfehler zu einer beiläufigen Zeile gemacht.
- **Ergänzung:** Der letzte Satz der Zeile sagt, dass dieselbe Zeile bei einem Start nach `enable`
  ein nicht übereinstimmendes App-Secret bedeutet; die Doku sagt denselben Satz.
- **Dateien:** `src/mcp_connector/exapp/config_values.py`, `docs/oauth-setup.md`
- **Commits:** `d213ce8`, `ba1ed00`

**6. [Rule 2 - Abgrenzung] `403` steht jetzt in der Liste der Fehlschläge, die ERROR bleiben**

- **Gefunden bei:** Task 1, beim Entfernen von `status_401` aus der parametrisierten Liste
- **Problem:** Ohne einen Nachbarstatus im Test hätte niemand gehalten, dass genau `401` der
  gemessene Erwartungsfall ist und nicht "irgendein 4xx".
- **Ergänzung:** `status_403` ersetzt `status_401` in der Liste; der Test besteht weiter auf einer
  ERROR-Zeile.
- **Dateien:** `tests/unit/test_exapp_config_values.py`
- **Commit:** `ef92acf`

**7. [Rule 2 - Buchführung] Die 401-Zeile in `deferred-items.md` ist geschlossen**

- **Gefunden bei:** Task 2, laut 05-12-SUMMARY für diesen Plan vorgesehen
- **Ergänzung:** Die Zeile trägt jetzt Messbefund, Fix, Commits und den Grund, warum die
  ursprüngliche Folgerung ("wirkt nie") widerlegt ist.
- **Dateien:** `.planning/phases/05-hardening-und-store-einreichung/deferred-items.md`
- **Commit:** `ba1ed00`

## Threat Flags

| Threat ID | Kategorie | Disposition im Plan | Stand nach Zweig N |
|-----------|-----------|---------------------|--------------------|
| T-05-48 | Tampering, wer die Cache-Datei schreiben kann, setzt `issuer` und Schalter | mitigate | **entfällt**: es gibt keine Cache-Datei, das Volume wird nicht zur neuen Vertrauensgrenze |
| T-05-49 | Elevation of Privilege, ein alter Cache hält einen abgeschalteten DCR-Schalter am Leben | mitigate | **entfällt**: kein Cache, jeder Start liest frisch, ein geleertes Feld verschwindet sofort |
| T-05-50 | Denial of Service, ein Fehler im `enabled=1`-Hook füllt `error` und deaktiviert die App | mitigate | **entfällt**: der Hook ist unverändert, es kommt keine vierte Registrierung dazu |
| T-05-51 | Denial of Service, Selbstneustart erzeugt eine Neustartschleife | mitigate | **entfällt**: kein Selbstneustart, Zweig R wurde nicht gebaut |
| T-05-52 | Information Disclosure, Admin-Werte im Log oder in einer weltlesbaren Datei | mitigate, eingehalten | Die neue INFO-Zeile nennt keinen Wert und keinen Schlüsselnamen aus der Antwort; der bestehende Test `test_no_request_or_response_value_reaches_a_log_record` deckt den Lesepfad weiter ab |
| T-05-SC | Tampering, Paketinstallationen | accept, eingehalten | Keine Installation, `git diff --stat uv.lock` ist leer |

Kein neuer Fund an Angriffsfläche: dieser Plan fügt keinen Endpunkt hinzu, ändert kein Schema,
schreibt keine Datei und ändert kein Verhalten außer der Stufe einer Logzeile.

## Verifikation

| Prüfung | Ergebnis |
|---------|----------|
| `uv run --no-sync pytest -q` | Exit 0, keine Fehler |
| `uv run --no-sync pytest tests/unit/test_exapp_config_values.py -q` | Exit 0 |
| `uv run --no-sync ruff check .` | All checks passed |
| `uv run --no-sync ruff format --check .` | 166 files already formatted |
| `uv run --no-sync pyright` | 0 errors, 0 warnings, 0 informations |
| `uv run --no-sync vulture src scripts vulture_whitelist.py` | keine Ausgabe |
| `uv run --no-sync python scripts/check_tool_budget.py` | grün |
| `uv run --no-sync pytest tests/unit/test_project_layout.py tests/unit/test_exapp_env_setup.py -q` | Exit 0 (dreizehn Routen im Manifest, kein neuer Modul-globaler Zustand) |
| `git diff --stat uv.lock` | leer |
| `grep -c '—\|–' docs/oauth-setup.md` | 0 |
| `grep -ci "archiv" docs/oauth-setup.md` | 0 |

## Was offen bleibt

Der Fix ist unit-belegt und nicht erneut gegen die Wegwerf-Topologie gefahren: die Aussage, die
er trifft, ist genau die, die 05-12 bereits gemessen hat (401 nur bei `enabled=0`, ein Zyklus
genügt), und der Codeunterschied ist die Stufe einer Logzeile. Wer den Effekt sehen will, sieht
ihn im Log des ersten Starts nach dem nächsten Deploy: dort steht statt der ERROR-Zeile die
INFO-Zeile mit dem Ausweg.

## Self-Check: PASSED

Alle im SUMMARY genannten Dateien existieren (`config_values.py`, `test_exapp_config_values.py`,
`docs/oauth-setup.md`, `deferred-items.md`, dieses SUMMARY), und alle drei Commits stehen in
`git log`: `ef92acf` (RED), `d213ce8` (GREEN), `ba1ed00` (Doku).
