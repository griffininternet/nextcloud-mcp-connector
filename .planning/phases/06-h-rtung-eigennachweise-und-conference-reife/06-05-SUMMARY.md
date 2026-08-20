---
phase: 06-h-rtung-eigennachweise-und-conference-reife
plan: 05
subsystem: oauth
tags: [cimd, get-client, enforcement-point, foreign-key, cache-freshness, ttl, fail-closed]

# Dependency graph
requires:
  - phase: 06-02
    provides: "cimd.fetch_document, cimd.is_cimd_client_id, validate_document, der gepinnte Abruf"
  - phase: 06-03
    provides: "ClientPolicy.cimd_enabled (fail-closed an dcr_enabled gekoppelt), loopback_match"
provides:
  - "provider._resolve_cimd: der eine Aufloeser einer URL-client_id, mit dem Schalter als erster Frage und einer echten clients-Zeile als Ergebnis"
  - "Der CIMD-Zweig in provider.get_client zwischen 'row is None' und _client_information, mit EINEM Aufrufpunkt fuer alle drei Faelle (keine Zeile, abgelaufene Frische, frische Zeile)"
  - "clients.cimd_fetched_at und clients.cimd_expires_at, idempotent nachgezogen, in save_client und load_client"
  - "Die Ausnahme von der Registrierungs-TTL an beiden Loeschstellen (get_client und store.expired_clients)"
  - "cimd.cache_lifetime plus cimd.fetch_document_and_lifetime: die Frische einer Antwort aus ihrem eigenen Cache-Header, gekappt auf 300 bis 3600 s"
affects: [AUTH-08, 06-06, 06-09]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ein neuer Weg in einen bestehenden Enforcement-Punkt einhaengen statt danebenlegen: der Zweig endet im gemeinsamen Rest derselben Funktion, damit allowed-Flag, Allowlist und Fehlerbild nicht kopiert werden muessen"
    - "Ein Aufrufpunkt fuer alle Faelle eines Zweigs (row is None ODER row.cimd_fetched_at is not None): der Aufgerufene unterscheidet sie, damit der Aufrufer keinen davon vergessen kann"
    - "Eine Grenze mit zwei Projektionen statt zwei Implementierungen: fetch_document_and_lifetime traegt den Wert, fetch_document ist derselbe Aufruf fuer einen Aufrufer ohne Ablage"
    - "Aus fremdem JSON wird eine benannte Teilmenge uebernommen, nie das Dokument: die Feldliste ist der Ort, an dem logo_uri nicht steht"
    - "Ein AST-Gate, das Docstrings zuerst abzieht: eine Erklaerung, die benennt was NICHT passiert, darf das Gate nicht ausloesen"

key-files:
  created:
    - .planning/phases/06-h-rtung-eigennachweise-und-conference-reife/06-05-SUMMARY.md
  modified:
    - src/mcp_connector/oauth/store.py
    - src/mcp_connector/oauth/provider.py
    - src/mcp_connector/oauth/cimd.py
    - tests/unit/test_oauth_store.py
    - tests/unit/test_oauth_provider.py
    - tests/unit/test_oauth_cimd.py
    - CHANGELOG.md
    - .planning/STATE.md
    - .planning/ROADMAP.md

key-decisions:
  - "Der Zweig hat EINEN Aufrufpunkt in get_client: 'if row is None or row.cimd_fetched_at is not None' ruft _resolve_cimd, und dort werden die drei Faelle unterschieden. Der Plan legt die Frische-Pruefung in get_client; ein zweiter Zweig dort haette den Schalter zweimal gefragt oder einmal vergessen"
  - "Der Schalter wirkt auch auf eine bestehende CIMD-Zeile: mit abgeschaltetem CIMD oder DCR kommt auch ein schon aufgeloester Client nicht mehr durch. Das ist die strengere Lesart der Locked Decision, kostet keine Zeile Code extra und ist bewusst anders als bei DCR (dort bleiben bestehende Registrierungen gueltig)"
  - "_has_expired wird fuer Zeilen mit gesetztem cimd_fetched_at nicht angewandt UND store.expired_clients nimmt sie aus: die zweite Stelle war im Plan nicht genannt, ohne sie waere die erste wirkungslos, weil der Sweep an jeder Autorisierung haengt (T-06-31)"
  - "Die Cache-Frist kommt aus dem Cache-Header der Antwort; dafuer bekommt cimd.py fetch_document_and_lifetime als Grenze und fetch_document als Projektion davon. Nur der Fetch sieht den Header, und die 107 Tests aus 06-02 bleiben unberuehrt"
  - "Aus dem Dokument werden vier Felder uebernommen (client_name, redirect_uris, grant_types, response_types); token_endpoint_auth_method wird auf none gesetzt und die client_id ist die abgerufene. logo_uri kommt damit nie in den Datensatz, statt spaeter beim Rendern wieder ausgelassen werden zu muessen"
  - "Der Provider nimmt den Resolver als Konstruktorargument, wie er die Uhr nimmt: sonst haette die Unit-Suite claude.ai wirklich aufgeloest, und die Zusicherung des Datei-Docstrings ('kein Socket') waere gefallen"

