---
phase: 05-hardening-und-store-einreichung
plan: 12
subsystem: exapp
tags: [gap-closure, measurement, appapi, 401, admin-values, lifecycle, restart-policy]

# Dependency graph
requires:
  - phase: 05-hardening-und-store-einreichung
    plan: 01
    provides: "das Administrator-Formular, dessen vier Werte ueber den gemessenen Kanal gelesen werden"
  - phase: 05-hardening-und-store-einreichung
    plan: 04
    provides: "die Startzeit-Aufloesung der Admin-Werte in entry_exapp._resolved_env, deren 401 hier gemessen wird"
  - phase: 05-hardening-und-store-einreichung
    plan: 08
    provides: "die Wegwerf-Topologie, die occ-Konvention und den Ausgangsbefund aus deferred-items.md"
  - phase: 05-hardening-und-store-einreichung
    plan: 11
    provides: "den Stand 0.1.1 mit Issuer-Regel und Rettungszweig, gegen den gemessen wurde"
provides:
  - "die gemessene Ursache des 401: der Lesekanal traegt, der Fehlschlag haengt allein am Aktivierungszustand der ExApp"
  - "der Gegenbeweis zur Folgerung aus deferred-items.md: ein Admin-Wert wirkt sehr wohl, naemlich nach Neustart oder Disable/Enable-Zyklus"
  - "die woertliche Restart-Policy des vom Deploy Daemon erzeugten Containers plus ein gemessener Selbstneustart"
  - "genau ein Fix-Weg fuer Plan 05-13 (Zweig N), mit Messnummern statt einer Vermutung"
affects: [EXAPP-04, .planning/phases/05-hardening-und-store-einreichung/05-13-PLAN.md]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Eine Ursache wird durch Isolation einer einzigen Variable belegt: derselbe Container, dasselbe Secret, dieselben Header, nur das enabled-Flag unterscheidet 200 von 401"
    - "Ein leeres Ergebnis beweist keinen funktionierenden Kanal: erst ein gesetzter Wert, der zurueckkommt, tut es"
    - "Ein Messwert der Restart-Policy wird nicht aus der Dokumentation abgeschrieben, sondern durch ein Prozessende von innen gegengeprobt"

key-files:
  created:
    - .planning/phases/05-hardening-und-store-einreichung/05-12-MEASUREMENTS.md
  modified: []

key-decisions:
  - "Zweig N statt der Selbstneustart-Variante: ein zweiter Lesevorgang am enabled=1-Hook waere ohne Wirkung, weil jeder Start einer aktivierten App die Werte bereits vollstaendig liest (M1, M2, M3)"
  - "Die Zuordnungsregel des Plans greift nicht, weil keine ihrer drei Vorbedingungen eingetreten ist; die Messung liegt in einem vierten Fall, deshalb entscheidet der Inhalt und nicht eine Vorbedingung, und die Regel wird im Dokument Punkt fuer Punkt gegengeprueft statt still uebergangen"
  - "Als Testwert wurde oauth_dcr=1 gewaehlt, also genau der Default aus registry.client_policy: der Wert macht das Overlay sichtbar, ohne das Verhalten der laufenden App zu aendern, und wurde am Ende wieder entfernt"
  - "Zwei Messungen mehr als geplant (M3b, M3c): ohne sie waere der Aktivierungszustand nur die wahrscheinlichste Erklaerung geblieben, nicht die gemessene"

patterns-established:
  - "Ein Messplan darf in einem Fall landen, den seine Zuordnungsregel nicht vorsah; dann wird die Regel woertlich geprueft, ihr Nichtgreifen protokolliert und die Wahl aus den Messungen begruendet"

requirements-completed: [EXAPP-04]

# Metrics
duration: 20min
completed: 2026-08-20
---

# Phase 05 Plan 12: Gap Closure, Ursachenmessung des 401 Summary

