---
phase: 05-hardening-und-store-einreichung
plan: 05
subsystem: testing
tags: [credential-flood, denial-of-service, harp-amplification, bruteforce, reverse-proxy, admin-runbook]

# Dependency graph
requires:
  - phase: 05-hardening-und-store-einreichung
    provides: "die wieder anfahrbare HaRP-Testtopologie samt bootstrap_exapp.sh und der Fixture aus 05-03"
  - phase: 03-oauth-2-1
    provides: "oauth/throttle.py (HaRP-Befund im Modulkopf, D-37) und oauth/verifier.py (nur positive Ergebnisse gecacht)"
  - phase: 02-exapp-shell
    provides: "appinfo/info.xml ohne bruteforce_protection auf /mcp (T-02-21) und die PUBLIC-Route /mcp"
provides:
  - "tests/integration/test_credential_flood.py: zwei getrennte Laeufe (ungueltiger Bearer, ungueltiges Basic) mit asyncio.gather, gemessen in Nextcloud-Requests pro Angreifer-Request, mit Pflicht-Ruecksetzung des Bruteforce-Zaehlers"
  - "docs/exapp-install.md, Abschnitt Security notes: die gemessenen Zahlen mit Datum plus Rate-Limit-Beispiele fuer Caddy und nginx und die zwei occ-Kommandos"
  - "die korrigierte Routentabelle des Installations-Runbooks (dreizehn Routen, Zugriffsklassen wie im Manifest)"
affects: [05-06, 05-09, 05-10, store-einreichung]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Lasttest ohne Lasttest-Werkzeug: asyncio.gather plus Semaphore ueber httpx, Grep-Gate gegen die vier verworfenen Werkzeuge"
    - "Die Messgroesse ist die Last beim Nachbarn (Nextcloud-Requests), nicht die eigene Antwortzeit"
    - "Kandidatenliste statt Annahme: der Zaehler wird fuer alle plausiblen Quelladressen gelesen und das Protokoll nennt, welche sich bewegt hat"
    - "Ein Test, der Instanzzustand aendert, liest den Vorzustand, stellt ihn im finally zurueck und protokolliert beides"
    - "Kontrollmessung als Bedeutungstraeger: derselbe Flut ohne Credential kostet null, damit haengt die Verstaerkung nachweislich am Header"

key-files:
  created:
    - tests/integration/test_credential_flood.py
    - .planning/phases/05-hardening-und-store-einreichung/05-05-MEASUREMENTS.md
  modified:
    - docs/exapp-install.md

key-decisions:
  - "Gemessen wird in Nextcloud-PHP-Runden pro Angreifer-Request, nicht in Millisekunden: die Antwortzeiten des eigenen Containers waren im Lauf unauffaellig, waehrend die Last vollstaendig bei Nextcloud landete (Quotient 1,00)"
  - "Der Test schaltet den Bruteforce-Waechter fuer die Messung ein und legt den vorherigen Wert im finally zurueck: der Bootstrap schaltet ihn aus, und ein leerer Zaehler waere sonst ein Artefakt der Fixture und keine Aussage ueber Nextcloud"
  - "Die Quelladresse wird nicht angenommen, sondern aus einer Kandidatenliste gemessen: die Eintraege liegen auf der HaRP-Adresse, nicht auf der des Angreifers, also teilen alle Nutzer aller ExApps hinter diesem Proxy einen Zaehler"
  - "Der Test spricht mit docker exec und festen Containernamen statt mit docker compose exec: jeder compose-Aufruf gegen compose.exapp.yml verlangt HP_SHARED_KEY in der Umgebung (WR-11), und der messende Prozess hat mit diesem Schluessel nichts zu tun"
  - "Beide Laeufe laufen einmal pro Modul in einer modulweiten Fixture mit asyncio.run: die Laeufe sind teuer und aendern Instanzzustand, also lesen alle fuenf Aussagen dieselbe Messung statt je eine eigene zu erzeugen"
  - "Kein Codefix am Connector: /mcp bleibt undrosselt (D-37), und die Messung liefert dafuer den Grund statt einer Ausnahme, weil nur der Reverse Proxy den Request abweisen kann, bevor HaRP Nextcloud fragt"
  - "Die Kontrollmessung ohne Authorization-Header gehoert zum Befund: zwanzig anonyme Requests kosten null PHP-Runden, deshalb kann die Regel im Proxy genau die Requests treffen, die Credentials tragen"

