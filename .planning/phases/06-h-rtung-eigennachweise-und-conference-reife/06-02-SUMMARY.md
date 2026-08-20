---
phase: 06-h-rtung-eigennachweise-und-conference-reife
plan: 02
subsystem: oauth
tags: [cimd, ssrf, dns-rebinding, ip-pinning, sni_hostname, respx, fail-closed, no-cache]

# Dependency graph
requires:
  - phase: 06-01
    provides: "is_cimd_client_id, target_allowed, resolve_addresses, AddressLookup, MAX_DOCUMENT_BYTES, FETCH_TIMEOUT_SECONDS, exapp.responses.bounded_response"
provides:
  - "cimd.fetch_document(client_id, *, resolver=...) als die eine Modulgrenze nach aussen: ein Dokument oder None, in jedem Fehlerfall None, nie eine Exception"
  - "cimd.validate_document(raw, client_id) mit den vier MUSTs der Spec in Spec-Reihenfolge, zeichengenauem client_id-Vergleich und ohne jede logo_uri-Verarbeitung"
  - "IP-Pinning als Muster: Request auf das geprueft IP-Literal, Original-Name in Host und sni_hostname, genau eine Aufloesung pro Aufruf"
  - "Der Negativkatalog AUTH-09 vollstaendig, inklusive benanntem Rebinding-Test und dem Beleg, dass Fehler und kaputte Dokumente nicht gecacht werden"
affects: [AUTH-08, 06-04, 06-05, 06-06, 06-09]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ein Outbound-Request in eine fremde Vertrauensdomaene baut seinen eigenen httpx.AsyncClient pro Aufruf und teilt sich nichts mit dem Credential-tragenden Pfad: die Haltung von nextcloud/http.py wird kopiert, das Objekt nicht"
    - "Die gepruefte Adresse ist die verbundene Adresse: url.copy_with(host=literal) plus Host-Header und extensions={'sni_hostname': name}, damit TLS und Zertifikatspruefung auf dem echten Namen bleiben"
    - "Ein privates _Refused traegt sieben Absagen durch das Modul und stirbt an der Modulgrenze in None (D-37): der Handler sieht nur einen Wert oder eine Absage"
    - "Zeichengenauer Vergleich statt Normalisierung, im Stil der issuer-Regel von metadata.py: eine Normalisierung waere die Differenz, die ein Angreifer bekommt"
    - "Der Beleg einer Grenze ist ein Test, der die Grenze am Transport benennt: nicht 'nichts passierte', sondern 'genau dieses Ziel wurde nicht kontaktiert' (respx-Route auf der URL, die ein gepinnter Abruf benutzt haette)"

key-files:
  created:
    - .planning/phases/06-h-rtung-eigennachweise-und-conference-reife/06-02-SUMMARY.md
  modified:
    - src/mcp_connector/oauth/cimd.py
    - tests/unit/test_oauth_cimd.py
    - .planning/STATE.md

key-decisions:
  - "Task 1 dekodiert das Dokument zunaechst inline (JSON plus Objekt-Pruefung) und Task 2 ersetzt diese fuenf Zeilen durch validate_document mit den vier MUSTs: so ist jeder der beiden Commits fuer sich lauffaehig und keiner enthaelt eine Funktion, die weniger tut, als ihr Name behauptet"
  - "Kein CHANGELOG-Eintrag: der Abruf haengt noch an keiner Route, provider.get_client ruft ihn erst in 06-05; nach aussen aendert sich in diesem Plan nichts. Derselbe Grund wie in 06-01"
  - "Kein Content-Type-Zwang auf der Antwort: der Draft macht keinen daraus, das JSON-Parsen ist die haertere Pruefung, und eine erfundene Absage waere eine, die wir gegen einen echten Client nicht verteidigen koennten"
  - "Der Vergleich in validate_document laeuft gegen die getrimmte Zeichenkette, mit der auch abgerufen wurde: is_cimd_client_id akzeptiert fuehrende Leerzeichen, und die abgerufene URL ist die getrimmte, also ist sie auch die verglichene"
  - "Ein IPv6-Pinning-Test kam ueber den Plan hinaus dazu: die Klammerform ist die eine Stelle, an der eine v6-Adresse in einer URL zweimal falsch werden kann, und sie war ungeprueft"

