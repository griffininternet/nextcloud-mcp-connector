---
phase: 17-opendesk-spike
plan: 04
subsystem: auth-measurement
tags: [spike, opendesk, od-02, oauth, pkce, weg-1, zwei-konten, d-04, d-05]
requires:
  - "17-03: OpenProject 17.7.2 laufend hinter Caddy auf 127.0.0.1:8082, Konten opa (id 5) und opb (id 6), privates Projekt spike-privat-b (id 3), Arbeitspaket 38, OAuth-Anwendung nc-mcp-spike-weg1 als nicht vertraulicher Client"
  - "17-01: docs/spike-opendesk.md mit Abschnittsgerüst und Entscheidungskriterien"
provides:
  - "Abschnitt 2.2 des Berichts vollständig: vier Messwerte mit je einer Gegenprobe, Weg 1 ist gemessen und nicht argumentiert"
  - "PKCE gemessen: 200 mit code_challenge, 400 an /oauth/authorize ohne code_challenge, Text 'Code challenge is required.'"
  - "expires_in gemessen: 7200 Sekunden, gleich der Erwartung aus access_token_expires_in 2.hours"
  - "Erneuerung ohne jeden Cookie-Speicher gemessen: 200, neues access_token und neues refresh_token, login opb aus dem neuen Token"
  - "Zwei-Konten-Negativbeweis auf Weg 1 (D-05): opb 200, opa 404 mit urn:openproject-org:api:v3:errors:NotFound, erfundene Id 999999999 dieselbe Antwort Byte für Byte"
  - "Der vollständige Consent-Fluss ist per Formular automatisiert, ohne Browser und ohne Owner-Schritt: /login, /oauth/authorize GET, /oauth/authorize POST, /oauth/token"
  - "DI-17-02 in deferred-items.md: der vorherige refresh_token stirbt erst mit dem ersten Gebrauch des neuen access_token"
  - "Frage 9 in Abschnitt 4 vorgemerkt: fehlendes code_challenge_methods_supported als Metadatenmangel"
affects:
  - "17-06 führt denselben Zwei-Konten-Negativbeweis auf Weg 0; die Form der Tabelle und die Sprache aus docs/spike-dav.md ('404, never 200') stehen hier als Vorlage"
  - "17-08 bekommt aus Abschnitt 2.2 zwei Fragen mit Grund: die Metadatenlücke (Frage 9, schon vorgemerkt) und den Keycloak-Umleitungsschritt, den der lokale Aufbau nicht reproduziert"
  - "17-09 kann 2.4 entscheiden, sobald Weg 0 gemessen ist; Weg 1 steht mit allen vier von D-04 verlangten Werten bereit und ist nicht mehr die Unbekannte des Vergleichs"
  - "OD-04 (v2.0) bekommt aus DI-17-02 eine Vorgabe für die Erneuerungslogik und aus 2.2 die Kostenrechnung von Weg 1"
tech-stack:
  added: []
  patterns:
    - "Die Gegenprobe zuerst planen und dann den Hauptlauf: bei einer Pflicht (force_pkce) ist der Lauf OHNE das Pflichtmerkmal der eigentliche Befund, der Hauptlauf allein beweist nichts"
    - "Fällt eine Gegenprobe anders aus als erwartet, ist das der Befund und nicht ein Fehlschlag der Messung. Den Mechanismus dann mit zwei Ketten trennen, die sich in genau einem Schritt unterscheiden und unmittelbar hintereinander laufen, damit verstrichene Zeit als Erklärung ausfällt"
    - "Dieselbe Berechtigungsgrenze auf drei Ebenen messen (Einzelressource, Container, Liste), weil eine Einzelabfrage eine Ausnahme sein kann und ein Listenleck sonst unsichtbar bleibt"
    - "Zwei 404 nicht nur nach Status vergleichen, sondern Byte für Byte samt Prüfsumme: 'verrät die Existenz nicht' ist eine Aussage über den Körper und nicht über den Code"
    - "Nach der letzten Messung jeden entstandenen Tokenwert widerrufen und den Widerruf gegenproben (401), statt sich auf die Ablaufzeit zu verlassen"
key-files:
  created: []
  modified:
    - "docs/spike-opendesk.md"
    - ".planning/phases/17-opendesk-spike/deferred-items.md"