patterns-established:
  - "Ein Befund gegen die eigene Entscheidung wird protokolliert, nicht wegassertiert: der Test sagt in seinem Modulkopf, dass sein Ergebnis eine Zahl fuer die Doku ist und keine Zusicherung ueber eine Drosselung"
  - "Zahlen in der Doku nennen ihren Befehl und ihr Datum, und eine veraltete Messung auf derselben Seite wird als veraltet markiert statt geloescht"

requirements-completed: []  # AUTH-03 stand schon auf Complete; EXAPP-04 braucht die Einreichung selbst

# Metrics
duration: 25min
completed: 2026-08-19
---

# Phase 05 Plan 05: Negativ-Credential-Lasttest und Admin-Empfehlung Summary

Der Preis eines Flutangriffs mit ungueltigen Anmeldedaten ist jetzt eine gemessene Zahl:
**eine vollstaendige Nextcloud-PHP-Runde pro Angreifer-Request** (Quotient 1,00 in beiden
Laeufen), null bei einem Request ohne `Authorization`-Header, und Bruteforce-Eintraege
ausschliesslich bei ungueltigem Basic, die auf der Adresse von HaRP landen und damit alle
Nutzer aller ExApps hinter diesem Proxy zusammen drosseln.

## Was entstanden ist

**`tests/integration/test_credential_flood.py`** mit zwei getrennten Laeufen ueber je 200
Requests auf `/exapps/mcp_connector/mcp`, 20 gleichzeitig (`asyncio.gather` plus
`asyncio.Semaphore`, kein Werkzeug von aussen). Der Modulkopf sagt, was gemessen wird und was
das Ergebnis nicht ist: eine Zahl fuer `docs/exapp-install.md`, keine Zusicherung ueber eine
Drosselung, die `/mcp` bewusst nicht traegt (D-37, T-02-21).

Um jeden Lauf herum stehen vier Messungen: die Zeilenzahl im Zugriffs-Log des
Nextcloud-Containers, die Teilmenge davon mit `GET /index.php/apps/app_api/harp/user-info`
(die Nachfrage, die HaRP fuer jeden `Authorization`-Header stellt), der Bruteforce-Zaehler von
fuenf Kandidaten-Adressen vor dem Lauf und derselbe danach. Der Healthcheck des Compose-Files
wird in jeder Zaehlung abgezogen, weil er Verkehr der Fixture ist.

Fuenf Aussagen, jede als eigener Test:

| # | Aussage | Wie sie belegt wird |
|---|---------|---------------------|
| 1 | Der Bearer-Flut wird sauber abgelehnt | 200 Antworten, alle 401, kein 5xx, kein Request ohne Antwort |
| 2 | Der Basic-Flut wird sauber abgelehnt | 200 Antworten, alle im 4xx-Bereich |
| 3 | Jeder Angreifer-Request kostet eine Nextcloud-Runde | 200 von 200 Requests erzeugen eine `user-info`-Anfrage, in beiden Laeufen |
| 4 | Nur Basic fuellt den Bruteforce-Zaehler | Bearer-Zuwachs auf allen fuenf Adressen 0, Basic-Zuwachs 27 auf der HaRP-Adresse |
| 5 | Die Instanz bleibt nicht gedrosselt | Nach `security:bruteforce:reset` sind alle fuenf Kandidaten 0 |

