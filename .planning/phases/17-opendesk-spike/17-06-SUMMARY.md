---
phase: 17-opendesk-spike
plan: 06
subsystem: auth-measurement
tags: [spike, opendesk, od-02, weg-0, integration-openproject, s3, s4, s6, zwei-konten, d-05, d-12]
requires:
  - "17-05: integration_openproject 3.1.1 im Modus oauth2, alice mit opa (id 5), bob mit opb (id 6), carol unverbunden, allow_local_remote_servers true, die 17 OCS-Routen samt Ausschlussliste"
  - "17-04: die Form des Zwei-Konten-Negativbeweises auf Weg 1 und DI-17-02"
  - "17-03: privates Projekt spike-privat-b (id 3), Arbeitspaket 38 mit dem Suchwort SPIKE-OD-8471, Mitglied nur opb"
provides:
  - "S3 gemessen: der Zwei-Konten-Negativbeweis liegt jetzt auf beiden Wegen vor (D-05 erfuellt), alice 200 mit 0 Treffern, bob 200 mit genau einem"
  - "Die Kette von Weg 0 als Satz belegt: Nextcloud entscheidet per AppAPI-Impersonation die Identitaet, OpenProject die Sichtbarkeit"
  - "Der Grund fuer die leere Vorgabe-Suche gemessen: der Filter linkable_to_storage_url greift ohne registrierte Ablage fuer kein Konto, GET /api/v3/storages total 0"
  - "S4 gemessen und damit die Behauptung geklaert, an der Weg 0 hängt: kuenstlicher Ablauf 0, Aufruf 200, danach token_expires_at 7200 s in der Zukunft, ohne Cookie und ohne App-Passwort"
  - "Die Gegenprobe, die S4 erst zu einem Erneuerungsnachweis macht: unbrauchbarer refresh_token liefert 401 mit invalid_grant im Protokoll"
  - "S4 ein zweites Mal, mit natuerlich verstrichenem Ablauf an alice (19623 s), gleicher Ausgang: der kuenstliche Ablauf ist als Messweg gegengeprobt"
  - "S6 gemessen: 4746 Bytes als bob, davon 3895 in 49 HAL-Relationen und 585 in 24 Feldern; Gegenprobe alice 2542 Bytes mit 27 Relationen"
  - "Die Bezugsgroesse, ohne die die Bytezahl wertlos wäre: API v3 derselben Instanz roh 15831 gegen 88 Bytes mit select, dazu der gemessene Befund, dass select nur an der Sammlung wirkt"
  - "Abschnitt 3 des Berichts vollstaendig: Feldsatz, Relationenliste, drei Lücken der OCS-Flaeche, der file-links-Fund, ausdruecklich ohne Entscheidung ueber den Werkzeugschnitt"
  - "DI-17-04: die fuer OD-04 wertvollste Route ist die einzige unerprobte, und der Grund hängt an DI-17-03"
affects:
  - "17-07 bekommt mit alice ein verbundenes und frisch erneuertes Konto (token_expires_at 1787975808) und die gemessene erste Haelfte der oauth2-gegen-oidc-Asymmetrie, gegen die S5 zu lesen ist"
  - "17-08 bekommt zwei Fragen mit Grund: liefert der openDesk-Bootstrap die Nextcloud-Ablage in OpenProject fertig eingerichtet aus, und rechnet ZenDiS mit dem Byte-Aufwand einer Flaeche ohne select"
  - "17-09 kann 2.4 jetzt entscheiden: von Weg 0 fehlt nur noch S5, und Abschnitt 3 liegt als Zahlenbasis vor, ohne der Entscheidung vorzugreifen"
  - "OD-04 bekommt aus 3.1 bis 3.3 den Feldsatz, die Byte-Kosten mit ihren zwei Abhaengigkeiten und die drei Lücken, dazu aus DI-17-04 die benannte offene Stelle"
tech-stack:
  added: []
  patterns:
    - "Eine Messmethode, die einen Zustand stellt, braucht selbst eine Gegenprobe: der natuerlich verstrichene Ablauf belegt, dass der gestellte Ablauf dasselbe misst, und raeumt den einzigen Einwand gegen die Methode aus"
    - "Eine Bytezahl nie ohne ihre Abhaengigkeiten berichten: dieselbe Flaeche liefert 4746 und 2542 Bytes, je nach Berechtigung des Nutzers und Modulsatz des Projekts, und wer daraus ein Budget rechnet, rechnet mit dem guenstigsten Fall"
    - "Bei einer Groessenmessung den Aufbauzugang zulassen und ausdruecklich kennzeichnen: fuer die Groesse einer Antwort ist er zulaessig, fuer eine Aussage ueber Berechtigungen nicht"
    - "Wenn ein Abschnitt keine Entscheidung treffen darf, den Satz hinschreiben, der sagt wer sie trifft und wann, statt die Entscheidung nur wegzulassen"
    - "Ein Fund, der die eigene Schlussfolgerung schwaecht (die wertvollste Route ist die unerprobte), gehoert in den Bericht und in die Uebergabe, nicht in eine Fussnote"