patterns-established:
  - "Wenn ein zweiter Weg in einen Enforcement-Punkt eingehaengt wird, gehoert die Absage-Reihenfolge des Zweigs in den Docstring des Zweigs und nicht in eine Planungsdatei: sie wird mit dem Code gelesen"

requirements-completed: []

# Metrics
duration: 35min
completed: 2026-08-20
---

# Phase 06 Plan 05: Der CIMD-Zweig in get_client Summary

**Eine `client_id`, die eine https-URL ist, wird in `get_client` aufgeloest und bekommt eine
echte `clients`-Zeile ohne Secret; danach laeuft dieselbe Funktion weiter wie fuer jeden
registrierten Client, und die Registrierungs-TTL nimmt einer so entstandenen Verbindung
weder in der Abfrage noch im Sweep die Zeile weg.**

## Performance

- **Duration:** 35 min
- **Tasks:** 2 von 2
- **Files modified:** 3 Quelldateien, 3 Testdateien, CHANGELOG, plus Zustand und Roadmap

## Task Commits

1. **Task 1: Zwei Spalten auf clients, idempotent nachgezogen** , `8b7750d` (feat)
2. **Task 2: _resolve_cimd und der Zweig in get_client** , `a28a3aa` (feat)

## Was entstanden ist

| Datei | Inhalt |
|-------|--------|
| `src/mcp_connector/oauth/store.py` | `clients.cimd_fetched_at` und `clients.cimd_expires_at` im Schema-Text (mit der Begruendung fuer zwei Werte statt einem), in `_add_missing_columns`, auf `ClientRow`, in `save_client` und in `load_client`; `expired_clients` nimmt Zeilen mit gesetztem `cimd_fetched_at` aus |
| `src/mcp_connector/oauth/provider.py` | `_resolve_cimd`, der Zweig in `get_client`, die TTL-Ausnahme, `_cimd_client_information` als Projektion des Dokuments, `_cimd_is_fresh`, der Resolver als Konstruktorargument |
| `src/mcp_connector/oauth/cimd.py` | `CACHE_MIN_SECONDS`/`CACHE_MAX_SECONDS`, `cache_lifetime`, `fetch_document_and_lifetime` als Grenze; `fetch_document` ist jetzt deren Projektion |
| `tests/unit/test_oauth_store.py` | 7 Tests: die Datei eines aelteren Builds, ihre unberuehrte Zeile, Idempotenz ueber zwei Oeffnungen, Rundlauf samt Maske, die Aktualisierung die `registered_at` behaelt, die Sweep-Ausnahme |
| `tests/unit/test_oauth_provider.py` | 22 Tests im neuen Abschnitt "AUTH-08", plus `resolving`, `cimd_document`, `cimd_route` und der Resolver in `build` |
| `tests/unit/test_oauth_cimd.py` | 20 Tests zur Frische-Frist: der Header-Katalog, die Frist am Fetch, die Gleichheit der zwei Projektionen, die abgelehnte Antwort ohne Frist |
| `CHANGELOG.md` | Ein `Added`-Eintrag unter `## [Unreleased]`: ein Assistent kann sich jetzt per eigenem Metadatendokument verbinden, mit den Grenzen in Nutzersprache |

## Wie der Zweig gebaut ist

**Ein Aufrufpunkt, drei Faelle.** In `get_client` steht heute

```python
        if row is None or row.cimd_fetched_at is not None:
            row = await self._resolve_cimd(client_id, store, row=row)
            if row is None:
                return None
```