Der Startzeit-401 der Admin-Werte ist gemessen statt vermutet: der Lesekanal traegt, und der
Fehlschlag haengt allein daran, dass die App im Moment des Lesens noch nicht als aktiviert
gilt.

## Was entstanden ist

`.planning/phases/05-hardening-und-store-einreichung/05-12-MEASUREMENTS.md`, 366 Zeilen,
acht Abschnitte: gemessene Versionen und Aufbau, M1 bis M4 mit Kommando und roher Ausgabe,
die Ursache und der Zweig fuer Plan 05-13. Keine Quelldatei wurde angefasst
(`git status --porcelain src tests scripts` ist leer), die volle Test-Suite bleibt gruen.

Die Messungen liefen gegen eine frisch aufgebaute Wegwerf-Topologie (`compose.exapp.yml`,
Compose-Projekt `nc-mcp-exapp`, App 0.1.1 vom Stand nach Plan 05-11), Nextcloud 34.0.2 mit
AppAPI 34.0.0 und HaRP als Deploy Daemon. Die Instanzen `nc-mcp-test` und
`findling-nextcloud` wurden in keinem Kommando genannt.

| Messung | Frage | Ergebnis |
|---------|-------|----------|
| M1 | Traegt der Kanal bei aktivierter, laufender App? | 200, und ein gesetzter Wert kommt vollstaendig zurueck |
| M2 | Trifft ein blosser Container-Neustart den Lesevorgang? | Nein, INFO-Zeile ueber den gewonnenen Admin-Wert, keine 401-Zeile |
| M3 | Stoppt und startet der Disable/Enable-Zyklus den Container, und was liest der Start danach? | Derselbe Container wird gestoppt und gestartet, der Start liest sauber |
| M3b | Derselbe Container, gestartet waehrend die App deaktiviert ist | Die 401-Zeile ist zurueck |
| M3c | Derselbe Lesevorgang aus dem laufenden Prozess bei deaktivierter App | 401, `OCS 997, AppAPI authentication failed` |
| M4 | Wie erzeugt der Deploy Daemon den Container, und kommt er von allein zurueck? | `unless-stopped`, MaximumRetryCount 0; RestartCount 0 nach 1 nach einem Prozessende von innen |

## Ursache

**Der Lesekanal traegt. Der 401 haengt allein daran, dass die App im Moment des Lesens in
Nextcloud noch nicht als aktiviert gilt.**

M1 belegt den Kanal (200 plus zurueckgelieferter Wert). M2 und M3 belegen, dass der
Startzeitpunkt an sich unschuldig ist: beide Starts lesen sauber. M3b und M3c isolieren die
einzige verbleibende Variable, denn Container, Secret, Adresse und Header sind identisch und
nur das `enabled`-Flag unterscheidet sich: mit `enabled=0` antwortet dieselbe Ressource
401 mit `AppAPI authentication failed`. Die Gegenprobe im Quelltext der laufenden Instanz
nennt dieselbe Stelle, `AppAPIService::validateExAppRequestToNC` akzeptiert das Secret und
faellt danach ueber `!$exApp->getEnabled()`; ausgenommen sind nur `ex-app/state` und,
waehrend `install` oder `update`, `ex-app/status`, der Konfigurationspfad also nicht.

Damit ist die Vermutung aus `deferred-items.md` in ihrer Ursache bestaetigt und in ihrer
Folgerung widerlegt. Bestaetigt: zur Startzeit gilt die App noch nicht als aktiviert, weil
`enable` erst nach `init` kommt. Widerlegt ist der Satz "ein im Admin-Formular gesetzter
Wert wirkt auf dieser Topologie nie": der dokumentierte Weg wirkt gemessen, weil der
Disable/Enable-Zyklus denselben Container stoppt und startet und dieser Start die Werte
liest. Was als Defekt uebrig bleibt, ist eine `ERROR`-Zeile im einzigen Zeitfenster, in dem
dieser Fehlschlag der Normalfall ist und in dem es noch gar keinen Admin-Wert geben kann.