key-files:
  created: []
  modified:
    - "docs/spike-opendesk.md"
    - ".planning/phases/17-opendesk-spike/deferred-items.md"
decisions:
  - "Der natuerlich verstrichene Ablauf an alice ist als eigener Messwert in den Bericht genommen und nicht als Nebenbeobachtung verworfen: er ist die Gegenprobe zur Methode des kuenstlichen Ablaufs und damit der Teil von S4, der ohne ihn angreifbar geblieben wäre"
  - "Die Byte-Messung ist mit einer zweiten Antwort unter einem anderen Konto gegengeprobt worden, obwohl der Plan nur eine verlangt; ohne sie wäre aus einer Einzelmessung eine Budgetgroesse geworden"
  - "Fuer die Bezugsgroesse ist der Aufbauzugang des Kontos admin benutzt und an jeder Stelle als solcher gekennzeichnet worden; er taucht in keinem Messwert von S3 oder S4 auf"
  - "Abschnitt 3 trifft ausdruecklich keine Entscheidung ueber den Werkzeugschnitt und sagt das im Text; die Wahl gehoert 17-09 und OD-04 (D-12)"
  - "OD-02 bleibt Pending: dieser Plan schliesst von Weg 0 S3, S4 und S6 ab, S5 fehlt und ist 17-07. Fortsetzung der Entscheidung aus 17-01 bis 17-05"
metrics:
  duration: 52 min
  completed: 2026-08-29
---

# Phase 17 Plan 06: Die drei Weg-0-Messungen ohne OIDC Summary

Weg 0 trägt, und das steht jetzt gemessen da statt argumentiert: die Berechtigungsgrenze hält zwischen zwei Konten, die serverseitige Erneuerung läuft ohne jede Browsersitzung, und beide Befunde tragen die Gegenprobe, ohne die sie nichts wert wären. Der teuerste Zusatz des Plans ist ein zweiter S4-Beleg, der gar nicht geplant war: der Ablauf von `alice` war von selbst verstrichen, und derselbe Aufruf hat sich genauso erneuert wie nach dem gestellten Ablauf.

## Die drei Messwerte, die dieser Plan schuldig war

| Behauptung | Messweg | Messwert | Gegenprobe |
|-----------|---------|----------|------------|
| **S3**, Zwei-Konten-Negativbeweis auf Weg 0 (D-05) | `GET /ocs/v2.php/apps/integration_openproject/api/v1/work-packages?searchQuery=SPIKE-OD-8471&isSmartPicker=true`, reine AppAPI-Impersonation, kein App-Passwort im Prozess | `alice` **200 mit 0 Treffern**, `bob` **200 mit genau einem** (`id 38`, `subject SPIKE-OD-8471 privat`) | drei Stück: Suchwort `Demo` liefert `alice` **14** Treffer und die `38` ist nicht darunter (also kein Tippfehler und keine kaputte Suche); 64 Nullen als `APP_SECRET` **401/997**; `carol` **401** mit leerer Meldung |
| **S4**, Erneuerung ohne Browsersitzung | `occ user:setting bob ... token_expires_at 0`, dann derselbe OCS-Aufruf, dann beide Zustandswerte erneut lesen | `1787949020` vorher, künstlich `0`, Aufruf dazwischen **200** mit einem Treffer, danach **`1787950505`**, also genau **7200 s** in der Zukunft; `token` und `refresh_token` beide mit neuem Präfix | unbrauchbarer `refresh_token` (43 Nullen), derselbe Ablauf, derselbe Aufruf: **401**, und im Protokoll `Failed to refresh token ... {"error":"invalid_grant"}` |
| **S4 noch einmal, ohne jeden Eingriff** (Nachtrag 29.08.) | `alice`, Ablauf aus 17-05 **von selbst** verstrichen, an diesem Konto nie ein `occ user:setting` | Ablauf **19623 s** alt, Aufruf **200** mit einem Treffer, danach **`1787975808`**, also **+7176 s** | der gestellte und der echte Ablauf sind gemessen deckungsgleich; damit ist die Methode des künstlichen Ablaufs selbst gegengeprobt |
| **S6**, Byte-Kosten und Feldsatz | dieselbe Antwort wie S3, als `bob`, minifiziert gezählt | **4746 Bytes**, davon **3895 in 49 HAL-Relationen** und **585 in 24 Feldern** | zweite Antwort unter `alice`: **2542 Bytes**, 27 Relationen, 22 Felder. Dazu die Bezugsgröße über API v3: roh **15831** gegen **88 Bytes** mit `select` |