Zwei Eigenschaften der Wegwerf-Topologie musste der Test dabei behandeln. Der Bootstrap
schaltet `auth.bruteforce.protection.enabled` aus, weil dieser Waechter eine Eigenschaft einer
unerreichbaren Instanz ist; der Test liest den Wert, schaltet ihn fuer die Messung ein und legt
ihn im `finally` zurueck (live gegengeprobt: nach dem Lauf steht wieder `false`). Und jeder
`docker compose`-Aufruf gegen `compose.exapp.yml` verlangt `HP_SHARED_KEY` in der Umgebung,
also spricht der Test mit `docker exec` und den festen Containernamen und nennt die
compose-Schreibweise in der ersten Zeile seines Protokolls.

**`docs/exapp-install.md`, Abschnitt "Security notes for production"** bekommt den
Unterabschnitt "A flood of invalid credentials is amplified against Nextcloud": die
Ergebnistabelle mit Datum und Befehl, die Erklaerung beider Credential-Formen, der Satz warum
`/mcp` undrosselt bleibt, je ein Rate-Limit-Beispiel fuer Caddy (mit dem ehrlichen Hinweis,
dass `rate_limit` kein Modul eines Standard-Builds ist) und nginx in der Form, in der
`docs/spike-discovery.md` seine Proxy-Regeln fuehrt, und die zwei occ-Kommandos zur Beobachtung
und Ruecksetzung samt dem Hinweis, nach welcher Adresse ein Admin fragen muss.

## Messprotokoll

Vollstaendige Rohmessungen mit allen Befehlen und Antworten:
`.planning/phases/05-hardening-und-store-einreichung/05-05-MEASUREMENTS.md`. Alles am
**19.08.2026**, Nextcloud 34.0.2, AppAPI 34.0.0, HaRP release, ExApp `mcp_connector 0.1.0
[enabled]`.

| Zeit (UTC) | Befehl | Ergebnis |
|-----------|--------|----------|
| 17:00:50 | `export HP_SHARED_KEY=$(openssl rand -hex 32) && docker compose -f compose.exapp.yml up -d --wait` | vier Container healthy |
| 17:07:42 | `bash scripts/bootstrap_exapp.sh` (Schluessel aus dem Container zurueckgelesen) | Fixture aus 05-03 wiederverwendet, `mcp_connector 0.1.0 [enabled]` |
| 17:08:05 | 3x `curl` mit ungueltigem Bearer | 3x 401, drei `harp/user-info`-Zeilen plus ein eigener Config-Lesevorgang |
| 17:09:xx | 3x `curl` mit ungueltigem Basic (Waechter eingeschaltet) | 3x 401, `172.29.42.131` (HaRP) attempts 3 delay 800, alle anderen Adressen 0 |
| 17:09:xx | 4x `curl` mit ungueltigem Bearer danach | 4x 401, Zaehler unveraendert bei 3 |
| 17:12:18 | `pytest tests/integration/test_credential_flood.py -q -m integration` ohne `.env.exapp` | `sssss`, fuenf Skips, Exit 0 |
| 17:12:26 | derselbe Lauf mit `.env.exapp` und `-v -s` | **5 passed in 17.43s, Exit 0** |
| 17:13:11 | Wiederholung aus dem Bootstrap-Zustand (Waechter `false`) | 5 passed, danach Waechter wieder `false` |
| 17:13:42 | Kontrolle: 20x `curl` **ohne** `Authorization`-Header | 20x 401, `user-info`-Delta **0**, Log-Delta 1 (ein Healthcheck) |
| 17:19:17 | `pytest ... -q -m integration` (Kommando des Plans, unveraendert) | 5 passed, Exit 0 |

Die Kennzahlen beider Laeufe:

