---
phase: 05-hardening-und-store-einreichung
plan: 14
subsystem: exapp
tags: [gap-closure, measurement, appapi, declarative-settings, oauth-discovery, live-proof]

# Dependency graph
requires:
  - phase: 05-hardening-und-store-einreichung
    plan: 11
    provides: "die https-oder-Loopback-Regel und den Rettungszweig, deren Wirkung Linie B misst"
  - phase: 05-hardening-und-store-einreichung
    plan: 12
    provides: "die Ursache des 401 und die Zahl der noetigen Disable/Enable-Zyklen"
  - phase: 05-hardening-und-store-einreichung
    plan: 13
    provides: "die INFO-Zeile statt der ERROR-Zeile, hier zum ersten Mal live im Log gesehen"
provides:
  - "Live-Nachweis, dass ein im Admin-Formular gesetzter Wert ohne Umgebungsvariable als issuer im Discovery-Dokument ankommt"
  - "Live-Nachweis, dass ein unbrauchbarer Wert keine Neustartschleife erzeugt und ueber das Formular korrigierbar ist"
  - "eine zweite, unabhaengige Topologie, auf der der 401-Befund aus 05-08 reproduziert und eingeordnet ist"
affects: [EXAPP-04, BL-06]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Eine Bedingung eines Nachweises wird hergestellt und protokolliert, nicht angenommen: die Deploy-Variable wurde durch eine Neuregistrierung ohne environment-variables-Block entfernt und ihr Fehlen mit grep -c belegt"
    - "Ein Messprotokoll nennt den Kontrastwert vor der Messung (hier den Default im Code), damit ein Treffer nicht mit einem Zufall verwechselt werden kann"
    - "Adressen aus einem Plan werden vor dem Lauf am Quelltext der laufenden Instanz gegengeprueft; der gemessene Weg steht im Protokoll, nicht der geplante"

key-files:
  created:
    - .planning/phases/05-hardening-und-store-einreichung/05-14-MEASUREMENTS.md
    - .planning/phases/05-hardening-und-store-einreichung/05-14-SUMMARY.md
  modified:
    - .planning/phases/05-hardening-und-store-einreichung/deferred-items.md

key-decisions:
  - "Die App wurde einmal ohne den environment-variables-Block neu registriert, weil AppAPI 34.0.0 kein occ-Kommando kennt, das eine Deploy-Variable entfernt; ohne diesen Schritt haette der Lauf nur bewiesen, dass ein Admin-Wert eine Variable ueberschreibt"
  - "Gesetzt wurde die eigene Adresse der Wegwerf-Instanz (http auf 127.0.0.1, die Loopback-Ausnahme von RFC 8414) statt einer https-Adresse: die Instanz liefert kein https aus, und eine fremde https-Adresse haette T-05-56 verletzt"
  - "Der Rueckweg in Linie C laeuft ausschliesslich ueber die Declarative-Settings-Route, nie ueber occ app_api:app:config:set, damit gemessen wird, was eine Administratorin tun kann"
  - "Das Wegwerf-App-Passwort des Admins wurde nach dem Lauf geloescht und lag nie in einer Datei dieses Repositories"

patterns-established:
  - "Ein Gap-Closure-Plan, dessen Auftrag Messen ist, aendert keine Quelldatei; der leere git status ueber src, tests, scripts und docs ist Teil des Beweises"

requirements-completed: [EXAPP-04]

# Metrics
duration: 25min
completed: 2026-08-20
---

# Phase 05 Plan 14: Gap Closure, Live-Nachweis Rundlauf Summary

Der Rundlauf vom Admin-Formular ins Discovery-Dokument ist einmal wirklich gefahren: auf einer
neu aufgebauten Topologie ohne gesetzte `NC_MCP_PUBLIC_URL` steht der im Formular gesetzte Wert
nach genau einem Disable/Enable-Zyklus zeichengleich als `issuer` im Autorisierungsserver-Dokument,
ein unbrauchbarer Wert erzeugt keine Neustartschleife, und der Rückweg läuft allein über dasselbe
Formular.

## Was entstanden ist