## S4 steht auf zwei Beinen, und das zweite ist nicht geplant gewesen

Der Plan verlangt einen gestellten Ablauf. Genau daran bleibt die Messung angreifbar: `0` ist zugleich der Vorgabewert von `isAccessTokenExpired()`, und ein Prüfer darf fragen, ob ein von Hand gesetzter Zustandswert überhaupt dasselbe auslöst wie eine wirklich verstrichene Frist.

Diese Frage ist beantwortet, und zwar durch einen Lauf, der als Nachprüfung der S6-Zahlen gedacht war. Der `token_expires_at` von `alice` aus Plan 17-05 (`1787949009`) war zum Zeitpunkt des Aufrufs (`1787968632`) **19623 Sekunden alt**, weit jenseits des Sicherheitsabstands von 60 Sekunden. An diesem Konto ist zu keinem Zeitpunkt ein `occ user:setting` gefahren worden.

| | gestellter Ablauf (`bob`) | verstrichener Ablauf (`alice`) |
|---|---|---|
| wie der Ablauf entstand | `occ user:setting ... token_expires_at 0` | von selbst, zwischen 17-05 und diesem Aufruf |
| Aufruf | 200, ein Treffer | 200, ein Treffer |
| `token_expires_at` danach | `1787950505`, +7200 s | `1787975808`, +7176 s |

**Der gestellte und der echte Ablauf sind gemessen deckungsgleich.** Damit ist nicht nur S4 belegt, sondern auch der Messweg, mit dem S4 belegt wurde, und die Erneuerung hängt nachweislich nicht an einer Besonderheit des Wertes `0`.

## Der Grund, warum die Vorgabe-Suche für beide Konten leer ist

Die erste Fassung von S3, genau nach dem Wortlaut des Auftrags, lieferte für `alice` **und** für `bob` null Treffer. Nach dem Ungemessen-Fallback des Plans wäre der Beweis damit leer gewesen. Er ist es nicht, und die Ursache ist gemessen statt geraten: `getSearchedWorkPackages()` setzt den Filter `linkable_to_storage_url` immer dann, wenn `isSmartPicker` nicht gesetzt ist (`OpenProjectAPIController.php:148`, Vorgabe `false` in Zeile 137). Der Filter verlangt, dass ein Arbeitspaket zu einer in OpenProject **registrierten** Nextcloud-Ablage verlinkbar ist, und `GET /api/v3/storages` antwortet in dieser Instanz `total 0`.

**Der Zusammenhang dahinter ist der eigentliche Befund:** die Ablage entsteht auf Weg A, und Weg A ist in dieser Topologie gemessen nicht gangbar (5.4, DI-17-03). Die Vorgabe-Suche von Weg 0 hängt also an genau dem Einrichtungsschritt, den der openDesk-Bootstrap-Job geht und den diese Messumgebung nicht hat. Für OD-04 ist das eine Zeile, die man nicht raten will: wer die Vorgabe nimmt, bekommt ohne registrierte Ablage eine leere Liste **ohne Fehlermeldung**.

Dass der Parameter S3 nicht entwertet, steht im Bericht mit Begründung: beide Läufe tragen ihn gleich, der Unterschied zwischen 0 und 1 Treffer ist ausschließlich der zwischen den Konten, und die 14 gleichen Treffer der `Demo`-Kontrolle zeigen, dass er auch für `alice` Daten durchlässt.

## Die Kette von Weg 0, in einem Satz und mit beiden Gliedern

S3 liest sich sonst wie eine Aussage über OpenProject allein. Sie ist keine: auf Weg 0 entscheidet **erst Nextcloud**, wer der Nutzer ist (AppAPI-Impersonation, belegt durch die 401/997 der 64-Nullen-Gegenprobe), und **danach OpenProject**, was er sehen darf (belegt durch den Unterschied zwischen den zwei Konten bei identischem Aufruf). Fällt das erste Glied, kommt die Anfrage gar nicht an, und die leere Antwort hätte nichts mit Berechtigungen zu tun. Genau deshalb tragen beide Glieder eine eigene Gegenprobe.

## Was Abschnitt 3 liefert und was er ausdrücklich nicht tut

**Die Zahl, die dieser Abschnitt festhält, ist nicht 4746, sondern 3895 von 4490.** Der Aufwand einer Weg-0-Antwort liegt zu 87 Prozent im HAL-Relationenblock und nicht in den Daten, die ein Werkzeug zeigen würde.