decisions:
  - "Der Browser-Rückfall aus dem Plan wurde nicht gebraucht: der Formularweg über /login und /oauth/authorize trug im ersten Versuch, für beide Konten. Damit ist D-04 ohne einen einzigen Owner-Schritt erfüllt"
  - "Die unerwartete 200 beim Wiedergebrauch des verbrauchten refresh_token ist als Befund geschrieben und nicht als bestandene Gegenprobe abgehakt; der Auslöser der Entwertung ist mit einem Zwei-Ketten-Versuch nachgemessen"
  - "Über den fremden Doorkeeper-Code behauptet der Bericht nur, dass die Spalte previous_refresh_token existiert (Belegstelle in der laufenden Instanz). Die Verknüpfung mit dem Verhalten ist die Messung und keine Lesart des Quelltexts"
  - "OD-02 bleibt Pending: dieser Plan misst Weg 1 vollständig, aber Weg 0 nicht, und OD-02 verlangt beide nebeneinander. Fortsetzung der Entscheidung aus 17-01, 17-02 und 17-03"
  - "Der Fund zur aufgeschobenen Entwertung wandert als DI-17-02 in deferred-items.md und nicht als Aufgabe in diesen Plan, weil er OD-04 betrifft und D-12 hier keinen Code zulässt"
metrics:
  duration: 41 min
  completed: 2026-08-28
---

# Phase 17 Plan 04: Weg 1 vollständig gemessen Summary

Weg 1 ist gemessen und nicht mehr argumentiert: der volle Consent-Fluss lief automatisiert per Formular für beide Konten durch, PKCE ist mit seiner Gegenprobe als Pflicht belegt, `expires_in` steht als gemessene 7200 Sekunden im Bericht, die Erneuerung trägt ohne jeden Cookie-Speicher, und der Zwei-Konten-Negativbeweis liefert eine 404, die von der auf eine nicht existierende Id Byte für Byte nicht zu unterscheiden ist.

## Die vier von D-04 verlangten Messwerte, alle vier gemessen

| Messwert | Erwartung aus der Quelle | Gemessener Wert | Gegenprobe |
|----------|--------------------------|-----------------|------------|
| Nimmt `/oauth/authorize` PKCE an | 200 und ein Token (`force_pkce`, `doorkeeper.rb:90`) | **ja**: Zustimmungsseite 200, 302 mit `code` (43 Zeichen), Token-Endpunkt 200 | **derselbe Client ohne `code_challenge`: 400** an `/oauth/authorize`, wörtlich "Code challenge is required.", kein Code, keine Zustimmungsseite |
| `expires_in` | 7200 (`access_token_expires_in 2.hours`) | **7200 Sekunden** | Code, Admin-Dokumentation und Messwert nennen denselben Wert; `custom_access_token_expires_in` ist nicht gesetzt |
| Erneuerung ohne Browsersitzung | neues Paar (`use_refresh_token`, `doorkeeper.rb:115`) | **200**, neues `access_token` und neues `refresh_token`, `expires_in` wieder 7200, `login opb` aus dem neuen Token. **Ohne `-b` und ohne `-c`, also ohne jeden Cookie-Speicher** | erfundener Wert 400 `invalid_grant`, entwerteter Wert 400 `invalid_grant`, altes `access_token` sofort 401 |
| Zwei-Konten-Negativbeweis (D-05) | 404 mit `urn:openproject-org:api:v3:errors:NotFound`, nicht 403 | **`opa` 404**, `opb` 200 | `opb` 200 mit `subject` `SPIKE-OD-8471 privat`; erfundene Id 999999999 antwortet Byte für Byte identisch (166 Bytes, gleicher SHA-256) |

Kein Aufruf dieses Plans benutzte den API-Schlüssel des Kontos `admin`, mit dem der Grundzustand aus 5.3 entstanden ist, und jede Zeile des Berichts nennt das Konto, unter dem sie lief.

## Der Consent-Fluss brauchte keinen Owner-Schritt

Der Plan sah einen Browser-Rückfall vor, bei dem der Owner die Zustimmungsseite selbst aufruft und den Code in die Verbindungsdatei legt. Er wurde **nicht** gebraucht: der Formularweg trug im ersten Versuch, und zwar für beide Konten.