| Groesse | Lauf A (ungueltiger Bearer) | Lauf B (ungueltiges Basic) | Kontrolle (kein Header) |
|---------|------------------------------|-----------------------------|--------------------------|
| Angreifer-Requests | 200 | 200 | 20 |
| Statusverteilung | `{401: 200}` | `{401: 200}` | 20x 401 |
| 5xx / Requests ohne Antwort | 0 / 0 | 0 / 0 | 0 / 0 |
| Nextcloud-Requests | 200 | 200 (erster Lauf 202) | 0 |
| davon `harp/user-info` | 200 | 200 | 0 |
| **Quotient Nextcloud/Angreifer** | **1,00** | **1,00** | **0,00** |
| Bruteforce-Zuwachs (HaRP-Adresse) | 0 | 27 bzw. 28 | 0 |
| Dauer | 3,2 bis 4,0 s | 2,0 bis 2,1 s | - |

Drei Befunde, die ueber die erwartete Bestaetigung hinausgehen:

1. **Der Zaehler haengt an HaRP, nicht am Angreifer.** Nextcloud vertraut in dieser Topologie
   nur dem Caddy-Container als Proxy, und die `user-info`-Anfrage kommt von HaRP. Gemessen:
   alle Eintraege auf `172.29.42.131`, null auf Gateway, Caddy und ExApp-Container. Damit ist
   die Formulierung "pro Quell-IP" aus dem Research zu schwach: ein Angreifer drosselt nicht
   nur alle Nutzer dieses Connectors, sondern alle Nutzer aller ExApps hinter demselben Proxy.
2. **200 abgelehnte Basic-Logins erzeugen nur 27 bis 28 Eintraege**, und Lauf B ist schneller
   als Lauf A. Sobald der Waechter seine Maximalverzoegerung erreicht hat, lehnt Nextcloud
   sofort ab, ohne einen weiteren Anmeldeversuch zu verarbeiten. Die PHP-Runde pro Request
   bleibt trotzdem (200 `user-info`), also wird der Angriff billiger und bleibt fuer die
   Instanz teuer.
3. **Lauf A ist der teurere Angriff.** Ein ungueltiger Bearer laeuft jedes Mal durch die volle
   Kette und hinterlaesst keinen Zaehler, der ihn irgendwann bremst. Nextcloud verteidigt sich
   hier nicht selbst, und genau deshalb ist die Empfehlung an den Admin kein Komfortpunkt.

Kein Befund spricht gegen D-37: die Bremse gehoert dorthin, wo ein Request abgewiesen werden
kann, **bevor** HaRP Nextcloud fragt, und das ist der Reverse Proxy des Admins.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Fehlende kritische Funktionalitaet] Der Test schaltet den Bruteforce-Waechter fuer die Messung ein**
- **Found during:** Task 1, Bestimmung der Messquelle
- **Issue:** `scripts/bootstrap_exapp.sh` setzt `auth.bruteforce.protection.enabled` auf
  `false` (Zeile "bruteforce protection: disabled (test instance)"). Lauf B haette damit einen
  leeren Zaehler gemessen, und dieser leere Zaehler waere eine Eigenschaft der Fixture gewesen,
  nicht eine Aussage ueber Nextcloud. Ein gruener Lauf ohne Aussage ist schlimmer als ein
  roter.
- **Fix:** Die Messung liest den Wert, schaltet ihn bei Bedarf ein und legt den vorherigen Wert
  im `finally` zurueck; beides steht im Protokoll (`bruteforce guard before the measurement`).
  Live gegengeprobt: aus dem Bootstrap-Zustand `false` gestartet, danach wieder `false`.
- **Files modified:** tests/integration/test_credential_flood.py
- **Commit:** df88ae1

**2. [Rule 3 - Blockierendes Problem] `docker compose exec` ist aus dem Testprozess nicht benutzbar**
- **Found during:** Task 1, erster Versuch der Wiederanfahr-Prozedur
- **Issue:** Jeder `docker compose`-Aufruf gegen `compose.exapp.yml` endet ohne exportiertes
  `HP_SHARED_KEY` mit `error while interpolating services.appapi-harp.environment.HP_SHARED_KEY`
  (WR-11 ist genau dafuer gebaut). Der Plan nennt compose-Kommandos fuer die Messung; ein
  Testprozess hat mit diesem Schluessel aber nichts zu tun, und ihn dort einzusammeln waere ein
  Geheimnis mehr an einer Stelle, die es nicht braucht.