**Und die Bytezahl ist keine Budgetgröße.** Die Kontrollmessung unter `alice` liefert 2542 statt 4746 Bytes, bei praktisch gleichen Feldkosten (588 gegen 585 Bytes) und fast halbierten Relationen (27 gegen 49). Beide Ursachen sind sichtbar: `bob` ist im eigenen Projekt schreibberechtigt und bekommt 23 Schreibrelationen mitgeliefert, und sein Projekt hat Module aktiv, die `storyPoints` und `sprint` erst erzeugen. Eine Bytezahl je Arbeitspaket hat damit zwei Abhängigkeiten, Berechtigung und Modulsatz, und wer daraus ein Token-Budget rechnet, rechnet mit dem günstigsten Fall.

**Zwei gemessene Befunde zur Bezugsgröße, die kein Zitat ersetzt:**

1. `select` wirkt an der **Sammlung** und nicht an der Einzelressource. An `/api/v3/work_packages/38` ändert der Parameter kein einziges Byte (8115 gegen 8115), an `/api/v3/work_packages` schrumpft dieselbe Auskunft von **15831 auf 88 Bytes**.
2. Die zulässigen Auswahlen zählt der Server im Fehlertext selbst auf. `updatedAt` ist nicht darunter und liefert **400** mit `urn:openproject-org:api:v3:errors:InvalidSignal`, also keine stille Teilantwort.

Die Werte aus der Recherche (`community.openproject.org`: roh 3691, mit `select` 216 Bytes) stehen als Kontext und als Größenordnung da, nicht als eigener Messwert.

**Die Zeile, die für Weg 0 zählt:** die OCS-Fläche hat **kein** `select`. Die Methode nimmt gemessen `searchQuery`, `fileId` und `isSmartPicker` und sonst nichts. Wer über Weg 0 liest, kann die 4746 Bytes nicht am Server kleiner machen; wer über die API v3 liest, kann es. Der Schlusssatz des Abschnitts sagt deshalb: die Diät macht der **Server** über `select` und nicht eine Projektion in unserem Code, denn eine Projektion bei uns spart Ausgabe an das Sprachmodell, aber kein Byte auf der Leitung und keine Arbeit in OpenProject.

**Keine Entscheidung, und der Bericht sagt das als Satz.** Ob ein künftiges Werkzeug über Weg 0 oder Weg 1 liest, welche Felder es projiziert und wie es mit den drei Lücken umgeht, entscheidet OD-04 nach dem Urteil aus 2.4, und 2.4 gehört 17-09.

## Deviations from Plan

**1. [Rule 2 - Ein ungeplanter Lauf beantwortet den einzigen Einwand gegen die Methode] Der natürlich verstrichene Ablauf an `alice`**
- **Gefunden bei:** Task 3, beim Nachprüfen der S6-Zahlen am Folgetag
- **Problem:** S4 stand ausschließlich auf einem gestellten Ablauf. Der Wert `0` ist zugleich der Vorgabewert der lesenden Methode, und damit blieb die Frage offen, ob ein von Hand gesetzter Zustandswert dasselbe auslöst wie eine wirklich verstrichene Frist. Beim Nachprüfen zeigte sich, dass der Ablauf von `alice` seit 17-05 von selbst verstrichen war und der Aufruf trotzdem 200 lieferte. Das als Nebenbeobachtung liegen zu lassen, hätte den einzigen angreifbaren Punkt von S4 angreifbar gelassen.
- **Fix:** Die drei Zahlen gelesen und als eigener Nachtrag in 2.1 geschrieben (`1787949009` vor dem Aufruf, `now 1787968632`, Differenz `-19623`, danach `1787975808`, also `+7176`), dazu Rohwerte als 5.5.4 und eine ergänzte S4-Zeile in der Behauptungstabelle. An `alice` ist dabei kein `occ user:setting` gefahren worden, weder vorher noch nachher.
- **Dateien:** `docs/spike-opendesk.md`
- **Commit:** 4720a00

**2. [Rule 2 - Eine Buchhaltung, die ein Wiederholungslauf falsch lesen würde] Der geänderte Wert von `alice` benannt**
- **Gefunden bei:** Task 3, unmittelbar nach Abweichung 1
- **Problem:** Zeile 12 von 5.5.2 protokolliert `alice` mit `token_expires_at 1787949009` als unberührt. Nach dem Nachtrag trägt das Konto `1787975808`. Wer den Bericht liest und den Wert nachprüft, findet eine andere Zahl und hält entweder den Bericht oder die Umgebung für kaputt.
- **Fix:** Ein Absatz sagt ausdrücklich, dass Zeile 12 für ihren Zeitpunkt richtig bleibt und nicht geändert wird, dass der heutige Wert der aus 5.5.4 ist, und dass die Aussage dahinter (Verbindung unversehrt) nach dem Nachtrag sogar belegter ist als vorher, weil sie gerade eine Erneuerung durchlaufen hat.
- **Dateien:** `docs/spike-opendesk.md`
- **Commit:** 4720a00