| Schritt | Status | Was belegt ist |
|---------|--------|----------------|
| `GET /login` | 200 | zwei Formulare, beide mit `authenticity_token` (86 Zeichen); genommen wurde das von `user-login--form` |
| `POST /login` | 302 | Ziel ist **nicht** `/my/page`, sondern `/two_factor_authentication/request`; die Kette endet nach zwei weiteren 302 auf `/my/page`, und die Seite nennt `Bob Spike` |
| `GET /oauth/authorize` mit PKCE | 200 | wörtlich `Authorize nc-mcp-spike-weg1 to use your account opb?` und `Full API v3 access`; das Formular trägt `code_challenge` als verstecktes Feld weiter |
| `POST /oauth/authorize` | 302 | `Location` trägt `code=` (43 Zeichen) und das gesendete `state` Zeichen für Zeichen zurück |

Auf Port 8099 hörte dabei nichts, und das musste es auch nicht: der Code wird aus dem `Location`-Kopf gelesen und nicht aus einer Zustellung (T-17-02).

## Der Befund, der anders ausfiel als die Erwartung

**Die zweite Gegenprobe zur Erneuerung ist zunächst durchgefallen, und das ist der wertvollste Teil dieses Plans.** Erwartet war, dass ein verbrauchter `refresh_token` fehlschlägt. Gemessen hat er beim ersten Wiedergebrauch **200** geliefert, mit einem zweiten vollständig gültigen Tokenpaar. Ein Bericht, der hier "Gegenprobe bestanden" geschrieben hätte, hätte die Instanz falsch beschrieben, und zwar in der Richtung, die für den Client aus OD-04 zählt.

Also ist der Mechanismus nachgemessen worden, mit zwei Ketten, die sich in genau einem Schritt unterscheiden und unmittelbar hintereinander im selben Lauf liefen, damit verstrichene Zeit als Erklärung ausfällt:

| Kette | Wird das **neue** `access_token` einmal benutzt | Alter `refresh_token` danach erneut |
|-------|------------------------------------------------|-------------------------------------|
| A | ja, `GET /api/v3/users/me` -> 200 | **400** `invalid_grant` |
| B | nein, gar nicht | **200**, ein weiteres vollständiges Paar |

**Der Auslöser der Entwertung ist damit gemessen: nicht die Erneuerung und nicht die Zeit, sondern der erste Gebrauch des neu ausgegebenen `access_token`.** Der passende Beleg aus der laufenden Instanz ist die Spalte `previous_refresh_token` auf `oauth_access_tokens` (`/app/db/structure.sql:4383`). Über den fremden Doorkeeper-Code behauptet der Bericht nur, dass diese Spalte existiert; die Verknüpfung mit dem Verhalten ist die Messung und keine Lesart des Quelltexts. Der Fund liegt als DI-17-02 in `deferred-items.md`, weil er OD-04 betrifft und D-12 hier keinen Code zulässt.

## Der Zwei-Konten-Negativbeweis, auf drei Ebenen statt auf einer

Der Plan verlangt drei Aufrufe. Gefahren sind sechs, weil eine Einzelressource allein eine Ausnahme sein könnte und ein Berechtigungsleck, das die Einzelabfrage abweist und die Liste nicht, sonst unsichtbar bliebe:

| Aufruf | `opb` (Mitglied) | `opa` (kein Mitglied) |
|--------|------------------|-----------------------|
| `GET /api/v3/work_packages/38` | 200, `subject SPIKE-OD-8471 privat`, `project Spike Privat B` | **404** `urn:openproject-org:api:v3:errors:NotFound` |
| `GET /api/v3/work_packages/999999999` | nicht gefahren | **404**, dieselbe Antwort Byte für Byte: je 166 Bytes, gleicher SHA-256, `cmp` meldet keinen Unterschied |
| `GET /api/v3/projects/3` | 200 | **404**, dieselbe Fehlerkennung |
| `GET /api/v3/projects/3/work_packages` | 200, `total 1`, Ids `[38]` | **404**, dieselbe Fehlerkennung |
| `GET /api/v3/work_packages?pageSize=100` | 200, `total 34`, enthält 38 | 200, `total 33`, enthält 38 **nicht** |

Die letzte Zeile ist die aussagekräftigste, weil sie nicht auf eine Id zielt: derselbe Endpunkt, dieselbe Seitengröße, genau ein Arbeitspaket Unterschied, und der Unterschied ist genau das private. Kein 403 an keiner Stelle, und kein Unterschied zwischen "gibt es nicht" und "darfst du nicht". Damit gilt für OpenProject-Arbeitspakete wörtlich, was `docs/spike-dav.md` für Nextcloud-Dateien belegt: "`404`, never `200`", und beides unter dem Konto selbst statt unter einem Dienstkonto.