- **Fix:** Die Messung ruft `docker exec` und `docker logs` mit den in `compose.exapp.yml`
  festgeschriebenen Containernamen. Die compose-Schreibweise desselben Aufrufs steht als
  Konstante im Modul und in der ersten Zeile jedes Protokolls, damit ein Leser sie
  nachvollziehen kann. Beides ist im Modulkopf begruendet.
- **Files modified:** tests/integration/test_credential_flood.py
- **Commit:** df88ae1

**3. [Rule 1 - Bug] Die Zugriffsklassen der Routentabelle widersprachen dem Manifest**
- **Found during:** Task 2, Abgleich der Zahlen gegen `appinfo/info.xml`
- **Issue:** Der Plan nannte "twelve routes" als veraltete Zahl. Beim Abgleich zeigte sich
  mehr: die Tabelle fuehrte `/authorize/decide` als `user`-Route und einen Absatz ueber "die
  eine `user`-Route", waehrend das Manifest seit CR-01 alle dreizehn Routen als `PUBLIC`
  deklariert, und `/connections` fehlte ganz. Eine falsche Zugriffsklasse im Dokument, mit dem
  ein Admin installiert, ist mehr als eine veraltete Zahl.
- **Fix:** Dreizehn Routen in der Reihenfolge des Manifests, `/connections` mit dem gemessenen
  CR-01-Grund, alle Klassen `public`, und der Absatz darunter erklaert, warum eine
  Identitaetspruefung auf einer PUBLIC-Route moeglich ist (HaRP schreibt das aufgeloeste Konto
  in `AUTHORIZATION-APP-API`). Zusaetzlich traegt Evidence-Schritt 4 jetzt eine Notiz, dass
  seine 403-Messung vom 15.08. vor Plan 03-01 liegt, mit der Messung von heute daneben (401
  aus der App, null Nextcloud-Requests).
- **Files modified:** docs/exapp-install.md
- **Commit:** b5eab6f

### Zusaetzliche Messung

Die Kontrolle ohne `Authorization`-Header stand nicht im Plan. Ohne sie waere die Zahl 1,00
zwar richtig, aber nicht handlungsleitend: erst der Vergleich mit 0,00 zeigt, dass die
Verstaerkung am Header haengt und nicht an der Route, und erst damit kann die Proxy-Regel
in der Doku genau die Requests treffen, die etwas kosten.

### Nicht gemacht

Kein Codefix am Connector, keine neue Abhaengigkeit (`git diff --stat uv.lock` leer,
`grep -c "hey\|vegeta\|locust\|k6" tests/integration/test_credential_flood.py` ist 0), keine
Aenderung an `/mcp` oder `oauth/throttle.py`.

## Requirements

- **AUTH-03** steht seit Phase 3 auf Complete; dieser Plan haengt keinen Haken um, sondern
  liefert die Belastungsseite dazu: der Discovery-Flow beginnt spezifikationsgemaess mit einer
  Ablehnung, und jetzt ist gemessen, was ein Missbrauch genau dieser Offenheit kostet.
- **EXAPP-04** bleibt Pending: die Einreichung selbst ist Sache der weiteren Plaene dieser
  Phase. Dieser Plan liefert einen Teil dessen, was ein Store-Reviewer und ein Admin dafuer
  lesen wollen.
- **SC 3 der Phase** ("Negative-Credential-Loadtest ist gruen") ist erfuellt und mit Zahlen
  belegt.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| T-05-22 (mitigate, erfuellt) | tests/integration/test_credential_flood.py, docs/exapp-install.md | Bearer-Flut gemessen statt geraten: Quotient 1,00 Nextcloud-Runden pro Angreifer-Request, 0 bei fehlendem Header; Empfehlung Rate Limit im Reverse Proxy mit Beispiel fuer Caddy und nginx; positive-only Cache unveraendert; `/mcp` bleibt undrosselt (D-37) und der Grund steht in der Doku |