patterns-established:
  - "Die Zuordnung Test zu Katalogzeile zu Threat-ID steht im Datei-Docstring der Testdatei, nicht in einer Planungsdatei: sie wird mit den Tests gelesen und mit ihnen veraltet oder nicht"
  - "Eine Grenze wird gegengeprobt, indem sie lokal entfernt und der Testlauf gezaehlt wird; das Ergebnis steht in der Zusammenfassung, die Entfernung wird zurueckgenommen"

requirements-completed: [AUTH-09]

# Metrics
duration: 40min
completed: 2026-08-20
---

# Phase 06 Plan 02: Der gepinnte CIMD-Abruf Summary

**Der Abruf des Metadatendokuments geht auf die Adresse, die geprueft wurde, und nicht ein
zweites Mal auf den Namen: ein Resolver, der beim zweiten Aufruf 127.0.0.1 sagt, aendert
nichts, weil es keinen zweiten Aufruf gibt.**

## Performance

- **Duration:** 40 min
- **Tasks:** 3 von 3
- **Files modified:** 2 Quelldateien, 1 Zusammenfassung, 1 Zustandsdatei

## Task Commits

1. **Task 1: Der gepinnte Abruf mit Groessen-, Zeit- und Redirect-Grenze** , `cfd9b24` (feat)
2. **Task 2: validate_document mit den vier MUSTs der Spec** , `8b01693` (feat)
3. **Task 3: Der Negativkatalog AUTH-09, inklusive Rebinding und Nicht-Cachen** , `de798f5` (test)

## Was entstanden ist

| Datei | Inhalt |
|-------|--------|
| `src/mcp_connector/oauth/cimd.py` | `fetch_document` als einzige Modulgrenze nach aussen, `validate_document`, das private `_fetch_pinned`, das private `_Refused`, die Konstanten `_REQUIRED` und `_FORBIDDEN_AUTH` |
| `tests/unit/test_oauth_cimd.py` | von 48 auf 107 Tests; der Fetch-Abschnitt, der Dokument-Abschnitt und der Abschnitt "rebinding, the cache prohibition, and every target class", plus die Zuordnungstabelle im Datei-Docstring |

## Wie der Abruf gebaut ist

**Der Request geht auf das IP-Literal.** `url.copy_with(host=literal)` schreibt die URL um
(IPv6 in eckigen Klammern), der `Host`-Header traegt `url.netloc`, und
`extensions={"sni_hostname": name}` haelt TLS und Zertifikatspruefung auf dem echten Namen,
weil `httpcore` 1.0.9 die Extension als `server_hostname` in den Handshake gibt. Der Code aus
06-RESEARCH.md Pattern 3 war gelesen, aber nie ausgefuehrt; jetzt ist er ausgefuehrt, und der
Ausfuehrungsbeleg ist der Test, der am gesendeten Request alle drei Eigenschaften gleichzeitig
prueft (`sent.url.host` ist die IP, `sent.headers["host"]` und
`sent.extensions["sni_hostname"]` sind der Name). Ein zweiter Test tut dasselbe fuer
`2606:4700:4700::1111`, weil die Klammerform die eine Stelle ist, an der eine v6-Adresse in
einer URL zweimal falsch werden kann.

**Die Reihenfolge ist die des Diagramms**, und jede Stufe steht dort, wo sie am billigsten
ist: Formpruefung (kostet kein Paket), Aufloesung (genau eine), gepinnter Abruf auf der ersten
gepruefte Adresse, Dokumentregeln. Der Resolver reist als Keyword mit, also stellt der
Rebinding-Test ihn, ohne eine Bibliotheksfunktion zu patchen.

**Sieben Wege in dieselbe Absage.** Ein Status ungleich 200 (also auch jedes 3xx),
`BodyTooLarge`, `BodyUnreadable`, eine Transport-Exception, ein Timeout, ein Dokument, das
kein JSON-Objekt ist, und eine Dokumentregel, die faellt. Innerhalb des Moduls traegt ein
privates `_Refused` sie, an der Modulgrenze werden sie `None`: aus `fetch_document` kommt in
keinem Pfad eine Exception, und ein parametrierter Test ueber 302, 400, 401, 403, 404, 500 und
503 sagt das ausdruecklich.