Wer die Tokens tragen, ist aus den Tokens gemessen und nicht aus dem Skript geschlossen: `GET /api/v3/users/me` nennt `login opb`, `id 6` und `login opa`, `id 5`, beide ohne `admin`. Das sind genau die Ids aus Abschnitt 5.3.

## Deviations from Plan

**1. [Rule 2 - Der Verweis des Plans hätte ins Leere gezeigt] Frage 9 in Abschnitt 4 vorgemerkt**
- **Gefunden bei:** Task 1
- **Problem:** Der Plan verlangt in Task 1 einen Verweis auf "Frage 9 in Abschnitt 4" und führt denselben Verweis als `key_links`-Eintrag. Abschnitt 4 trägt aber bis Plan 17-08 nur die Zeile `noch nicht gemessen`. Ein Leser wäre auf eine Frage 9 verwiesen worden, die es nicht gibt, und 17-08 hätte den Nebenbefund nur über den Plantext gefunden.
- **Fix:** Ein kurzer, ausdrücklich als "vorgemerkt aus Abschnitt 2.2" gekennzeichneter Absatz in Abschnitt 4 nennt Frage 9 samt Grund. Die Formulierung der Liste bleibt 17-08 überlassen; die Zeile `noch nicht gemessen, Plan 17-08` bleibt unangetastet stehen.
- **Dateien:** `docs/spike-opendesk.md`
- **Commit:** 7e64252

**2. [Rule 1 - Anmeldeschritt des Plans endet nicht dort, wo der Plan es erwartet] Ein 2FA-Umweg zwischen `/login` und `/my/page`**
- **Gefunden bei:** Task 1
- **Problem:** Der Plan erwartet nach `POST /login` eine 302 auf `/my/page` oder die Startseite. Gemessen führt die 302 auf `/two_factor_authentication/request`, und `GET /api/v3/users/me` mit diesem Cookie-Speicher antwortete an dieser Stelle **401**. Wer hier abbricht, liest den Zustand als "Anmeldung gescheitert" und geht in den Browser-Rückfall, obwohl der Formularweg trägt.
- **Fix:** Der Weiterleitungskette gefolgt. Nach zwei weiteren 302 endet sie auf `/my/page`, die Seite nennt `Bob Spike`, und derselbe API-Aufruf antwortet danach 200. Für die Folgeläufe genügt `curl -L` auf dem `POST /login`. Der Bericht nennt den Umweg ausdrücklich als Messwert, damit ein Wiederholungslauf ihn nicht als Fehlschlag liest.
- **Dateien:** `docs/spike-opendesk.md`
- **Commit:** 7e64252

**3. [Rule 2 - Eine Gegenprobe, die anders ausfällt, verlangt eine eigene Messung] Zwei-Ketten-Versuch zum Zeitpunkt der Entwertung**
- **Gefunden bei:** Task 2
- **Problem:** Der verbrauchte `refresh_token` lieferte 200 statt eines Fehlschlags, beim dritten Gebrauch dann 400. Damit standen zwei Erklärungen im Raum, eine Zeitgrenze und ein anderer Auslöser. Der Plan sieht für diesen Fall vor, den Befund zu schreiben; ohne die Ursache wäre der Bericht aber bei "manchmal 200, manchmal 400" geblieben, und das ist kein Messwert.
- **Fix:** Zwei Ketten, unmittelbar hintereinander im selben Lauf, Unterschied nur im Gebrauch des neuen `access_token`. Ergebnis eindeutig (Tabelle oben). Zusätzlich die Belegstelle `previous_refresh_token` in `/app/db/structure.sql:4383` der laufenden Instanz geprüft. Der Bericht trägt Befund und Auslöser, DI-17-02 trägt die Folge für OD-04.
- **Dateien:** `docs/spike-opendesk.md`, `.planning/phases/17-opendesk-spike/deferred-items.md`
- **Commit:** 9071da6 und bfeae09