und `_resolve_cimd` unterscheidet: keine Zeile (aufloesen), eine Zeile deren Frische
abgelaufen ist (erneut lesen), eine Zeile die noch frisch ist (unveraendert zurueckgeben).
Der Plan legt die Frische-Pruefung in `get_client`; zwei Zweige dort haetten den Schalter
zweimal gefragt oder einmal vergessen, und der Schalter ist die Frage, die vor jedem Paket
kommt. Fuer eine DCR-Zeile ist die Bedingung `False`, also aendert sich auf dem bestehenden
Weg nichts, und der gemeinsame Rest (`_client_information`, `row.allowed`,
`self._policy.allows`) laeuft danach unveraendert. Genau das ist der Grund, warum die vier
AUTH-07-Punkte gratis greifen: es gibt keine zweite Stelle, an der ein Client eingelassen
wird.

**Die Reihenfolge in `_resolve_cimd`**, jede Stufe dort wo sie am billigsten ist: Schalter,
Frische, Schreibweise des Identifiers, Form (`is_cimd_client_id`), Abruf, Modell,
Adressfilter, Zeile. Die ersten vier kosten kein Paket.

**Der Schalter wirkt auch auf eine bestehende Zeile.** Er ist die erste Frage, und weil er
vor der Frische-Antwort steht, ist ein schon aufgeloester CIMD-Client bei abgeschaltetem
CIMD oder DCR sofort draussen und nicht erst nach Ablauf seiner Cache-Frist. Das ist
bewusst strenger als bei DCR (dort bleibt eine bestehende Registrierung gueltig, wenn der
Schalter faellt) und es ist die Lesart, in der "ein abgeschaltetes DCR ist ueber CIMD nicht
umgehbar" auch eine Stunde nach dem Umschalten noch wahr ist.

**Die Zeile ist echt und nicht ein Cache.** `flows.client_id` und
`authorizations.client_id` referenzieren `clients(client_id)`; ein Client, der nur im
Speicher existiert, waere am ersten `/authorize` mit einem `IntegrityError` gescheitert
(Pitfall 3). Ein Test legt nach der Aufloesung einen `flows`-Datensatz mit dieser
`client_id` an und liest ihn zurueck, damit dieser Satz gemessen und nicht behauptet ist.

**`secret_hash` ist in jedem Pfad `None`.** Ein Client dieses Weges ist per Draft public,
`validate_document` lehnt jedes Verfahren mit geteiltem Geheimnis schon ab, und
`client_secret_hash` liest `None` seit Phase 3 als "dieser Client hat kein Secret". Ein
Dokument, das trotzdem ein `client_secret` mitschickt, ist damit kein Sonderfall: der Wert
wird nicht ins Modell projiziert, `model_dump_json(exclude={"client_secret"})` laesst ihn
weg, und ein Test prueft den Datensatz auf beides.

**Nur vier Felder kommen aus dem Dokument** (`client_name`, `redirect_uris`, `grant_types`,
`response_types`), die `client_id` ist die abgerufene und `token_endpoint_auth_method` wird
auf `none` gesetzt. Das ist die Stelle, an der `logo_uri` nicht steht: ein
`model_validate(document)` haette die URL einer ungepruefte Domaene in den Datensatz
geschrieben, und die Zustimmungsseite haette sich in 06-06 erneut dagegen entscheiden
muessen (T-06-13).

**Die Adressen laufen durch dieselbe Funktion wie eine Registrierung**, samt
Teilregistrierung: aus `["cursor://x/cb", "https://www.cursor.com/...", "http://localhost:8787/callback"]`
werden die letzten zwei, und ein Dokument, dessen Adressen alle unzulaessig sind, schreibt
keine Zeile. Kein `RegistrationError` auf diesem Weg: ein AST-Gate liest `get_client`,
`_resolve_cimd` und `_cimd_client_information` und faellt, wenn der Name dort auftaucht.

## Pitfall 4, entschieden und an zwei Stellen

Die Registrierungs-TTL sagt "eine Registrierung, die nie einen Token erzeugt hat", und
`clients` haengt mit `ON DELETE CASCADE` an `authorizations`. Eine CIMD-Zeile ist jederzeit
neu lesbar und damit nie verwaist; abgelaufen ist bei ihr nur die Frische, und die kostet
einen Abruf. Also:

| Stelle | Vorher | Jetzt |
|--------|--------|-------|
| `provider.get_client` | `_has_expired(...)` fuer jede Zeile | nur fuer Zeilen mit `cimd_fetched_at IS NULL` |
| `store.expired_clients` (der Sweep hinter `sweep_expired_clients`) | jede alte Zeile | `cimd_fetched_at IS NULL AND (...)` |
| `store.purge_expired` | unveraendert | unveraendert: sie loescht nur Zeilen ohne Autorisierung, also bleibt sie der Backstop, der die Tabelle endlich haelt |