| T-05-23 (mitigate, erfuellt) | tests/integration/test_credential_flood.py, docs/exapp-install.md | Eigener Lauf, eigener Befund: 27 bis 28 Bruteforce-Eintraege je 200 Requests, gemessen auf der HaRP-Adresse und nicht auf der des Angreifers; die Konsequenz fuer einen Remote-Server (ein Zaehler fuer alle Nutzer aller ExApps hinter dem Proxy) und die Ruecksetzung stehen im Runbook |
| T-05-24 (mitigate, erfuellt) | tests/integration/test_credential_flood.py | `security:bruteforce:reset` ist Pflichtschritt fuer alle fuenf Kandidaten-Adressen, mit Nachweis im Protokoll (`counters after reset: alle 0`) und einem eigenen Test; zusaetzlich wird der Waechter-Zustand des Bootstraps zurueckgelegt |
| T-05-25 (mitigate, erfuellt) | uv.lock, tests/integration/test_credential_flood.py | `asyncio.gather` plus `httpx`, kein neues Paket; `uv.lock` unveraendert, Grep-Gate auf die vier verworfenen Werkzeuge ist 0 |
| T-05-SC (accept) | uv.lock | Keine Installation, kein Package-Legitimacy-Fall |

Kein neues Angriffsflaechen-Flag: die Aenderungen liegen in einer Testdatei der
Wegwerf-Topologie und in einem Dokument. `src/` ist unberuehrt.

## Known Stubs

Keine.

## Offene Punkte

- Die gemessenen Zahlen gelten fuer diese Topologie (Caddy vor Nextcloud, HaRP als Deploy
  Daemon, `TRUSTED_PROXIES` auf genau den Caddy-Container). Auf einer Instanz, deren
  Proxy-Vertrauensliste HaRP mit einschliesst, koennte der Bruteforce-Zaehler an der Adresse
  des Angreifers landen statt an der von HaRP. Der Quotient 1,00 haengt an HaRPs
  `user-info`-Nachfrage und nicht an der Proxy-Konfiguration, ist davon also unberuehrt.
- Der Rate-Limit-Vorschlag ist nicht live verprobt: die Beispiele nennen die Direktiven und die
  Grundlage (Quotient und Kontrollmessung), aber kein Lauf hat gemessen, ob die genannten
  Grenzen eine echte Assistenten-Sitzung durchlassen. Dieselbe Klasse offener Punkte wie die
  Proxy-Regeln in `docs/spike-discovery.md`.
- Die Topologie ist wieder heruntergefahren (`down` mit erhaltenen Volumes, danach
  `docker stop`/`docker rm nc_app_mcp_connector` und `docker network rm nc-mcp-exapp-net`).
  Der Bruteforce-Waechter steht auf `false` und alle Zaehler auf 0, also im Zustand, den
  `scripts/bootstrap_exapp.sh` herstellt. `nc-mcp-test` und `findling-nextcloud` liefen die
  ganze Zeit unberuehrt weiter.

## Verification

```
uv run --no-sync pytest -q                  -> alle gruen (Default-Suite, ohne integration)
uv run --no-sync ruff check .               -> All checks passed!
uv run --no-sync ruff format --check .      -> 161 files already formatted
uv run --no-sync pyright                    -> 0 errors, 0 warnings, 0 informations
uv run --no-sync vulture src scripts vulture_whitelist.py -> leer
git diff --stat uv.lock                     -> leer
grep -c "twelve routes" docs/exapp-install.md    -> 0
grep -c "thirteen routes" docs/exapp-install.md  -> 1
grep -c "—\|–" docs/exapp-install.md             -> 0
```