**4. [Rule 2 - Der Negativbeweis des Plans war einseitig prüfbar] Drei Aufrufe wurden sechs**
- **Gefunden bei:** Task 3
- **Problem:** Der Plan verlangt drei Aufrufe auf eine Einzelressource. Eine 404 auf ein einzelnes Arbeitspaket schließt ein Leck an einer anderen Stelle nicht aus: hätte die Listenabfrage das private Arbeitspaket ausgeliefert, wäre der Negativbeweis grün gewesen und die Grenze trotzdem undicht (dieselbe Mechanik wie Pitfall 3, "der Beweis ist leer und sieht grün aus").
- **Fix:** Dieselbe Grenze zwei Ebenen höher mitgemessen: Projekt 3 direkt, die projektbezogene Arbeitspaketliste und die globale Liste mit `pageSize=100`. Alle drei asymmetrisch, `total 34` gegen `total 33`, und der Unterschied ist genau das private Arbeitspaket. Die drei vom Plan verlangten Zeilen stehen unverändert als eigene Tabelle davor.
- **Dateien:** `docs/spike-opendesk.md`
- **Commit:** 861ee38

**5. [Rule 2 - Ein neues Zitat lässt das Pitfall-2-Gate unklar aussehen] `client_credentials` eingeordnet**
- **Gefunden bei:** Task 3, beim Lauf des Pitfall-2-Griffs
- **Problem:** Der Griff `git grep -i "client_credentials\|GLOBAL__BASIC__AUTH\|apikey:"` fand nach Task 1 einen neuen Treffer außerhalb des dafür vorgesehenen Absatzes: das wörtliche Zitat des Metadatendokuments trägt `"grant_types_supported":[...,"client_credentials",...]`. Nach der in 17-03 festgelegten Regel ist jeder Treffer außerhalb des erklärenden Absatzes ein Befund, und ein Gate mit unklaren Treffern wird beim nächsten Lauf übergangen statt gelesen.
- **Fix:** Ein Absatz direkt unter dem Zitat sagt, dass der Grant ein Zitat des Serverdokuments und keine Einladung ist, dass **kein** Aufruf dieses Abschnitts ihn benutzt hat, dass er ohne den Wert im Feld `Client Credentials User ID` auch nichts im Namen eines Menschen liefern könnte, und dass genau dieser Weg der Dienstkonto-Weg aus Pitfall 1 und T-17-03 wäre. Der Griff hat damit zwei erwartete Stellen, hier und in 5.3.
- **Dateien:** `docs/spike-opendesk.md`
- **Commit:** 861ee38

**6. [Rule 2 - T-17-01 verlangt mehr als "nicht aufschreiben"] Zwanzig Tokenwerte widerrufen und den Widerruf gegengeprobt**
- **Gefunden bei:** nach Task 3
- **Problem:** Die Messungen haben zehn Tokenpaare erzeugt, alle mit einer Lebensdauer von 7200 Sekunden, und DI-17-02 belegt, dass ein `refresh_token` nach dem Wiedergebrauch weitere Paare liefern kann. Der Plan verlangt nur, keinen Wert aufzuschreiben. Zurückbleibende gültige Tokens sind trotzdem Fläche, auch auf einer Loopback-Instanz.
- **Fix:** Jeder entstandene Wert per `POST /oauth/revoke` widerrufen, zwanzig Aufrufe, je Status 200. Gegenprobe: `GET /api/v3/users/me` mit dem Token von `opb` und mit dem von `opa` antwortet danach je 401. Cookie-Speicher, Verifier und Zwischendateien lagen unter dem Temporärverzeichnis und sind gelöscht. Der Absatz steht im Bericht, weil ein Prüfer nach genau diesem Aufräumschritt fragt.
- **Dateien:** `docs/spike-opendesk.md`
- **Commit:** 861ee38

**7. [Rule 1 - Regelverstoß beim Schreiben, vor dem Commit behoben] ASCII-Ersatzschreibung von Umlauten**
- **Gefunden bei:** Task 1, beim ersten Entwurf des Abschnitts
- **Problem:** Der erste Entwurf schrieb `ausschliesslich`, `Laenge`, `Praefix`, `Haekchen` und rund zwanzig weitere Wörter in ASCII-Ersatzschreibung. Das verstößt gegen die Projektregel und gegen die Form der Abschnitte 1 und 5, die 17-01 bis 17-03 mit echten Umlauten geschrieben haben.
- **Fix:** Vor dem ersten Commit berichtigt und danach nach jedem Schreibschritt ein Griff nach `ae|oe|ue|ss` über den Abschnitt gefahren, dessen Restliste nur noch echte Wörter enthält (`Erneuerung`, `Quelle`, `neues`, englische Zitate). Kein Commit dieses Plans trägt eine Ersatzschreibung.
- **Dateien:** `docs/spike-opendesk.md`
- **Commit:** 7e64252 (berichtigt vor dem Commit)