## Zweig fuer 05-13

**Zweig N.** Kein Selbstneustart, sondern eine ehrliche Logzeile fuer das Fenster vor der
Aktivierung plus der dokumentierte Disable/Enable-Zyklus als der Weg, auf dem ein gesetzter
Wert wirksam wird.

**Restart-Policy, woertlich:** `unless-stopped`, MaximumRetryCount 0. Ein Prozessende von
innen bringt den Container von allein zurueck (RestartCount 0 nach 1, neues StartedAt, App
bleibt aktiviert), ein von `disable` gestoppter Container bleibt liegen. Nach der
Buchstabenregel des Plans haette diese Policy auf die Selbstneustart-Variante gezeigt; ihre
Vorbedingung (die 401-Zeile beim Start nach `enable`) ist aber nicht eingetreten, und ein
Selbstneustart loest nichts, was M2 und M3 nicht schon loesen.

Die drei Vorbedingungen der Zuordnungsregel wurden woertlich geprueft und keine ist
eingetreten: M1 ist nicht 401, M2 zeigt die 401-Zeile nicht, M3 beim Start nach `enable`
ebenfalls nicht. Die Messung liegt in einem vierten Fall, den die Regel nicht vorsah, und
das steht so im Dokument.

## Abweichungen vom Plan

### Automatisch ergaenzt

**1. [Rule 2 - fehlende kritische Messung] M3b und M3c zusaetzlich gemessen**

- **Gefunden bei:** Task 1, nachdem M2 und M3 beide keine 401-Zeile zeigten
- **Problem:** Die Zuordnungsregel des Plans setzt voraus, dass mindestens einer der drei
  Faelle eintritt. Keiner trat ein, und ohne eine weitere Messung waere der
  Aktivierungszustand nur die wahrscheinlichste Erklaerung geblieben, also wieder eine
  Vermutung. Genau das sollte dieser Plan beenden.
- **Ergaenzung:** M3b startet denselben Container bei `enabled=0`, M3c misst dazu den
  Statuscode aus dem laufenden Prozess. Beide zusammen isolieren die einzige verbleibende
  Variable, und die Quelltext-Gegenprobe in AppAPI 34.0.0 bestaetigt sie.
- **Dateien:** nur `05-12-MEASUREMENTS.md` (Abschnitte 4.1 bis 4.3)
- **Commit:** `59f8f27`

**2. [Rule 2 - Aussagekraft der Messung] Ein Admin-Wert wurde fuer die Messung gesetzt**

- **Gefunden bei:** Task 1, M1
- **Problem:** M1 antwortete 200 mit leerer Liste, weil kein Admin-Wert gesetzt war. Ein
  leeres Ergebnis beweist nicht, dass ein gesetzter Wert ankommt, und ohne einen gesetzten
  Wert loggt ein erfolgreicher Startzeit-Lesevorgang gar nichts, womit M2 und M3 nicht
  zwischen Erfolg und stillem Fehlschlag unterscheiden koennten.
- **Ergaenzung:** `occ app_api:app:config:set mcp_connector oauth_dcr --value 1`, also genau
  der Default aus `registry.client_policy`, deshalb ohne Verhaltensaenderung. Am Ende des
  Laufs wieder entfernt (`app_api:app:config:delete`, Abschnitt 6).
- **Dateien:** keine Quelldatei; Zustand der Wegwerf-Topologie
- **Commit:** `59f8f27`

**3. [Rule 3 - blockierend] `MSYS_NO_PATHCONV=1` fuer jeden `docker exec` mit Container-Pfad**

- **Gefunden bei:** Task 1, erster M1-Aufruf
- **Problem:** Git Bash schrieb `/app/.venv/bin/python` in einen Windows-Pfad um, der Aufruf
  scheiterte mit Exit 127.