**Kein Negativ-Cache, und das ist eine Zusicherung und keine Auslassung.** Der Draft verbietet
das Cachen von Fehlerantworten und ungueltigen Dokumenten woertlich. Zwei Tests belegen es von
aussen: 500 dann 200, und kaputtes JSON dann gutes; beide Male zaehlt die respx-Route zwei
Calls und der zweite Aufruf liefert ein Dokument. Der Docstring nennt, wohin die Drosselung
stattdessen gehoert (`oauth/throttle.py`, `CLASS_AUTHORIZE_START` drosselt die Route, an der
der Abruf haengt) und dass dieser Plan keine neunte Klasse auf Verdacht erfindet.

## Wie das Dokument geprueft wird

Die vier MUSTs in Spec-Reihenfolge: gueltiges JSON und ein Objekt, die drei Pflichtfelder,
`client_id` zeichengleich mit der Abruf-URL, und kein Authentifizierungsverfahren mit
geteiltem Geheimnis. Der Vergleich in Schritt 3 ist derselbe Stil, den `metadata.py` fuer den
`issuer` fuehrt: keine Normalisierung, weil eine Normalisierung genau die Differenz zwischen
zwei Schreibweisen an einen Angreifer verschenkt. Der Negativkatalog nimmt das ernst und
enthaelt drei Varianten davon, die alle abgelehnt werden: ein Schraegstrich am Ende, eine
andere Gross-/Kleinschreibung, und eine fremde URL.

`logo_uri` wird nicht gelesen, und der Docstring haelt fest, warum: ein zweiter
Outbound-Request in eine ungepruefte Domaene und ein Cross-Domain-Tracking-Kanal auf jeder
Zustimmungsseite (Draft 6.7, T-06-13). `redirect_uris` wird auf seine Form geprueft und
**nicht** gefiltert: D-35 lebt in `provider.py`, und eine zweite Filterstelle waere eine
zweite Wahrheit.

Das echte Claude-Code-Dokument liegt als Testkonstante in der Datei, mit dem Tag, an dem es
abgerufen wurde, und ein Test belegt, dass es jede Regel passiert. Ein Regelwerk, das den
Kandidat-Client dieser Phase ablehnt, waere ein Regelwerk, das die Phase nicht erfuellt.

## Der Negativkatalog, und wozu er gut ist

Der Datei-Docstring traegt jetzt die Zuordnung Katalogzeile zu Test zu Threat-ID. Das ist der
Nachweis fuer Success Criterion 2 der Phase, und drei Eintraege sind die, die ohne diesen Task
gefehlt haetten:

1. **Rebinding.** Der Resolver antwortet beim ersten Aufruf oeffentlich und danach mit
   `127.0.0.1`. Der Test prueft drei Dinge zusammen, weil eines allein nichts beweist: das
   Ergebnis ist dasselbe wie ohne den Versuch, der Resolver wurde genau einmal gefragt, und
   die respx-Route auf `https://127.0.0.1/c.json` bleibt uncalled. Das Wort "rebinding" steht
   im Testnamen, damit die Absicht auffindbar ist.
2. **Nicht-Cachen**, siehe oben, zweimal.
3. **Kein Netzwerkverkehr bei einer Formabsage.** Acht Formen von `client_id` (nicht https,
   Pfad fehlt, Fragment, Userinfo, zwei Dot-Segment-Varianten, leer) und in jedem Fall
   `route.called is False` **und** der Resolver ungefragt.

Dazu die acht Ziel-Absagen und die gemischte Aufloesung, jede gegen die exakte URL, die ein
gepinnter Abruf benutzt haette: die Zusicherung ist nicht "es passierte nichts", sondern
"dieses Ziel wurde nicht kontaktiert".