**3. [Rule 2 - Der Plan verlangt eine Byte-Messung, eine einzelne wäre irreführend] Zweite Antwort unter einem anderen Konto**
- **Gefunden bei:** Task 3
- **Problem:** Der Plan verlangt die Byte-Kosten einer Antwort. Eine einzelne Zahl in einem Bericht wird zur Budgetgröße, sobald jemand sie liest, und OD-04 ist genau der Leser, der daraus rechnen würde.
- **Fix:** Dieselbe Fläche unter `alice` gegen ein anderes Arbeitspaket gemessen: 2542 statt 4746 Bytes, 27 statt 49 Relationen, bei praktisch gleichen Feldkosten. Beide Ursachen (Schreibberechtigung, Modulsatz) sind im Bericht benannt, samt der Liste der Relationen, die nur je einer Seite gehören.
- **Dateien:** `docs/spike-opendesk.md`
- **Commit:** 4720a00

**4. [Rule 2 - Der Bericht würde sonst eine offene Stelle verschweigen] DI-17-04 angelegt**
- **Gefunden bei:** Task 3, beim Schreiben von 3.3
- **Problem:** Abschnitt 3.3 kommt zu dem Ergebnis, dass `GET /api/v1/work-packages/{id}/file-links` die einzige Route der Fläche ist, die eine Id annimmt, und zugleich das Unterscheidungsmerkmal aus `research/FEATURES.md`. Gemessen ist an ihr nichts, weil die Instanz keine registrierte Ablage hat. Damit stützt sich der Vergleich in 17-09 für Weg 0 auf eine Fläche, deren wertvollste Route unerprobt ist, und dieser Umstand hätte nur im Fließtext eines Abschnitts gestanden.
- **Fix:** DI-17-04 mit dem gemessenen Grund (`GET /api/v3/storages` `total 0`), der Abhängigkeit von DI-17-03 (ohne Weg A keine Ablage, ohne Ablage kein `file-links`), der ausdrücklichen Liste des Ungemessenen und einer vorgeschlagenen Behandlung für 17-08 und 17-09.
- **Dateien:** `.planning/phases/17-opendesk-spike/deferred-items.md`
- **Commit:** 4a686c0

**5. [Rule 1 - Verfrühter Statuswechsel, wie in 17-01 bis 17-05] OD-02 bleibt Pending**
- **Gefunden bei:** Zustandsaktualisierung
- **Problem:** Die Frontmatter nennt `requirements: [OD-02]`, und `requirements mark-complete` hätte OD-02 abgehakt. OD-02 verlangt Weg 0 und Weg 1 mit Messwerten nebeneinander; von Weg 0 fehlt nach diesem Plan noch S5, und der Vergleich selbst ist 17-09.
- **Fix:** OD-02 bleibt `Pending` und wird von 17-09 abgehakt.
- **Dateien:** keine
- **Commit:** derselbe wie dieses SUMMARY

**6. [Bekannte Gate-Eigenheit, nicht behoben, hier benannt] `grep -v '^#'` entfernt jede Ueberschrift**
- **Gefunden bei:** allen drei Tasks, beim Lauf der Gates
- **Problem:** Dieselbe Eigenheit, die 17-03 (Abweichung 7), 17-04 (9) und 17-05 (11) gemeldet haben. Zusätzlich enthält das Gate von Task 3 ein `grep -c '^## 3\.'`, dessen Ergebnis (1) durch den Filter der vorangehenden Griffe nie sichtbar würde.
- **Fix:** Nicht umgeschrieben. Beide Prüfungen gefahren und beide grün: die gefilterten Griffe für die inhaltlichen Zeichenketten (`Bytes`, `file-links`, `3691`, `searchQuery=SPIKE-OD-8471`, `S3`, `alice`, `bob`, `token_expires_at`, `refresh_token`, `1764`), ungefiltert `grep -q "### 2.1"` und `grep -c '^## 3\.'` mit Ergebnis 1.
- **Dateien:** keine
- **Commit:** keiner

