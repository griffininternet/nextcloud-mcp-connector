# 05-05 Rohmessungen: Negativ-Credential-Lasttest

Alle Messungen am **19.08.2026** auf dem Entwicklungsrechner (Windows 11, Docker Desktop
29.5.2, Git Bash) gegen die Topologie aus `compose.exapp.yml` (Projekt `nc-mcp-exapp`):
Nextcloud **34.0.2**, AppAPI 34.0.0, HaRP `ghcr.io/nextcloud/nextcloud-appapi-harp:release`,
ExApp `mcp_connector 0.1.0 [enabled]`. Die Instanzen `nc-mcp-test` und `findling-nextcloud`
liefen die ganze Zeit unberuehrt weiter.

Alle Zeiten UTC. Jede Zahl unten nennt den Befehl, der sie erzeugt hat.

---

## Schritt 0: Topologie anfahren (Prozedur aus STATE.md)

```
17:00:50  export HP_SHARED_KEY=$(openssl rand -hex 32) && docker compose -f compose.exapp.yml up -d --wait
          -> vier Container healthy, Exit 0
```

Danach die beiden Abmeldungen aus der Prozedur. Erster Versuch scheiterte an genau dem
Punkt, den STATE.md nennt (die Shell-Env ueberlebt einen Aufruf nicht):

```
docker compose -f compose.exapp.yml exec ... occ app_api:app:unregister mcp_connector --silent --force
-> error while interpolating services.appapi-harp.environment.HP_SHARED_KEY:
   required variable HP_SHARED_KEY is missing a value
```

Der Schluessel wird deshalb aus dem laufenden Container zurueckgelesen, nicht neu erzeugt
(ein neuer Wert wuerde die Registrierung des Daemons gegen den Container verstimmen):

```
export HP_SHARED_KEY=$(docker inspect nc-mcp-exapp-harp \
  --format '{{range .Config.Env}}{{println .}}{{end}}' | grep '^HP_SHARED_KEY=' | cut -d= -f2)
-> key length: 64
occ app_api:daemon:unregister harp_proxy_docker   -> Daemon config unregistered.
occ app_api:app:list                              -> ExApps:            (leer)
```

Der erste `bash scripts/bootstrap_exapp.sh` lief ohne exportierten Schluessel und endete
nach fuenf Minuten mit "ERROR: Nextcloud is still not installed", obwohl `occ status`
`installed: true` meldete: die `occ`-Huelle des Skripts geht durch `docker compose`, und
jeder dieser Aufrufe scheiterte still an der Interpolation (`2>/dev/null` in der
Warteschleife). Mit exportiertem Schluessel:

```
17:07:42  bash scripts/bootstrap_exapp.sh
          -> share folder /mcp-share-04d2eb7d6d: already there        (Fixture aus 05-03, wiederverwendet)
          -> read-only share /mcp-share-04d2eb7d6d to bob: present (attempt 1)
          -> bruteforce protection: disabled (test instance)
          -> exapp mcp_connector: registered and deployed / enabled
          -> mcp_connector (MCP Connector): 0.1.0 [enabled]
```

---

## Schritt 1: Die Messquelle bestimmen (Vorbereitung, nicht die Messung)

**Wo die Nextcloud-Requests sichtbar sind.** `docker logs nc-mcp-exapp-nc` fuehrt das
Apache-Zugriffs-Log auf stdout. Drei Requests mit ungueltigem Bearer:

```
17:08:05  curl -X POST -H "Authorization: Bearer notarealtoken<n>" .../exapps/mcp_connector/mcp   (3x)
          -> 401 401 401
          neue Logzeilen:
          172.29.42.10 - - "GET /index.php/apps/app_api/harp/user-info?appId=mcp_connector HTTP/1.1" 200 1430 "-" "curl/8.19.0"
          172.29.42.10 - - "POST /ocs/v2.php/apps/app_api/api/v1/ex-app/config/get-values HTTP/1.1" 200 1820 "-" "nextcloud-mcp-connector/0.1"
          172.29.42.10 - - "GET /index.php/apps/app_api/harp/user-info?appId=mcp_connector HTTP/1.1" 200 1430 "-" "curl/8.19.0"
          172.29.42.10 - - "GET /index.php/apps/app_api/harp/user-info?appId=mcp_connector HTTP/1.1" 200 1430 "-" "curl/8.19.0"
```

Damit ist der Befund von 05-RESEARCH Pitfall 5 als Zeile belegt: HaRP fragt Nextcloud pro
Request mit `Authorization`-Header genau einmal, wer der Aufrufer ist
(`GET /index.php/apps/app_api/harp/user-info`), und das ist eine vollstaendige PHP-Runde.
Die vierte Zeile ist unsere eigene (der Lesevorgang der ExApp-Config, einmal fuer die drei).
Der Healthcheck des Compose-Files (`GET /status.php`, alle fuenf Sekunden) ist Verkehr der
Fixture und wird in jeder Zaehlung abgezogen.