**8. [Rule 1 - Verfrühter Statuswechsel, wie in 17-01 bis 17-03] OD-02 bleibt Pending**
- **Gefunden bei:** Zustandsaktualisierung
- **Problem:** Die Frontmatter nennt `requirements: [OD-02]`, und `requirements mark-complete` hätte OD-02 abgehakt. Der Wortlaut trägt das nicht: OD-02 verlangt Weg 0 **und** Weg 1 mit Messwerten nebeneinander. Dieser Plan misst Weg 1 vollständig und Weg 0 mit keinem einzigen Wert.
- **Fix:** OD-02 bleibt `Pending` und wird von 17-09 abgehakt. Das folgt den Entscheidungen aus 17-01, 17-02 und 17-03 und der Projektregel, Nachweise wörtlich zu nehmen.
- **Dateien:** keine
- **Commit:** derselbe wie dieses SUMMARY

**9. [Bekannte Gate-Eigenheit, nicht behoben, hier benannt] `grep -v '^#'` entfernt jede Überschrift**
- **Gefunden bei:** Task 3, beim Lauf der Gates
- **Problem:** Alle Gates dieses Plans beginnen mit `grep -v '^#'`, um Kommentarzeilen auszuschließen. Der Griff entfernt damit auch jede Markdown-Überschrift. Der `artifacts`-Eintrag der Frontmatter verlangt `contains: "### 2.2"`, und genau diese Zeichenkette findet der so gefilterte Griff nie. Dieselbe Eigenheit hat 17-03 als Abweichung 7 gemeldet.
- **Fix:** Nicht umgeschrieben, weil das Gate des Plans nicht Sache der Ausführung ist. Stattdessen beide Prüfungen gefahren und beide grün: der gefilterte Griff für die inhaltlichen Zeichenketten, ein ungefilterter `grep -q "### 2.2"` für die Überschrift. Ein Folgeplan, der dieselbe Zeile schreibt, sollte den Griff ohne `grep -v '^#'` fahren oder die Zeichenkette zusätzlich in den Fließtext nehmen.
- **Dateien:** keine
- **Commit:** keiner

Sonst keine. Insbesondere ist kein `client_credentials`-Lauf gefahren worden, obwohl der Grant in den Metadaten steht, und der API-Schlüssel des Kontos `admin` ist in keinem Messwert dieses Plans vorgekommen.

## Authentication Gates

**Keiner.** Der Plan sah einen möglichen Owner-Schritt vor (Browser-Rückfall für die Zustimmungsseite, Code in `.env.spike-opendesk` als `OP_AUTH_CODE`). Er war nicht nötig: der Formularweg über `/login` und `/oauth/authorize` trug im ersten Versuch, für `opb` und für `opa`. Die vier Werte aus 17-03 lagen vollständig in der git-ignorierten Verbindungsdatei; gebraucht wurden `OP_OAUTH_CLIENT_ID` (43 Zeichen), `OP_USER_A_PASSWORD` und `OP_USER_B_PASSWORD` (je 20 Zeichen) sowie `OP_WP_ID` (`38`). `OP_OAUTH_CLIENT_SECRET` wurde bewusst **nicht** benutzt, weil der Client öffentlich ist und ein Secret die gemessene Frage verändert hätte.

## Verification