- **Ergaenzung:** `export MSYS_NO_PATHCONV=1` in jedem Messkommando, dieselbe Vorkehrung,
  die `scripts/bootstrap_exapp.sh` bereits fuer die Route-Regexe trifft.
- **Dateien:** keine
- **Commit:** `59f8f27`

Die Zuordnungsregel selbst wurde nicht umgeschrieben, sondern woertlich geprueft und ihr
Nichtgreifen protokolliert (Abschnitt 8 des Messprotokolls).

## Threat Flags

| Threat ID | Kategorie | Disposition | Wie er in diesem Lauf behandelt wurde |
|-----------|-----------|-------------|----------------------------------------|
| T-05-45 | Information Disclosure, Credentials im Messprotokoll | mitigate, eingehalten | Kein Header wurde abgedruckt, nur Zieladresse, Statuscode und Antwortkoerper der Konfigurationsressource; `grep -rniE "app_secret\|hp_shared_key\|app-passwort\|app password"` findet in `05-12-MEASUREMENTS.md` genau einen Treffer, und der ist der Variablenname `HP_SHARED_KEY` im Konventionsblock, kein Wert |
| T-05-46 | Tampering, ein Kommando trifft die falsche Instanz | mitigate, eingehalten | Jedes Kommando nennt `nc-mcp-exapp`, `nc-mcp-exapp-nc` oder `nc_app_mcp_connector` woertlich; `nc-mcp-test` und `findling-nextcloud` liefen unberuehrt weiter und kommen in keiner Zeile des Laufs vor |
| T-05-47 | Denial of Service, kaputte Wegwerf-Topologie | accept | Die Topologie steht am Ende sauber da: App `enabled`, Container `running`, Testwert entfernt, keine Konfigurationszeile mehr (Abschnitt 6) |

Kein neuer Angriffsflaechen-Fund: dieser Plan hat keine Quelldatei geaendert, keinen
Endpunkt hinzugefuegt und kein Schema beruehrt.

## Verifikation

| Pruefung | Ergebnis |
|----------|----------|
| `test -f .planning/phases/05-hardening-und-store-einreichung/05-12-MEASUREMENTS.md` | vorhanden |
| `grep -cE "^## " ...05-12-MEASUREMENTS.md` | 8, gefordert waren mindestens 6 |
| `grep -ciE "zweig (R\|N\|H)" ...` | 1, gefordert war genau eine gewaehlte Zweigbezeichnung |
| `grep -c "Em-Dash-Zeichen" ...` | 0 |
| Vokabular-Gate des Plans auf `...05-12-MEASUREMENTS.md` | 0 Treffer |
| `git status --porcelain src tests scripts` | leer |
| `uv run --no-sync pytest -q` | Exit 0, keine Fehler |
| `occ app_api:app:list` | `mcp_connector (MCP Connector): 0.1.1 [enabled]`, deploy und init auf 100 |

## Was Plan 05-13 jetzt weiss

1. Ein zweiter Lesevorgang am `enabled=1`-Hook und ein Cache sind unnoetig (M1, M2, M3).
2. Der 401 waehrend `enabled=0` ist der erwartete Ausgang und keine Stoerung (M3b, M3c plus
   Quelltext), jeder andere Fehlschlag dieses Lesevorgangs muss weiter `ERROR` bleiben.
3. Der Weg, auf dem ein geaenderter Wert wirksam wird, ist gemessen und ist genau der aus
   der Doku (M3).
4. Falls je ein Selbstneustart erwogen wird: er waere technisch moeglich, die Policy heisst
   `unless-stopped` (M4).

## Self-Check: PASSED

Alle im SUMMARY genannten Dateien existieren (`05-12-MEASUREMENTS.md`, `05-12-SUMMARY.md`),
beide Task-Commits stehen in `git log` (`59f8f27`, `c004d45`). Keine weiteren Behauptungen
ueber Dateien oder Commits in diesem Dokument.