| Datei | Inhalt |
|-------|--------|
| `05-14-MEASUREMENTS.md` | Versionen und frischer Aufbau, der am Controller gegengeprüfte Schreibweg, die hergestellte Bedingung (keine Deploy-Variable), Linie A, Linie B, Linie C, Endzustand, Abschnitt "Was damit belegt ist" mit beiden wörtlich zitierten Wahrheiten |
| `deferred-items.md` | Die 401-Zeile aus 05-08 ist durchgestrichen und verweist auf 05-12 (Ursache), 05-13 (Fix) und 05-14 (Nachweis); dazu eine neue Zeile für einen Nebenbefund aus Linie B |

Keine Quelldatei ist angefasst worden: `git status --porcelain src tests scripts docs` ist leer,
und `uv run --no-sync pytest` meldet 1821 passed, 92 deselected.

## Die drei Messlinien in einem Satz

* **Linie A:** `public_url` über `/ocs/v2.php/settings/api/declarative/value` gesetzt (HTTP 200),
  ein Disable/Enable-Zyklus, danach `issuer` gleich `http://127.0.0.1:8081/exapps/mcp_connector`
  statt des vorherigen Defaults `http://127.0.0.1:8765`. Zeichenvergleich programmatisch: True.
* **Linie B:** `http://cloud.example.com/exapps/mcp_connector` gesetzt, derselbe Zyklus. Die
  Warnzeile aus `config_values` steht wörtlich im Log, `.State.Status` bleibt `running`,
  `RestartCount` bleibt 0, die App bleibt `enabled`, der `issuer` fällt auf den Default zurück
  und trägt den http-Wert nicht, `/settings/admin/security` antwortet 200.
* **Linie C:** derselbe Weg mit dem brauchbaren Wert, und das Dokument trägt ihn wieder. Kein
  `occ app_api:app:config:set`, kein PDO, kein Eingriff in `oc_appconfig_ex`.

## Belege je Gap

| Gap aus 05-VERIFICATION.md | Messlinie | Beleg |
|----------------------------|-----------|-------|
| **Gap 1 (CR-01, Truth 5):** "Kein bekannter, ungeloester kritischer Haertungsfehler bleibt im Code (Review-Gate der 'gehärtet'-Zusage)" | Linie B und Linie C | Linie B misst die Verhinderungshälfte: ein http-Wert auf einem Nicht-Loopback-Host wird in `config_values._public_url` abgelehnt, ohne dass der Container in eine Schleife gerät (`running`, `RestartCount` unverändert 0, App weiter `enabled`, Admin-Seite 200). Linie C misst die Rettungshälfte: die Installation kommt allein über das Formular zurück. Der Deadlock aus 05-REVIEW.md ist damit live widerlegt statt nur unit-getestet. |
| **Gap 2 (401, Truth 6):** "Ein in Nextcloud gesetzter Admin-Wert (public_url, DCR, Allowlist) wirkt in der Praxis ohne gesetzte Umgebungsvariable" | Linie A, auf frischer Topologie | Der App-Container trägt nachweislich keine `NC_MCP_PUBLIC_URL` (`grep -c` gleich 0, Variablennamen ohne Werte protokolliert), der Ausgangswert des Dokuments ist der Default im Code, und nach einem Zyklus steht der Formularwert als `issuer` und als `resource` dort. Der 401 des ersten Starts erscheint als INFO-Zeile mit Ausweg (Fix aus 05-13, hier zum ersten Mal live gesehen). |
| Human-Verification-Punkt 2 (Wiederholung auf einer zweiten Topologie) | der ganze Lauf | Volumes und Registrierung wurden vor der ersten Messung weggeworfen (`down -v`, `docker rm -f nc_app_mcp_connector`, `docker volume rm nc_app_mcp_connector_data`), also stammt der Nachweis nicht von der Instanz, auf der 05-08 den 401 fand. Der Befund war kein Artefakt einer einzelnen Topologie. |

## Abweichungen vom Plan

**1. [Rule 3 - blockierende Bedingung] Die App wurde einmal ohne die Deploy-Variable neu registriert**

- **Gefunden bei:** Task 1, direkt nach dem Bootstrap
- **Problem:** `scripts/bootstrap_exapp.sh` registriert die App immer mit
  `NC_MCP_PUBLIC_URL` im json-info-Payload, und AppAPI 34.0.0 kennt kein occ-Kommando, das eine
  Deploy-Variable wieder entfernt (`occ list app_api` geprüft). Mit gesetzter Variable hätte die
  Messung nur gezeigt, dass ein Admin-Wert eine Variable überschreibt, und nicht die Wahrheit, die
  Gap 2 verlangt.