- Task-1-Gate: `expires_in`, `code_challenge_method=S256` und `opb` im Bericht gefunden, Geheimnis-Griff ohne Treffer.
- Task-2-Gate: `ohne code_challenge`, `grant_type=refresh_token` und `kein Cookie` (unabhängig von Groß- und Kleinschreibung) gefunden.
- Task-3-Gate: `urn:openproject-org:api:v3:errors:NotFound`, `999999999`, `opa` und `OPENPROJECT_OMNIAUTH__DIRECT__LOGIN__PROVIDER` gefunden.
- `artifacts`-Eintrag: `grep -q "### 2.2"` ungefiltert grün (siehe Abweichung 9). `key_links`-Muster `code_challenge_methods_supported` steht in 2.2 und in Abschnitt 4.
- Geheimnis-Gate des Plans über `docs/spike-opendesk.md`: kein Treffer. `git grep` über den ganzen verfolgten Baum: nur die bekannten Stellen aus Plantexten, Vorgänger-SUMMARYs und der Paginierungs-Beispielzeile der READMEs, keine neue.
- Wertprüfung statt nur Musterprüfung: für alle sechs Werte aus `.env.spike-opendesk` (`OP_OAUTH_CLIENT_ID`, `OP_OAUTH_CLIENT_SECRET`, `OP_API_TOKEN`, `OP_ADMIN_PASSWORD`, `OP_USER_A_PASSWORD`, `OP_USER_B_PASSWORD`) sucht `git grep -F` nach dem Wert selbst. Kein Treffer.
- Pitfall-2-Griff über den Bericht: vier Treffer, alle erwartet und alle eingeordnet (das Metadatenzitat samt seinem Absatz in 2.2, der Absatz in 5.3).
- `uv run pytest -q` mit `env -u APP_ID -u APP_SECRET -u APP_VERSION`: grün, viermal gefahren (nach Task 1, nach Task 2, nach Task 3 und nach der Einordnung von `client_credentials`).
- Kein U+2014 und kein U+2013 in `docs/spike-opendesk.md`, kein Zeichen oberhalb U+2600, keine ASCII-Ersatzschreibung von Umlauten im neuen Abschnitt.
- `git status --short src/ appinfo/ pyproject.toml uv.lock`: leer, nach jedem der vier Commits geprüft. `files_modified` des Plans nennt keinen Pfad unter `src/` (D-12). Werkzeugoberfläche und Budget-Gate sind nicht angefasst.
- Zeilenenden: `docs/spike-opendesk.md` trägt in Arbeitskopie und Index 0 CRLF, der Diff der vier Commits ist ein reiner Zuwachs und keine Massenänderung.
- Keiner der vier Commits löscht eine verfolgte Datei, keine unverfolgte Datei bleibt liegen (`git status --short` leer).
- Aufräumen gegengeprobt: zwanzig `POST /oauth/revoke` je 200, danach beide Tokens 401. Das Temporärverzeichnis mit 63 Zwischendateien ist gelöscht.
- Loopback: alle Aufrufe gingen über `http://op.localtest.me:8082`, `curl -w '%{remote_ip}'` meldet `127.0.0.1`. Kein Aufruf an eine fremde Adresse, nichts an einen Dritten gesendet.

## Known Stubs

Beabsichtigt und im Bericht gekennzeichnet: die Abschnitte 2.1 (Plan 17-05 und 17-06), 2.4 und 2.5 (17-09), 3 (17-09), 4 (17-08) und "Was diese Messung nicht beweist" tragen weiter je eine Zeile `noch nicht gemessen` mit Planzuordnung. Die Kopfzeilen `integration_openproject` (17-05) sowie `user_oidc` und Keycloak (17-07) ebenso.

Ein Stub, der ausdrücklich einer bleibt: Abschnitt 4 trägt jetzt einen vorgemerkten Absatz zu Frage 9 (Abweichung 1), aber weiterhin die Zeile `noch nicht gemessen, Plan 17-08`. Die Liste selbst entsteht in 17-08 und ist hier nicht vorweggenommen.

Kein Stub verhindert das Ziel dieses Plans: Abschnitt 2.2 ist vollständig, alle vier von D-04 verlangten Messwerte tragen ihre Gegenprobe, und der Negativbeweis aus D-05 ist auf Weg 1 geführt.

## Threat Flags

Keine neue Fläche über das Bedrohungsmodell des Plans hinaus. Vier Anmerkungen zu Einträgen daraus:

- **T-17-01 (Information Disclosure), gehalten und über den Plan hinaus behandelt:** zehn Tokenpaare sind entstanden, kein Wert steht in einer verfolgten Datei, in einem Protokoll oder in diesem SUMMARY. Der Bericht nennt von ihnen nur Längen (43 Zeichen), Vier-Zeichen-Präfixe, `expires_in`, `created_at` und Statuscodes. Zusätzlich sind alle zwanzig Werte widerrufen und der Widerruf ist gegengeprobt (Abweichung 6).
- **T-17-03 (Elevation of Privilege), gehalten und im Bericht belegt:** kein `client_credentials`-Lauf, obwohl der Grant in den Metadaten der laufenden Instanz steht; der Ausschluss steht als eigener Absatz direkt unter dem Zitat (Abweichung 5). Jeder Messwert nennt sein Konto. Kein Aufruf benutzte den Admin-Schlüssel.
- **T-17-05 (Repudiation), gehalten:** jeder der vier Messwerte trägt seine Gegenprobe in derselben Tabellenzeile. Die eine Gegenprobe, die anders ausfiel, ist als Befund geschrieben und mit einer eigenen Messung aufgeklärt statt als bestanden abgehakt (Abweichung 3).
- **T-17-04 (Tampering), gehalten:** Verifier und Challenge kommen aus `pkce()` in `scripts/oauth_flow_check.py:160-164`, per Import aufgerufen. Keine Zeile dieser Datei und keine Zeile unter `src/` ist geändert.