**7. [Bekannter Vorbefund, nicht von diesem Plan, hier eingeordnet] Zwei Treffer im Geheimnis-Gate über den ganzen Baum**
- **Gefunden bei:** Geheimnis-Gate vor dem Commit von Task 3
- **Problem:** `git grep -F` über die Werte aus `.env.spike-opendesk` findet für `NC_MCP_TEST_PASSWORD` und `NC_MCP_TEST_PASSWORD2` Treffer in `scripts/bootstrap_exapp.sh`, `scripts/bootstrap_spike_opendesk.sh`, `scripts/bootstrap_test_nc.sh` und `tests/unit/test_staging_env_setup.py`.
- **Fix:** Nachgesehen statt abgehakt. Es sind die Vorgabewerte der Bootstrap-Skripte selbst (`ALICE_PASSWORD="${NC_SPIKE_OD_ALICE_PASSWORD:-alice-test-pw-01}"`, aus Commit 712a4ef in 17-02), also Platzhalter für Wegwerfkonten einer lokalen Messumgebung, die zufällig auch in der ortsgebundenen Verbindungsdatei stehen. Kein Wert dieses Plans und kein Geheimnis im Sinne von T-17-01. Ueber `docs/spike-opendesk.md` allein ist das Gate für alle 16 geprüften Werte ohne Treffer. Außerhalb des Auftrags dieses Plans, deshalb nicht geändert.
- **Dateien:** keine
- **Commit:** keiner

Sonst keine. Insbesondere ist keine der vier schreibenden und auch nicht die freiwillig ausgeschlossene Formularroute ausgelöst worden, kein `client_credentials`-Lauf gefahren, und der Aufbauzugang des Kontos `admin` kommt in keinem Messwert von S3 oder S4 vor.

## Authentication Gates

**Keiner.** Alle drei Tasks liefen autonom. Die Zugangsdaten lagen vollständig aus 17-02 bis 17-05 in der git-ignorierten Verbindungsdatei vor; gebraucht wurden `APP_SECRET`, `APP_ID` und `APP_VERSION` für die Impersonation sowie `OP_API_TOKEN` für die Bezugsgrößenmessung. Kein Wert ist gedruckt worden, weder in einem Protokoll noch in einer verfolgten Datei noch in diesem SUMMARY.

Ein Owner-Schritt wäre nur nötig gewesen, wenn der Ungemessen-Fallback von Task 1 gegriffen hätte (`bob` findet nichts). Er hat nicht gegriffen, nachdem die Ursache der leeren Vorgabe-Suche gemessen war.

## Verification