- **Lösung:** `occ app_api:app:unregister mcp_connector --rm-data`, danach
  `occ app_api:app:register` mit demselben Secret, demselben Image, denselben dreizehn Routen und
  ohne den `external-app`-Block. Das Fehlen der Variable ist danach protokolliert.
- **Dateien:** keine (Payload lag außerhalb des Repositories und ist gelöscht)

**2. [Rule 1 - falsche Adresse im Plan] Die Declarative-Settings-Route heißt anders**

- **Gefunden bei:** Task 1, bei der vom Plan geforderten Gegenprobe am Controller
- **Problem:** Der Plan nennt `/ocs/v2.php/apps/settings/api/declarative/value`. Die laufende
  Instanz deklariert die Route mit `'root' => ''` (`apps/settings/appinfo/routes.php:57`), also
  ohne das `apps/`-Segment.
- **Lösung:** Gemessen wurde `/ocs/v2.php/settings/api/declarative/value` mit den Feldern `app`,
  `formId`, `fieldId`, `value`; der Quelltextauszug steht im Protokoll.
- **Dateien:** keine

**3. [Rule 3 - der Plan verlangt etwas, das die Topologie nicht hat] http auf Loopback statt https**

- **Gefunden bei:** Task 1, Linie A
- **Problem:** Der Plan sagt "auf die https-Adresse setzen, unter der die Wegwerf-Instanz diese
  App ausliefert". Diese Instanz liefert ausschließlich `http://127.0.0.1:8081` aus, und T-05-56
  verbietet, eine fremde Adresse zu setzen.
- **Lösung:** Gesetzt wurde `http://127.0.0.1:8081/exapps/mcp_connector`, die eigene Adresse der
  Instanz und zugleich die einzige Nicht-https-Form, die `_public_url` durchlässt (Loopback-Ausnahme
  von RFC 8414). Der Nachweis wird dadurch nicht schwächer: der Kontrastwert vor der Messung ist der
  Default `http://127.0.0.1:8765`, der Treffer ist also unterscheidbar.
- **Dateien:** keine

**4. [Zweig N statt Zweig R, Erwartung des Plans] Zwei Formulierungen des Plans gingen ins Leere**

- Der Plan erwartet in der Startzeile eine Quellenangabe "frisch gelesen oder aus dem Volume". Mit
  Zweig N gibt es keine zweite Quelle: die Zeile nennt nur die gewonnenen Schlüssel
  (`NC_MCP_PUBLIC_URL`). Protokolliert und im Protokoll begründet.
- Der Plan erwartet in Linie B "die Ablehnungszeile aus `config_values` beziehungsweise die
  Rettungszeile aus `entry_exapp`". Gemessen wurde die Ablehnungszeile: der Wert wird verworfen,
  bevor er `build_exapp_app` erreicht. Die Rettungszeile bleibt als zweite Sicherung dahinter.

**5. [Rule 2 - Buchführung] Ein Nebenbefund ist als offene Zeile aufgenommen**

- **Gefunden bei:** Task 1, Linie B
- **Fund:** Die ERROR-Zeile aus `entry_exapp.main` sagt "no public address is stored in Nextcloud
  either", obwohl eine gespeichert ist, nur eine unbrauchbare. Kein Fehlverhalten, ein ungenauer
  Satz; die Zeile davor sagt den wahren Grund.
- **Nicht hier gefixt:** `files_modified` dieses Plans sind zwei Planungsdateien, und ein Eingriff
  in `src/` hätte den Nachweis kaputt gemacht, dass dieser Lauf am gemessenen Stand nichts geändert
  hat.
- **Dateien:** `deferred-items.md`

**6. Messnotiz ohne Codefolge:** Jeder `docker compose`-Aufruf gegen `compose.exapp.yml` verlangt
`HP_SHARED_KEY` in der Umgebung (WR-11). Der erste Bootstrap-Versuch lief ohne diesen Export und
wartete fünf Minuten vergeblich auf die Installation, weil das `occ status` des Skripts still
scheiterte. Der zweite Lauf mit Export war nach 70 Sekunden fertig. Für einen späteren Plan ist das
kein Fix, sondern eine Zeile im Wissen über dieses Skript.