Ein Punkt, der ausdrücklich **kein** Threat Flag dieser App ist, aber in OD-04 eine Entscheidung verlangt: die aufgeschobene Entwertung des `refresh_token` (DI-17-02). Sie ist eine Eigenschaft von OpenProject, nicht dieser ExApp, und diese Phase erzeugt keinen Client, der davon betroffen wäre.

## Hinweise für die Folgepläne

1. **Der Consent-Fluss von Weg 1 ist per Formular automatisierbar, ohne Browser und ohne Owner.** Die vier Schritte stehen im Bericht. Zwei Fallen darin: `POST /login` endet auf `/two_factor_authentication/request` und braucht `curl -L`, und die Anmeldeseite trägt **zwei** Formulare, brauchbar ist der `authenticity_token` von `user-login--form`. Auf der Zustimmungsseite ist es der des **ersten** Formulars; das zweite ist "Cancel and deny authorization".
2. **`curl -4` benutzen.** Der AAAA-Eintrag von `localtest.me` auf `::1` ist die Falle aus 17-03 und trifft auch Aufrufe vom Host. Mit `-4` meldet `%{remote_ip}` verlässlich `127.0.0.1`.
3. **Ein 415 an `/oauth/token` ist kein Befund über den Fluss, sondern über die Verpackung** (`enforce_content_type`, gemessen). Immer `curl -d`, nie `json=`.
4. **Für 17-06, den Zwei-Konten-Negativbeweis auf Weg 0:** die Form der Tabelle, die Byte-für-Byte-Gegenprobe mit der Id 999999999 und die drei Ebenen (Einzelressource, Projekt, Liste mit `pageSize=100`) stehen hier als Vorlage. Die Listenzeile ist die aussagekräftigste und die billigste.
5. **Arbeitspaket 38 ist unverändert.** Dieser Plan hat nur gelesen. `subject` ist weiter `SPIKE-OD-8471 privat`, Projekt `Spike Privat B` (id 3), Mitglied nur `opb`. Die Zählstände für einen Vergleich: global sieht `opb` `total 34`, `opa` `total 33`.
6. **Alle Tokens dieses Plans sind widerrufen.** Wer 17-06 oder 17-07 fährt, braucht ein neues; die vier Schritte kosten unter zehn Sekunden. Die OAuth-Anwendung `nc-mcp-spike-weg1` selbst ist nicht angefasst und weiter nutzbar.
7. **Die drei Exporte vor jedem compose-Kommando gelten weiter** (`set -a && . ./.env.spike-opendesk && set +a`), und `pytest` braucht weiter `env -u APP_ID -u APP_SECRET -u APP_VERSION`. Beides aus 17-02 und 17-03 unverändert.
8. **Für 17-08:** Frage 9 ist in Abschnitt 4 vorgemerkt und muss dort nur ausformuliert und eingeordnet werden. Zwei weitere Fragen mit Grund liegen im Abschluss von 2.2: der Keycloak-Umleitungsschritt und die Scope-Pflicht für ein OIDC-JWT, beide ausdrücklich als `ungemessen` markiert.

## Self-Check: PASSED

Die zwei in diesem SUMMARY genannten Dateien existieren (`docs/spike-opendesk.md`, `.planning/phases/17-opendesk-spike/deferred-items.md`), und alle vier Commit-Kennungen (7e64252, 9071da6, 861ee38, bfeae09) sind im Repository auffindbar. `git status --short src/ appinfo/ pyproject.toml uv.lock` ist leer, `uv run pytest -q` ist grün, und kein Wert aus `.env.spike-opendesk` steht im verfolgten Baum. Keine Behauptung dieses SUMMARY steht ohne den Messwert, aus dem sie kommt; wo eine Messung fehlt (der Keycloak-Umleitungsschritt, die Scope-Pflicht für ein OIDC-JWT, eine obere Zeitgrenze für den alten `refresh_token`, der Grund für den Sprachwechsel im `error_description`-Text), sagt der Text das mit dem Wort `ungemessen` und nicht als Vermutung.