**Wofuer die Bruteforce-Eintraege gezaehlt werden.** Der Bootstrap schaltet den Waechter aus
(`bruteforce protection: disabled (test instance)`), also wurde er fuer die Messung
eingeschaltet. Baseline, alle Kandidaten null:

```
17:09:xx  occ config:system:set auth.bruteforce.protection.enabled --value=true --type=boolean
          occ security:bruteforce:attempts --output=json <ip>   fuer .1 / .10 / .131 / .132 / 127.0.0.1
          -> jeweils {"bypass-listed":false,"attempts":0,"delay":0}
```

Drei Requests mit ungueltigem Basic:

```
17:09:xx  curl -u "ghostuser<n>:wrongpassword" ...   (3x)  -> 401 401 401
          172.29.42.1    (Gateway)     attempts 0
          172.29.42.10   (Caddy)       attempts 0
          172.29.42.131  (HaRP)        attempts 3, delay 800
          172.29.42.132  (ExApp)       attempts 0
          127.0.0.1                    attempts 0
```

**Der Zaehler haengt an der Adresse von HaRP, nicht an der des Angreifers.** Nextcloud
vertraut in dieser Topologie nur dem Caddy-Container als Proxy (`TRUSTED_PROXIES:
172.29.42.10`), und die `user-info`-Anfrage kommt von HaRP. Fuer Nextcloud ist damit jeder
Nutzer jeder ExApp hinter diesem HaRP dieselbe Quelle. Das ist die Verschaerfung von
Pitfall 5 gegenueber "pro Quell-IP": die Drosselung trifft nicht nur alle Nutzer dieses
Connectors, sondern alle Nutzer aller ExApps hinter demselben Proxy.

Vier weitere Requests mit ungueltigem Bearer, direkt danach:

```
17:09:xx  curl -H "Authorization: Bearer stillnotarealtoken<n>" ...  (4x) -> 401 401 401 401
          172.29.42.131  attempts 3, delay 800     (unveraendert)
```

Bearer erzeugt keinen Eintrag. Die Annahme des Research haelt.

---

## Schritt 2: Ohne Topologie skippt die Datei

```
17:12:18  uv run --no-sync pytest tests/integration/test_credential_flood.py -q -m integration
          (ohne geladene .env.exapp)
          -> sssss, fuenf Skips, Exit 0
```

---

## Schritt 3: Lauf A und Lauf B, erste Messung

```
17:12:26  set -a && . ./.env.exapp && set +a
          uv run --no-sync pytest tests/integration/test_credential_flood.py -m integration -v -s
          -> 5 passed in 17.43s, Exit 0
```

Ausgabe des Messprotokolls, woertlich:

```
=== credential flood measurement, 2026-08-19 17:12:27 UTC ===
occ command shape: docker compose -p nc-mcp-exapp -f compose.exapp.yml exec -T --user www-data nextcloud php occ <command>
bruteforce guard before the measurement: true
run A (invalid bearer), 200 attacker requests, 20 in flight, 4.0 s
  status distribution: {401: 200}
  transport failures: 0
  nextcloud requests: 200 (ratio 1.0), of them 200 user-info (ratio 1.0)
  bruteforce growth: {'harp (172.29.42.131)': 0, 'caddy (172.29.42.10)': 0, 'exapp (172.29.42.132)': 0, 'gateway (172.29.42.1)': 0, 'loopback (127.0.0.1)': 0}
run B (invalid basic), 200 attacker requests, 20 in flight, 2.0 s
  status distribution: {401: 200}
  transport failures: 0
  nextcloud requests: 202 (ratio 1.01), of them 200 user-info (ratio 1.0)
  bruteforce growth: {'harp (172.29.42.131)': 27, 'caddy (172.29.42.10)': 0, 'exapp (172.29.42.132)': 0, 'gateway (172.29.42.1)': 0, 'loopback (127.0.0.1)': 0}
  reset: 172.29.42.131, 172.29.42.10, 172.29.42.132, 172.29.42.1, 127.0.0.1
  counters after reset: {'harp (172.29.42.131)': 0, 'caddy (172.29.42.10)': 0, 'exapp (172.29.42.132)': 0, 'gateway (172.29.42.1)': 0, 'loopback (127.0.0.1)': 0}
```

Der Waechter stand hier auf `true`, weil Schritt 1 ihn eingeschaltet hatte. Deshalb wurde er
fuer den zweiten Lauf wieder auf den Bootstrap-Zustand gesetzt.

---

## Schritt 4: Zweite Messung aus dem Bootstrap-Zustand (Wiederholbarkeit plus Waechter-Nachweis)

```
17:13:0x  docker exec -u www-data nc-mcp-exapp-nc php occ config:system:set \
            auth.bruteforce.protection.enabled --value=false --type=boolean
          -> value now: false
17:13:11  set -a && . ./.env.exapp && set +a
          uv run --no-sync pytest tests/integration/test_credential_flood.py -m integration -q -s
          -> ..... 5 passed, Exit 0
```