## Threat Flags

| Threat ID | Kategorie | Disposition im Plan | Stand nach dem Lauf |
|-----------|-----------|---------------------|---------------------|
| T-05-53 | Information Disclosure, Wegwerf-Admin-Passwort, App-Secret oder HaRP-Schlüssel im Protokoll | mitigate | **eingehalten**: im Protokoll stehen nur Statuscodes, JSON-Felder, Logzeilen und Variablennamen. Anmeldedaten und Registrierungs-Payload lagen außerhalb des Repositories und sind gelöscht; das Wegwerf-App-Passwort des Admins ist mit `occ user:auth-tokens:delete` entfernt (Liste danach leer). `grep -rniE "app_secret|hp_shared_key|app password"` trifft nur Variablennamen. |
| T-05-54 | Tampering, ein Kommando trifft `nc-mcp-test` oder `findling-nextcloud` | mitigate | **eingehalten**: jedes Kommando nennt `compose.exapp.yml`, `nc-mcp-exapp-nc` oder `nc_app_mcp_connector` wörtlich. Beide Fremdinstanzen liefen durch und wurden in keinem Kommando genannt. `uv run --no-sync pytest` bleibt grün, der Bestandstest zur Topologietrennung eingeschlossen. |
| T-05-55 | Denial of Service, Linie B lässt die Installation im Fehlzustand zurück | mitigate | **eingehalten**: Linie C ist gefahren, das Dokument trägt wieder die eigene Adresse der Instanz, die App ist `enabled` und der Container läuft. |
| T-05-56 | Spoofing, der gesetzte `issuer` zeigt auf eine fremde Adresse | mitigate | **eingehalten**: gesetzt wurde ausschließlich `http://127.0.0.1:8081/exapps/mcp_connector`, die Adresse dieser Wegwerf-Instanz. Der Vergleich im Protokoll ist zeichengenau und programmatisch geprüft. Der einzige fremde Wert (`cloud.example.com`) ist der bewusst unbrauchbare aus Linie B, und er ist gemessen nie wirksam geworden. |
| T-05-SC | Tampering, Paketinstallationen | accept | **eingehalten**: keine Installation, nur docker-, curl- und occ-Kommandos. |

Kein neuer Fund an Angriffsfläche: dieser Plan fügt keinen Endpunkt hinzu, ändert kein Schema und
keine Quelldatei.

## Zustand der Wegwerf-Topologie am Ende des Laufs

Die Topologie bleibt benutzbar stehen, in dem Zustand, den Linie C hergestellt hat: `mcp_connector
(MCP Connector): 0.1.1 [enabled]`, Container `nc_app_mcp_connector` `running` mit `RestartCount` 0,
`public_url` im Admin-Formular auf `http://127.0.0.1:8081/exapps/mcp_connector`, und ohne
`NC_MCP_PUBLIC_URL` in der Deploy-Umgebung. Wer sie für einen späteren Plan neutral braucht, setzt
das Feld leer oder baut sie wie in Abschnitt 1 des Protokolls neu auf; wer den Bootstrap erneut
laufen lässt, bekommt die Deploy-Variable zurück.

## Verifikation

| Prüfung | Ergebnis |
|---------|----------|
| `occ app_api:app:list` | `mcp_connector (MCP Connector): 0.1.1 [enabled]` |
| `docker inspect -f '{{.State.Status}} {{.RestartCount}}'` | `running 0` |
| `test -f ...05-14-MEASUREMENTS.md` | vorhanden, 433 Zeilen |
| `grep -c "issuer" ...05-14-MEASUREMENTS.md` | 13 |
| `grep -c "05-14" ...deferred-items.md` | 2 |
| `grep -c '—\|–'` in beiden Dateien | 0 |
| `grep -ci "archiv"` in beiden Dateien | 0 |
| `grep -rniE "app_secret\|hp_shared_key\|app password"` im Protokoll | nur Variablennamen, kein Wert |
| `git status --porcelain src tests scripts docs` | leer |
| `uv run --no-sync pytest` | 1821 passed, 92 deselected |

## Self-Check: PASSED

Beide Dateien existieren (`05-14-MEASUREMENTS.md`, `deferred-items.md`), und beide Commits stehen in
`git log`: `c4f1962` (Messprotokoll) und `ea83055` (offene Zeile geschlossen).