**Die Gegenprobe.** Die Konjunktion in `target_allowed` wurde lokal auf `not addr.is_private`
verkuerzt und der Lauf gezaehlt: **sieben Tests rot** (die drei gemessenen Luecken je zweimal,
in der Regel und am Transport, plus die Zusicherung der Messung selbst), verlangt waren
mindestens drei. Die Verkuerzung wurde danach zurueckgenommen und die Datei ist byteweise
identisch mit dem Zustand davor.

## Verifikation

| Prueflauf | Ergebnis |
|-----------|----------|
| `uv run --no-sync pytest tests/unit/test_oauth_cimd.py -q` | gruen, 107 Tests |
| `uv run --no-sync pytest tests/unit -q` | gruen (keine Regression in den Nachbarsuiten) |
| `uv run --no-sync pytest` (Default-Auswahl) | 2090 passed, 92 deselected in 55,51 s |
| `uv run --no-sync ruff check .` | All checks passed |
| `uv run --no-sync ruff format --check .` | 171 files already formatted |
| `uv run --no-sync pyright` | 0 errors, 0 warnings, 0 informations |
| `uv run --no-sync vulture src scripts vulture_whitelist.py` | keine Ausgabe, Exit 0 |
| Vokabular-Gate | "archiv" kommt in keiner der beiden Dateien vor |
| `pyproject.toml`, `uv.lock` | unveraendert (T-06-SC: dieser Plan installiert nichts) |

Die Grep-Akzeptanzgrenzen wurden einzeln nachgezaehlt: `shared_client` null,
`follow_redirects=False` zwei (Code und Docstring), `follow_redirects=True` null,
`redirect_uri_allowed` null, `logo_uri` genau einmal und nur im Docstring, `Resolve` und
`elicit` null (Contract-Gate).

## Abweichungen vom Plan

### Automatisch behoben

**1. [Rule 3 - Blocker] Zwei Docstring-Formulierungen kollidierten mit Grep-Akzeptanzgrenzen**

- **Gefunden bei:** Task 1 und Task 2, beim Nachzaehlen der Akzeptanzkriterien
- **Problem:** Zwei Kriterien sind Grep-Zaehlungen ueber die Quelldatei
  (`shared_client` == 0, `redirect_uri_allowed` == 0). Beide waren durch **Prosa** verletzt,
  nicht durch Code: der Docstring von `_fetch_pinned` nannte
  `nextcloud/http.shared_client()` als das, was der Fetch bewusst **nicht** benutzt, und der
  Docstring von `is_cimd_client_id` nannte seit 06-01 `registry.redirect_uri_allowed` als das
  Vorbild seiner drei Absagen. Ein Gate, das eine Verneinung nicht von einer Verwendung
  unterscheiden kann, ist namensblind, aber nicht falsch: es haelt die Absicht "diese Namen
  kommen in dieser Datei nicht vor".