```
=== credential flood measurement, 2026-08-19 17:13:12 UTC ===
bruteforce guard before the measurement: false
run A (invalid bearer), 200 attacker requests, 20 in flight, 3.2 s
  status distribution: {401: 200}
  transport failures: 0
  nextcloud requests: 200 (ratio 1.0), of them 200 user-info (ratio 1.0)
  bruteforce growth: {'harp (172.29.42.131)': 0, ... alle 0}
run B (invalid basic), 200 attacker requests, 20 in flight, 2.1 s
  status distribution: {401: 200}
  transport failures: 0
  nextcloud requests: 200 (ratio 1.0), of them 200 user-info (ratio 1.0)
  bruteforce growth: {'harp (172.29.42.131)': 28, ... alle 0}
  reset: 172.29.42.131, 172.29.42.10, 172.29.42.132, 172.29.42.1, 127.0.0.1
  counters after reset: {... alle 0}
```

```
17:13:30  docker exec -u www-data nc-mcp-exapp-nc php occ config:system:get auth.bruteforce.protection.enabled
          -> false
```

Der Test schaltet den Waechter fuer die Messung ein und legt den vorherigen Wert zurueck.
Beide Laeufe liefern dieselben Zahlen, der Bruteforce-Zuwachs schwankt um eine Einheit
(27 und 28).

---

## Schritt 5: Gegenprobe ohne Authorization-Header

Die scharfste Form des Befundes: dieselbe Route, dieselbe Nutzlast, kein Credential.

```
17:13:42  20x curl -X POST (ohne Authorization-Header) .../exapps/mcp_connector/mcp
          -> 401 (20x)
          user-info before=810 after=810 delta=0
          alle Logzeilen delta=1   (die eine ist ein Healthcheck)
```

Zwanzig anonyme Requests kosten Nextcloud **null** PHP-Runden, zwanzig Requests mit einem
beliebigen `Authorization`-Header kosten zwanzig. Damit haengt die gemessene Verstaerkung
nachweislich am Header und nicht an der Route, und die Empfehlung an den Admin kann genau
sein.

---

## Die Kennzahlen

| Groesse | Lauf A (ungueltiger Bearer) | Lauf B (ungueltiges Basic) | Kontrolle (kein Header) |
|---------|------------------------------|-----------------------------|--------------------------|
| Angreifer-Requests | 200 | 200 | 20 |
| Antworten | 200x 401 | 200x 401 | 20x 401 |
| 5xx | 0 | 0 | 0 |
| Requests ohne Antwort | 0 | 0 | 0 |
| Nextcloud-Requests | 200 | 200 (erster Lauf 202) | 0 |
| davon `harp/user-info` | 200 | 200 | 0 |
| **Quotient Nextcloud/Angreifer** | **1,00** | **1,00** | **0,00** |
| Bruteforce-Zuwachs (HaRP-IP) | 0 | 27 bzw. 28 | 0 |
| Dauer | 3,2 bis 4,0 s | 2,0 bis 2,1 s | - |

Zwei Beobachtungen, die keine Assertion sind und deshalb hier stehen:

1. **Lauf B ist schneller als Lauf A.** Sobald der Bruteforce-Waechter seine
   Maximalverzoegerung erreicht hat, antwortet Nextcloud sofort ablehnend, ohne einen
   weiteren Anmeldeversuch zu verarbeiten. Genau daran haengt auch, warum 200 abgelehnte
   Basic-Requests nur 27 bis 28 Zaehler-Eintraege erzeugen und nicht 200: ab der
   Maximalverzoegerung wird nicht mehr gezaehlt, weil nicht mehr geprueft wird. Die PHP-Runde
   pro Request bleibt trotzdem (200 `user-info`).
2. **Lauf A ist der teurere Angriff.** Ein ungueltiger Bearer laeuft jedes Mal durch die
   volle Kette (HaRP fragt Nextcloud, unsere ExApp prueft den Token im Store, und der Verifier
   cacht nur positive Ergebnisse), und er hinterlaesst keinen Zaehler, der ihn irgendwann
   bremst. Nextcloud verteidigt sich hier nicht selbst.

---

## Was der Lauf hinterlaesst

- Bruteforce-Zaehler aller fuenf Kandidaten-Adressen: 0, nachgewiesen im Protokoll und
  nachgemessen um 17:13:5x (`{"bypass-listed":false,"attempts":0,"delay":0}` fuer
  172.29.42.131).
- `auth.bruteforce.protection.enabled`: `false`, also der Zustand, den
  `scripts/bootstrap_exapp.sh` herstellt.
- `git diff --stat uv.lock`: leer. Kein Lasttest-Werkzeug als Abhaengigkeit,
  `grep -c "hey\|vegeta\|locust\|k6" tests/integration/test_credential_flood.py` ist 0.
- Kein Codefix am Connector. `/mcp` bleibt undrosselt (D-37), und die Messung liefert keinen
  Grund, das zu aendern: die Bremse gehoert in den Reverse Proxy des Admins, weil sie dort den
  Request abweisen kann, bevor HaRP Nextcloud fragt.