- Task-1-Gate: `searchQuery=SPIKE-OD-8471`, `S3`, `alice` und `bob` im Bericht gefunden.
- Task-2-Gate: `token_expires_at`, `refresh_token` und `1764` gefunden; `occ user:setting alice integration_openproject token_expires_at` liefert einen Wert (heute `1787975808`, siehe Abweichung 2).
- Task-3-Gate: `Bytes`, `file-links` und `3691` gefunden; `grep -c '^## 3\.'` ergibt 1.
- `artifacts`-Eintrag: `contains: "S4"` grün; zusätzlich ungefiltert `grep -q "### 2.1"` grün (siehe Abweichung 6). `key_links`-Muster `token_expires_at` steht in 2.1 sowie in 5.5.2 und 5.5.4.
- **Die sechs Bezugsgrößen sind vor dem Commit erneut gefahren und reproduzieren Byte für Byte:** 8115, 8115, 15831, 88, 361 und 400/310 mit `urn:openproject-org:api:v3:errors:InvalidSignal`. Die `alice`-Gegenprobe von S6 ebenso: 200, 2542 Bytes, 27 Relationen (1772 Bytes), 22 Felder (588 Bytes), `id 12`.
- Geheimnis-Gate: `git grep -F` über die Werte von 16 Schlüsseln aus `.env.spike-opendesk`; über `docs/spike-opendesk.md` kein Treffer, über den ganzen Baum zwei bekannte Vorbefunde (Abweichung 7). Muster-Gate über den Bericht (`AUTHORIZATION-APP-API`-Wert, JWT-Muster, `apikey:` mit Wert): ohne Treffer.
- Pitfall-2-Griff über den Bericht: **11** Treffer, alle geprüft. Vier zu `client_credentials` an den zwei aus 17-04 bekannten Stellen, sieben zu `apikey:` und alle sieben in der Schreibweise `apikey:<OP_API_TOKEN>` mit Platzhalter, jeder in einem Absatz, der den Aufbauzugang als solchen kennzeichnet. Die drei neuen Treffer dieses Plans stehen in 3.2, 5.5.3 und 5.5.4.
- `uv run pytest -q` mit `env -u APP_ID -u APP_SECRET -u APP_VERSION`: Rücknahmewert **0**, dreimal gefahren (nach dem Nachtrag, vor dem Commit von Task 3, nach DI-17-04). Das Vokabular-Gate hängt an ganz `docs/` und ist damit mitgelaufen.
- Vokabular außerdem einzeln geprüft: das verbotene Wort kommt in `docs/spike-opendesk.md` und in `deferred-items.md` **null**mal vor. Kein U+2014 und kein U+2013, kein Zeichen oberhalb U+2600, keine ASCII-Ersatzschreibung von Umlauten, 0 CRLF in beiden Dateien und 0 CRLF im Index.
- **Produktionsbaum unverändert (D-12):** `git status --short src/ appinfo/ pyproject.toml uv.lock` ist leer, nach jedem der vier Commits geprüft. `files_modified` des Plans nennt keinen Pfad unter `src/`. Werkzeugoberfläche und Budget-Gate sind nicht angefasst; `OpenProjectAPIController.php` und `OpenProjectAPIService.php` liegen im Container und nicht in diesem Baum und wurden ausschließlich gelesen.
- **Arbeitspaket 38 unverändert**, nach der letzten Messung geprüft: `subject SPIKE-OD-8471 privat`, **`lockVersion 0`**, `createdAt` und `updatedAt` beide `2026-08-28T17:17:55.534Z` und damit identisch, Projekt `Spike Privat B`. Die Aktivitätenliste trägt `total 1`, das ist der Anlagevorgang selbst. Keine der vier schreibenden Routen und nicht die Formularroute ist aufgerufen worden.
- Keiner der vier Commits löscht eine verfolgte Datei; `git status --short` ist nach dem letzten leer, keine unverfolgte Datei bleibt liegen.
- Loopback: jeder Aufruf ging an `127.0.0.1:8091` oder an `op.localtest.me:8082` (löst auf `127.0.0.1` auf), alle mit `curl -4`. Kein Aufruf an eine fremde Adresse, nichts an einen Dritten gesendet, keine gemietete Infrastruktur, kein `wsl --shutdown`, keine `.wslconfig`. Die zwei Container fremder Projekte (`findling-nextcloud`, `nc-mcp-test`) laufen unverändert weiter, die sechs Container der Messumgebung sind alle gepinnt.
- Zwischendateien der Messung liegen im Temporärverzeichnis und **nicht** im Repository (D-12).

## Known Stubs

Beabsichtigt und im Bericht gekennzeichnet: 2.4 und 2.5 (17-09), 4 (17-08), "Was diese Messung nicht beweist" (17-09), sowie in 2.1 die Zeilen S5a/b/c (17-07). Die Kopfzeilen `user_oidc` und Keycloak bleiben `noch nicht gemessen (Plan 17-07)`.

Abschnitt 3 ist mit diesem Plan **kein** Stub mehr, trägt aber ausdrücklich die Kennzeichnung "teilweise gemessen": die Byte- und Feldzahlen sind gemessen, `file-links`, `statuses`, `types` und `projects` sind es nicht, jeweils mit Grund.

Kein Stub verhindert das Ziel dieses Plans. Von Weg 0 fehlt nur noch S5, und das ist 17-07 mit einem verbundenen Konto als Ausgangszustand.

## Threat Flags

Keine neue Fläche über das Bedrohungsmodell des Plans hinaus. Fünf Anmerkungen zu Einträgen daraus:

- **T-17-01 (Information Disclosure), gehalten:** kein Token, kein Client-Secret, kein Passwort und kein `AUTHORIZATION-APP-API`-Wert steht in einer verfolgten Datei, in einem Protokoll oder in diesem SUMMARY. `token` und `refresh_token` erscheinen ausschließlich als Länge (43) und Vier-Zeichen-Präfix. Von den Antwortkörpern stehen Feldnamen, Relationennamen, Bytezahlen und Statuscodes im Bericht; der einzige übernommene Freitext ist `SPIKE-OD-8471 privat` und `Upload presentations to website`, beides Aufbaudaten. Die Protokollzeile mit `invalid_grant` ist vor der Uebernahme gegen jeden Wert der Verbindungsdatei geprüft worden.
- **T-17-05 (Repudiation), gehalten und über den Plan hinaus:** jeder Messwert trägt seine Gegenprobe, S3 sogar drei. Für S4 ist eine zweite Art von Gegenprobe dazugekommen, die nicht den Messwert, sondern den **Messweg** prüft (Abweichung 1).
- **T-17-03 (Elevation of Privilege), gehalten:** beide Läufe von S3 unter reiner AppAPI-Impersonation mit benanntem Nutzer, kein Dienstkonto, kein App-Passwort im Prozess. Der Aufbauzugang des Kontos `admin` ist ausschließlich für Größenvergleiche benutzt und an jeder der sieben Stellen als solcher gekennzeichnet.
- **T-17-02 (Tampering), wie geplant akzeptiert und eingetreten:** die Weg-0-Verbindung von `bob` ist nach der Gegenprobe absichtlich kaputt (`refresh_token` 43 Nullen, `token_expires_at` 0). Der Zustand verschwindet mit dem Nextcloud-Band beim `down -v`. `alice` ist unberührt und für 17-07 verfügbar.
- **T-17-04 (Tampering), gehalten:** geschrieben sind ausschließlich `docs/spike-opendesk.md` und `deferred-items.md`.