- **Fix:** Beide Stellen benennen dieselbe Sache ohne den Namen ("der prozessweite Client von
  `nextcloud/http.py`", "die Adresspruefung der Registry"). Die Aussage ist unveraendert, die
  Zaehlungen sind null. Die zweite Aenderung beruehrt eine Zeile aus 06-01.
- **Dateien:** `src/mcp_connector/oauth/cimd.py`
- **Commits:** cfd9b24, 8b01693

**2. [Rule 2 - fehlende kritische Pruefung] `httpx.URL` wird gegen sich selbst abgesichert**

- **Gefunden bei:** Task 1
- **Problem:** Die Formpruefung laeuft auf `urlsplit`, der Abruf auf `httpx.URL`. Zwei
  Bibliotheken, die eine Zeichenkette unterschiedlich zerlegen, sind der klassische Weg zu
  einem Ziel, das die Pruefung nicht gesehen hat; `httpx.URL` kann fuer Randfaelle auch
  einfach werfen, und eine Exception aus `fetch_document` verbietet D-37.
- **Fix:** Der Aufbau von `httpx.URL`, `raw_host` und `port` liegt in einem `try`, und ein
  Fehler ist eine Absage mit Log der Fehlerart. Der Kommentar sagt den Grund: zwei
  Bibliotheken, die sich ueber ein Ziel nicht einig sind, sind eine Absage und keine Wahl.
- **Dateien:** `src/mcp_connector/oauth/cimd.py`
- **Commit:** cfd9b24

**3. [Rule 2 - fehlende kritische Pruefung] Ein IPv6-Pinning-Test ueber den Plan hinaus**

- **Gefunden bei:** Task 1
- **Problem:** Der Plan verlangt einen Pinning-Test. Die Klammerform der v6-Adresse
  (`copy_with(host="[::1]")` gegen `copy_with(host="::1")`) ist aber die eine Stelle, an der
  das Umschreiben still das Falsche tun kann, und sie waere ungeprueft geblieben.
- **Fix:** Ein zweiter Pinning-Test mit `2606:4700:4700::1111`, der dieselben drei
  Eigenschaften am gesendeten Request prueft.
- **Dateien:** `tests/unit/test_oauth_cimd.py`
- **Commit:** cfd9b24

### Bewusste Auslegung des Plan-Zuschnitts

Der Plan legt `fetch_document` in Task 1 und `validate_document` in Task 2, waehrend Task 1
schon einen Test hat, der bei genau 5120 Bytes **ein Dokument** verlangt. Umgesetzt so: Task 1
dekodiert inline (JSON plus Objekt-Pruefung, fuenf Zeilen), Task 2 ersetzt diese fuenf Zeilen
durch `validate_document` mit den vier MUSTs. Damit ist jeder Commit fuer sich vollstaendig
und keiner enthaelt eine Funktion, die weniger tut, als ihr Name verspricht.

## Was dieser Plan nicht tut

Keine Route, kein Schalter, keine Store-Spalte, kein Consent-Text. `provider.get_client` ruft
`fetch_document` noch nicht: das ist 06-05, und der Schalter aus 06-03 wird dort gefragt,
bevor das erste Paket geht. Der Positiv-Cache mit seiner Frist gehoert zu denselben
Store-Spalten und ist bewusst hier nicht vorweggenommen worden; der Teil des kontrollierten
Cachens, der eine Sicherheitsgrenze ist (das Verbot des Negativ-Caches), steht und ist
getestet. Kein neues Paket, kein `os.environ`, kein modul-globaler veraenderlicher Zustand.

## Known Stubs

Keine. `fetch_document` und `validate_document` tun vollstaendig, was ihre Docstrings sagen;
was fehlt, ist ihr Aufrufer, und der ist Gegenstand von 06-05.

## Threat Flags

Keine neue Angriffsflaeche ausserhalb des Threat-Registers dieses Plans. Der Plan schafft die
erste Outbound-Verbindung dieses Projekts in eine fremde Vertrauensdomaene, und genau dafuer
ist das Register geschrieben (T-06-07 bis T-06-14, alle `mitigate` bis auf T-06-10, das
bewusst an die vorhandene Drosselung uebergibt). Es entsteht kein Endpunkt, kein Auth-Pfad,
kein Dateizugriff und keine Schema-Aenderung.

## Requirements

**AUTH-09 ist erfuellt.** Nur https, Pfad Pflicht, kein Fragment/Userinfo/Dot-Segment; keine
privaten, Loopback-, link-lokalen, reservierten, Multicast- oder unspezifizierten Ziele, auch
nicht als v4-mapped, NAT64 oder CGNAT, und auch nicht nach einer zweiten DNS-Antwort;
Groessenlimit 5120 Bytes mit Abbruch im Chunk-Loop, Connect- und Read-Timeout 5 s; kontrolliert
im Sinne des Drafts heisst hier: Fehlerantworten und kaputte Dokumente werden nachweislich
nicht gecacht, die Drosselung liegt bei `throttle.py`. Und jede dieser Grenzen hat einen
Negativtest, dessen Zuordnung zur Katalogzeile und zur Threat-ID im Datei-Docstring steht.

## Self-Check: PASSED

`src/mcp_connector/oauth/cimd.py` und `tests/unit/test_oauth_cimd.py` liegen auf der Platte,
die drei Task-Commits sind im Log (cfd9b24, 8b01693, de798f5), und der volle Default-Lauf ist
nachgeprueft gruen (2090 passed).