Die zweite Zeile der Tabelle steht nicht im Plan und ist der Grund, warum die erste
ueberhaupt wirkt: `sweep_expired_clients` haengt an `authorize`, laeuft also bei jeder neuen
Verbindung, und haette die CIMD-Zeile mit ihren App-Passwoertern eingesammelt, waehrend
`get_client` sie gerade verschont hat. Zwei Tests belegen beide Stellen, einer davon mit
einer daran haengenden `authorizations`-Zeile.

## Die Frische, und woher sie kommt

Der Draft verlangt "SHOULD respect HTTP cache headers" und erlaubt eigene Grenzen; die
Referenzimplementierung faehrt 5 Minuten Default mit 1 Stunde Deckel. Umgesetzt als
`cache_lifetime(cache_control)`: `max-age` wird gelesen und auf 300 bis 3600 s gekappt,
`no-store` und `no-cache` enden an der Untergrenze (eine Zeile muss der Fremdschluessel
wegen ohnehin existieren, also heisst "nicht behalten" hier "die kuerzeste Frist dieses
Servers"), `s-maxage` wird bewusst nicht gelesen, und alles Unlesbare endet ebenfalls an der
Untergrenze. `Expires` bleibt draussen, mit dem Grund im Docstring: ein Vergleich zweier
Zeitstempel derselben fremden Antwort entscheidet nichts.

Weil nur der Fetch diesen Header sieht, hat `cimd.py` jetzt zwei Sichten auf eine
Implementierung: `fetch_document_and_lifetime` traegt Dokument und Frist,
`fetch_document` ist derselbe Aufruf ohne die Frist. Die 107 Tests aus 06-02 blieben
dadurch unberuehrt, und ein Test belegt, dass die zwei Sichten ueber denselben Identifier
dasselbe sagen.

## Verifikation

| Prueflauf | Ergebnis |
|-----------|----------|
| `uv run --no-sync pytest tests/unit/test_oauth_store.py -q` | 71 gruen |
| `uv run --no-sync pytest tests/unit/test_oauth_provider.py -q` | 112 gruen |
| `uv run --no-sync pytest tests/unit/test_oauth_cimd.py -q` | 126 gruen |
| `uv run --no-sync pytest tests/unit -q` | gruen |
| `uv run --no-sync pytest` (Default-Auswahl) | 2162 passed, 92 deselected in 57,26 s |
| `uv run --no-sync pytest -m integration -q` | unveraendert: alle 84 skipped (keine laufende Instanz im Lauf) |
| `uv run --no-sync ruff check .` | All checks passed |
| `uv run --no-sync ruff format --check .` | 171 files already formatted |
| `uv run --no-sync pyright` | 0 errors, 0 warnings, 0 informations |
| `uv run --no-sync vulture src scripts vulture_whitelist.py` | keine Ausgabe, Exit 0 |
| Vokabular-Gate | "archiv" in keiner geaenderten Datei, auch nicht im CHANGELOG-Eintrag |
| `pyproject.toml`, `uv.lock` | unveraendert (T-06-SC: dieser Plan installiert nichts) |

Die Grep-Akzeptanzgrenzen des Plans einzeln nachgezaehlt:

| Grenze | Ergebnis |
|--------|----------|
| `grep -c "cimd_fetched_at" src/mcp_connector/oauth/store.py` | 12 (verlangt: mindestens 4) |
| `grep -c "cimd_expires_at" src/mcp_connector/oauth/store.py` | 10 |
| Reihenfolge in `get_client` (`row is None` -> `_resolve_cimd` -> `_client_information`) | Zeilen 340, 347, 351 |
| `RegistrationError` in `get_client`/`_resolve_cimd`/`_cimd_client_information` | keiner, per AST-Gate gehalten |

## Abweichungen vom Plan

### Automatisch behoben

**1. [Rule 2 - fehlende kritische Funktion] Die TTL-Ausnahme braucht die zweite Loeschstelle**

- **Gefunden bei:** Task 1, beim Lesen von `sweep_expired_clients` fuer die Pitfall-4-Frage
- **Problem:** Der Plan nennt nur `_has_expired` in `provider.get_client`. Es gibt aber eine
  zweite Stelle, die eine Client-Zeile samt Kaskade loescht: `store.expired_clients` liefert
  die Liste, `sweep_expired_clients` gibt die App-Passwoerter zurueck und loescht. Dieser
  Sweep haengt an `authorize`, laeuft also bei jeder neuen Verbindung irgendeines Clients.
  Die Ausnahme in `get_client` allein waere damit wirkungslos gewesen, und T-06-31 waere
  offen geblieben, obwohl das Register ihn als `mitigate` fuehrt.
- **Fix:** `expired_clients` filtert `cimd_fetched_at IS NULL`, mit der Begruendung im
  Docstring und zwei Tests (Store-Ebene und Provider-Ebene). `purge_expired` bleibt
  absichtlich unberuehrt: sie loescht nur Zeilen ohne Autorisierung und ist damit der
  Backstop, der die Tabelle endlich haelt.
- **Dateien:** `src/mcp_connector/oauth/store.py`, `tests/unit/test_oauth_store.py`,
  `tests/unit/test_oauth_provider.py`
- **Commits:** 8b7750d, a28a3aa

**2. [Rule 3 - Blocker] Die Cache-Frist war durch die Grenze aus 06-02 nicht erreichbar**

- **Gefunden bei:** Task 2
- **Problem:** Der Plan verlangt, dass die Frist aus den HTTP-Cache-Headern der Antwort
  entsteht (und der Schema-Kommentar aus Task 1 sagt das ausdruecklich). `fetch_document`
  gibt aber nur das Dokument zurueck; der Header existiert ausschliesslich innerhalb von
  `_fetch_pinned`, und die Antwort dorthin herauszugeben haette einem Aufrufer einen offenen
  Stream mit dem Groessenlimit dieses Moduls in die Hand gegeben.
- **Fix:** `cache_lifetime` plus `fetch_document_and_lifetime` in `cimd.py`, und
  `fetch_document` wird zur Projektion derselben Implementierung. Eine Implementierung, zwei
  Sichten, kein bestehender Test geaendert (die 107 aus 06-02 liefen unveraendert weiter).
- **Dateien:** `src/mcp_connector/oauth/cimd.py`, `tests/unit/test_oauth_cimd.py`
- **Commit:** a28a3aa

**3. [Rule 3 - Blocker] Ohne injizierten Resolver haette die Unit-Suite claude.ai aufgeloest**

- **Gefunden bei:** Task 2, beim Schreiben des Happy-Path-Tests
- **Problem:** `_resolve_cimd` ruft den Abruf ohne Resolver, also den des Hosts. Der
  Datei-Docstring von `test_oauth_provider.py` sagt "Nothing here starts a container or
  opens a socket", und eine DNS-Aufloesung ist ein Socket. Ausserdem waere der Test von der
  Netzlage abhaengig geworden.
- **Fix:** Der Provider nimmt `resolver` als Konstruktorargument, in derselben Form wie
  `clock` und `store_provider` (Shared Pattern der Testdatei); `build()` gibt in jedem Test
  einen Resolver herein, der ein festes oeffentliches Literal antwortet, und `respx`
  antwortet auf der gepinnten URL. Kein Patch einer Bibliotheksfunktion.
- **Dateien:** `src/mcp_connector/oauth/provider.py`, `tests/unit/test_oauth_provider.py`
- **Commit:** a28a3aa

**4. [Rule 2 - fehlende kritische Pruefung] Eine ungetrimmte client_id ist eine Absage**

- **Gefunden bei:** Task 2
- **Problem:** `is_cimd_client_id` und `fetch_document` trimmen den Identifier, `get_client`
  bekommt ihn ungetrimmt. Der Abruf waere unter einer Schreibweise gelaufen und die Zeile
  unter einer anderen geschrieben worden. Genau diese Differenz zwischen zwei Schreibweisen
  ist das, was der zeichengenaue Vergleich aus 06-02 verhindern soll.
- **Fix:** `_resolve_cimd` lehnt einen Identifier ab, der nicht seine eigene getrimmte Form
  ist; ein Test prueft es zusammen mit den anderen Formabsagen und mit ungerufener Route.
- **Dateien:** `src/mcp_connector/oauth/provider.py`, `tests/unit/test_oauth_provider.py`
- **Commit:** a28a3aa

**5. [Rule 1 - Bug im Testentwurf] Das AST-Gate zog die Docstrings nicht ab**

- **Gefunden bei:** Task 2, erster Testlauf
- **Problem:** Das Gate "kein `RegistrationError` auf diesem Pfad" faellt sofort, weil der
  Docstring von `_resolve_cimd` ausdruecklich erklaert, warum dort kein
  `RegistrationError` benutzt wird. Dasselbe Muster wie die zwei Grep-Kollisionen aus 06-02.
- **Fix:** Das Gate zieht den Docstring des Knotens ab, bevor es unparst, genau wie das
  Throttle-Gate derselben Datei; die Begruendung steht im Testdocstring.
- **Dateien:** `tests/unit/test_oauth_provider.py`
- **Commit:** a28a3aa

**6. [Rule 2 - Owner-Regel] CHANGELOG-Eintrag ergaenzt**

- **Gefunden bei:** nach Task 2
- **Problem:** Der Plan nennt `CHANGELOG.md` nicht, aber ab diesem Commit wirkt etwas nach
  aussen: ein Client kann sich ohne Registrierung verbinden. Der Eintrag unter
  `## [Unreleased]` ist Owner-Regel.
- **Fix:** Ein `Added`-Eintrag in Nutzersprache, mit den Grenzen (nur https und Loopback als
  Rueckadressen, Allowlist, kein geteiltes Geheimnis, nur oeffentliche Ziele, kein Redirect,
  kein Bild), ohne Em-Dashes und ohne das verbotene Vokabular.
- **Dateien:** `CHANGELOG.md`
- **Commit:** a28a3aa

### Bewusste Auslegung des Plan-Zuschnitts

Der Plan legt die Frische-Pruefung nach `get_client` und die Cache-Treffer-Frage
ausdruecklich nicht in `_resolve_cimd`. Umgesetzt ist beides in `_resolve_cimd`, mit einem
Aufrufpunkt in `get_client`. Der Grund steht im Docstring: der Schalter muss die erste Frage
sein, und mit zwei Zweigen im Aufrufer waere er entweder zweimal gefragt oder in einem der
drei Faelle vergessen worden. Die Akzeptanzgrenze (der Zweig steht zwischen `row is None`
und `_client_information`) ist erfuellt.

### Bewusst nicht getan

`consent.py`, `metadata.py` und die Zustimmungsseite blieben unberuehrt (das ist 06-06).
Keine neunte Drosselklasse: der Abruf haengt an `/authorize`, und `CLASS_AUTHORIZE_START`
drosselt diese Route schon; `/token` und `/revoke` finden die Zeile im Normalfall frisch
vor, weil die Untergrenze der Frist 300 s ist, also faellt kein Abruf in das
Zehn-Sekunden-Budget des Token-Endpunkts.

## Was dieser Plan nicht tut

Kein neues Paket, kein `os.environ`, kein modul-globaler veraenderlicher Zustand, keine neue
Route, kein neues Fehlerbild. Die Zustimmungsseite zeigt noch nicht, dass eine Identitaet
aus einem Dokument stammt, und sie warnt noch nicht bei einer reinen Loopback-Adresse; beides
ist 06-06. Der Live-Rundlauf mit echtem Claude Code ist 06-09.

## Known Stubs

Keine. `_resolve_cimd`, `cache_lifetime` und die zwei Spalten tun vollstaendig, was ihre
Docstrings sagen.

## Threat Flags

Keine neue Angriffsflaeche ausserhalb des Threat-Registers dieses Plans. Die eine
Erweiterung, die das Register nicht wortgleich vorsah, ist die Ausnahme in
`store.expired_clients`, und sie liegt innerhalb von T-06-31 (dieselbe Absicht, zweite
Stelle). Es entsteht kein Endpunkt und kein neuer Auth-Pfad; die Schema-Aenderung sind zwei
nullable Spalten ohne Datenmigration.

## Requirements

**AUTH-08 bleibt Pending, bewusst.** Der Wortlaut lautet "kann sich verbinden", und der
Nachweis dieses Projekts fuer einen Verbindungssatz ist eine Messdatei mit einem echten
Client gegen eine laufende Instanz. Im Code ist AUTH-08 mit diesem Plan vollstaendig
(Schalter, Advertising, Zweig, Adressregel, Allowlist, Frische); abgehakt wird es in 06-09,
zusammen mit CLIENT-05. AUTH-09 ist seit 06-02 erfuellt und wurde hier nicht angefasst.

## Self-Check: PASSED

`06-05-SUMMARY.md` liegt auf der Platte, die zwei Task-Commits stehen im Log (`8b7750d`,
`a28a3aa`), alle sieben geaenderten Quell-, Test- und Doku-Dateien sind darin enthalten, und
der volle Default-Lauf wurde nach dem letzten Quellcode-Commit wiederholt (2162 passed).