Ein Punkt, der **kein** Threat Flag ist, aber in 17-09 in den Begründungssatz gehört: die für OD-04 wertvollste Route der Weg-0-Fläche ist die einzige unerprobte (DI-17-04).

## Hinweise für die Folgepläne

1. **Für 17-07 (OIDC) ist `alice` das Konto.** Sie trägt `token_expires_at 1787975808` und hat gerade eine serverseitige Erneuerung durchlaufen; `bob` ist absichtlich kaputt. Die Warnung aus 17-05 gilt unverändert: ein Wechsel von `oauth2` auf `oidc` löst nach `ConfigController` einen Reset des jeweils anderen Zweigs aus, also erst lesen, dann schalten.
2. **S5 ist gegen die gemessene erste Hälfte zu lesen.** `OpenProjectAPIService.php:1764-1765` sagt im Kommentar der Upstream-Entwickler selbst, dass nur im `oauth2`-Modus erneuert wird. S4 belegt diese Hälfte jetzt gemessen; wenn S5 dasselbe Ergebnis liefert wie S4, ist entweder der Modus nicht wirklich `oidc` oder die Messung greift daneben.
3. **Die geglückte Erneuerung ist im Protokoll stumm, die gescheiterte laut.** Null Zeilen im Zeitfenster des Hauptlaufs, zwei in dem der Gegenprobe. Wer S5 nur am Log prüft, hält einen geglückten Lauf für einen Nichtlauf. Die Zustandswerte sind die Messung, das Log der Zusatzbeleg.
4. **`isSmartPicker=true` ist ohne registrierte Ablage Pflicht**, sonst antwortet die Suche für jedes Konto mit einer leeren Liste und ohne Fehlermeldung. Das kostet einen halben Tag, wenn man es nicht weiß.
5. **Für 17-08 zwei Fragen mit Grund:** liefert der openDesk-Bootstrap die Nextcloud-Ablage in OpenProject fertig eingerichtet aus (davon hängt ab, ob die Vorgabe-Suche und `file-links` dort überhaupt je leer sind), und rechnet ZenDiS mit dem Byte-Aufwand einer Fläche ohne `select`, die zu 87 Prozent Relationen ausliefert.
6. **Für 17-09:** 2.4 kann entscheiden, sobald 17-07 seine Zeilen trägt. Abschnitt 3 liegt als Zahlenbasis vor und greift der Entscheidung ausdrücklich nicht vor. In den Begründungssatz gehören zwei benannte offene Stellen: DI-17-03 (Weg A ungemessen) und DI-17-04 (`file-links` ungemessen), und die zweite hängt an der ersten.
7. **Die drei Exporte vor jedem compose-Kommando gelten weiter** (`set -a && . ./.env.spike-opendesk && set +a`), `pytest` braucht weiter `env -u APP_ID -u APP_SECRET -u APP_VERSION`, `curl -4` bleibt Pflicht wegen der AAAA-Falle von `localtest.me`, und das Vokabular-Gate hängt an ganz `docs/`.

## Self-Check: PASSED

Die zwei genannten Dateien existieren (`docs/spike-opendesk.md`, `.planning/phases/17-opendesk-spike/deferred-items.md`), und alle vier Commit-Kennungen (d6190b4, 71dd607, 4720a00, 4a686c0) sind im Repository auffindbar. `git status --short src/ appinfo/ pyproject.toml uv.lock` ist leer, `uv run pytest -q` gibt 0 zurück, Arbeitspaket 38 trägt `lockVersion 0` mit identischem `createdAt` und `updatedAt`, und kein Wert aus `.env.spike-opendesk` steht in `docs/spike-opendesk.md`. Keine Behauptung dieses SUMMARY steht ohne den Messwert, aus dem sie kommt; wo eine Messung fehlt (`file-links`, `statuses`, `types`, `projects`, Weg A, das Verhalten im Modus `oidc`), sagt der Text das mit dem Wort `ungemessen` samt Grund und nicht als Vermutung.
