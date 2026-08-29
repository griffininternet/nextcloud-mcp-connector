---
phase: 17-opendesk-spike
plan: 07
subsystem: auth-measurement
tags: [spike, opendesk, od-02, weg-0, oidc, keycloak, user-oidc, s5, d-07, d-08, d-12]
requires:
  - "17-06: alice als verbundenes und frisch erneuertes Konto (token_expires_at 1787975808), bob absichtlich kaputt, S4 als gemessene erste Haelfte der oauth2-gegen-oidc-Asymmetrie"
  - "17-05: integration_openproject 3.1.1 im Modus oauth2, allow_local_remote_servers true, die Warnung, dass ein Moduswechsel ueber ConfigController den anderen Zweig zuruecksetzt"
  - "17-RESEARCH K5: die drei Ereignispfade, die Zeilennummern in TokenService.php, die Vorbedingung isLoggedIn() in allen drei Listenern"
provides:
  - "S5a gemessen: Pfad external ohne Austausch bricht, 401 mit 77 Bytes, Log-Zeilen [ExternalTokenRequestedListener] received request und [TokenService] getToken: no session data"
  - "S5b gemessen: beide Meldungen des Austauschpfads woertlich reproduziert, TokenService.php:318 und :328"
  - "S5c gemessen und die Ausgangsvermutung bestaetigt: isLoggedIn() liefert unter AppAPI-Impersonation true, in jedem Lauf erscheint eine Listener-Zeile, der Bruch liegt an der Sitzungsfrage und nicht davor"
  - "Die S4-gegen-S5-Zeile an demselben Konto alice: derselbe Aufruf, derselbe gestellte Ablauf, oauth2 200 mit Erneuerung gegen oidc 401 ohne jede Aenderung am Zustand"
  - "Der schaerfste Beleg fuer S5: gueltiger gegen abgelaufener Zwischenspeicher, 341 gegen 77 Bytes, mit und ohne jede user_oidc-Zeile; getAccessToken() Zeile 1748 fragt user_oidc gar nicht, solange der Token gilt"
  - "Die Gegenprobe mit echter Keycloak-Sitzung: getToken findet Sitzungsdaten statt no session data, damit ist die einzige Variable zwischen Haupt- und Gegenlauf das Sitzungscookie"
  - "Stufe C der Messumgebung: Keycloak 26.7.0 hinter Caddy auf 127.0.0.1:8083, user_oidc 8.11.0, Anbieter spike skriptbar eingerichtet, Realm per kcadm.sh statt Import"
  - "Die Nutzer-Id, unter der user_oidc das Konto fuehrt, ist ein Streuwert und nicht alice: jede S5-Zeile nennt deshalb ihr Konto"
  - "docs/contrib/user-oidc-925-kommentar.md, Entwurf mit geglueckter Live-Repro, ausdruecklich unversendet (D-08)"
  - "DI-17-05: der einzige sitzungsfreie OIDC-Pfad ist angelaufen und nicht zu Ende gemessen"
affects:
  - "17-08 bekommt einen Zusatz zu Frage 7 mit Grund: falls openDesk im Modus oidc laeuft, mit welchem sso_provider_type, weil einer der drei Pfade die Sitzungsfrage nicht stellt"
  - "17-09 kann 2.4 jetzt entscheiden: von Weg 0 sind S0 bis S6 vollstaendig gemessen; 2.5 traegt drei vorgemerkte ungemessene Punkte, und der Absatz zum Loglevel steht in Was diese Messung nicht beweist"
  - "OD-04 bekommt den Satz, der die Wahl praegt: Weg 0 traegt im Modus oidc genau so lange wie der zwischengespeicherte Token, und die Erneuerung braucht eine Sitzung, die eine ExApp nicht hat"
  - "Der Owner bekommt einen versandfertigen, unversendeten Entwurf zu nextcloud/user_oidc#925"
tech-stack:
  added:
    - "quay.io/keycloak/keycloak:26.7.0 (Stufe C der Wegwerf-Topologie, Profil oidc)"
    - "user_oidc 8.11.0 (in der Messinstanz, nicht im Paketbaum)"
  patterns:
    - "Den Loglevel senken, bevor der erste Lauf startet, nicht danach: die Zeile, die die Ursache trennt, ist oft debug, und ein nachtraeglich gesenkter Level liefert sie nicht rueckwirkend"
    - "Eine Anwesenheit kann der Messwert sein: dass in jedem Lauf eine Listener-Zeile erscheint, beantwortet S5c, und ein Bericht, der nur auf Fehlermeldungen achtet, uebersieht genau diesen Befund"
    - "Zwei Laeufe, die sich in einer einzigen Zahl unterscheiden, sind mehr wert als zehn, die sich in mehreren unterscheiden: gueltiger gegen abgelaufener Zwischenspeicher isoliert die Ursache ohne jede Auslegung"
    - "Wenn eine Gegenprobe nur die halbe Frage beantwortet, den Hauptlauf genau so kennzeichnen und die andere Haelfte benennen, statt die Gegenprobe als gelungen oder gescheitert zu buchen"
    - "Eine gleichnamige Identitaet auf zwei Seiten ist nicht dasselbe Konto: der Streuwert von user_oidc gegen den Nextcloud-Namen alice, und jede Messzeile nennt deshalb ihre Id"
    - "Aufbaufehler eines Produkts, die wie Produktfehler aussehen, gehoeren mit woertlicher Meldung in den Bericht, nicht in den Papierkorb des Anlaufs"
key-files:
  created:
    - "docs/contrib/user-oidc-925-kommentar.md"
  modified:
    - "compose.spike-opendesk.yml"
    - "deploy/Caddyfile.spike-opendesk"
    - ".env.spike-opendesk.example"
    - "docs/spike-opendesk.md"
    - ".planning/phases/17-opendesk-spike/deferred-items.md"
decisions:
  - "Die Realm ist mit kcadm.sh im Container angelegt worden und nicht mit start-dev --import-realm: der Import ist nach Annahme A1 [ASSUMED], ueberspringt eine vorhandene Realm stillschweigend und haette vor jedem zweiten Lauf ein down -v samt Neuaufbau von Stufe A erzwungen"
  - "Der Moduswechsel auf oidc ist mit occ config:app:set gefahren und nicht ueber PUT /admin-config: der Weg ueber den ConfigController haette nach der Warnung aus 17-05 den oauth2-Zweig zurueckgesetzt und damit das Konto alice als Kontrolle vernichtet, mit dem die S4-gegen-S5-Zeile ueberhaupt erst moeglich ist"
  - "Zwei Kontrollaeufe ueber den Auftrag hinaus genommen: der Pfad nextcloud_hub und das Konto alice. Ohne den ersten stuende der sitzungsfreie Pfad nur als Herleitung da, ohne den zweiten waere S5 nicht mit S4 vergleichbar"
  - "Der Lauf gegen den noch gueltigen Zwischenspeicher ist als eigener Messwert genommen worden, obwohl der Plan ihn nicht verlangt: er ist der einzige, der die Behauptung von S5 auf eine einzige Variable reduziert"
  - "Die Gegenprobe ist als halb gelungen protokolliert und nicht als gelungen gebucht: sie belegt die Sitzungsfrage und nicht die Datenlieferung, und der Unterschied steht als Vermerk am Hauptlauf"
  - "OD-02 bleibt Pending: dieser Plan schliesst Weg 0 mit S5 ab, der Vergleich beider Wege ist 17-09. Fortsetzung der Entscheidung aus 17-01 bis 17-06"
metrics:
  duration: 64 min
  completed: 2026-08-29
---

# Phase 17 Plan 07: S5 gemessen, und der Bruch hat einen anderen Ort als vermutet Summary

S5 ist gemessen und nicht behauptet: Weg 0 fällt im Modus `oidc` nach Ablauf des zwischengespeicherten Tokens auf 401, und vier Protokollzeilen sagen wörtlich, woran. Der wichtigste Einzelbefund ist aber nicht die 401, sondern eine Anwesenheit: in **jedem** Lauf erscheint eine Listener-Zeile, also liefert `IUserSession::isLoggedIn()` unter AppAPI-Impersonation `true`. Der Bruch liegt damit nicht vor der Sitzungsfrage, sondern genau an ihr.

## Die Messwerte, die dieser Plan schuldig war

| Behauptung | Messweg | Messwert | Gegenprobe |
|-----------|---------|----------|------------|
| **S5a**, Pfad `external` ohne Austausch bricht nach Ablauf | `occ user:setting <konto> ... token_expires_at 0`, dann derselbe OCS-Aufruf wie in S4 unter reiner AppAPI-Impersonation, Loglevel vorher auf `Debug (0)` | **401**, 77 Bytes, leere Meldung; `[ExternalTokenRequestedListener] received request`, `[TokenService] getToken: no session data`, `Token event has not been caught by 'user_oidc'`; Zustand unverändert | derselbe Lauf mit `store_login_token 0` liefert eine **andere** Meldung: `Failed to get external token, login token is not stored`. Die zwei Bruchstellen desselben Pfades sind damit unterscheidbar |
| **S5b**, Pfad `external` **mit** Austausch, zwei Meldungen | dasselbe, `token_exchange 1`, je ein Lauf mit `store_login_token` 0 und 1 | beide wörtlich: `Failed to exchange token, storing the login token is disabled. It can be enabled in config.php` (`TokenService.php:318`) und `Failed to exchange token, no login token found in the session` (`TokenService.php:328`) | die Meldungen unterscheiden sich, obwohl der Statuscode in beiden 401 ist; ohne den Log wären beide Läufe derselbe Messwert |
| **S5c**, liefert `isLoggedIn()` unter Impersonation `true`? | die Anwesenheit oder Abwesenheit einer Listener-Zeile in allen sechs Läufen | **`true`.** In jedem der sechs Läufe erscheint die Listener-Zeile, also hat `if (!$this->userSession->isLoggedIn()) { return; }` nicht gegriffen | Kontrolle im selben Protokoll: die Zeile `checkLoginToken: user not logged in` stammt aus einem anderen Aufrufweg und ist ausdrücklich **nicht** der S5c-Messwert |
| **S4 gegen S5 am selben Konto** | `alice`, derselbe Aufruf, derselbe gestellte Ablauf, nur `authorization_method` verschieden | `oauth2` (17-06): **200**, `token_expires_at` **+7200 s**, neues Tokenpaar. `oidc` (heute): **401**, `token_expires_at` bleibt **0**, `token` unverändert | der Kommentar in `OpenProjectAPIService.php:1764-1765` ist damit beidseitig gemessen und nicht nur zitiert |
| **Die Ursache, auf eine Variable reduziert** | zwei Läufe desselben Kontos ohne Cookie, unterschieden nur durch den Ablauf des Zwischenspeichers | gültig: **341 Bytes**, **keine** `user_oidc`-Zeile. Abgelaufen: **77 Bytes**, vier Zeilen bis `no session data` | `getAccessToken()` Zeile 1748 fragt `user_oidc` gar nicht, solange der Token gilt |
| **Gegenprobe mit echter Sitzung** | derselbe Aufruf mit dem Cookie aus einer Keycloak-Anmeldung, sonst identische Konfiguration | `[TokenService] getToken: token is still valid, it expires in 300`, Erneuerung gegen Keycloak, `New token expires at 2026/08/29 02:38:56` | endet an OpenProject mit `urn:openproject-org:api:v3:errors:Unauthenticated`, weil OpenProject an dieselbe Keycloak nicht gebunden ist (Out of Scope) |

## Der Satz, der aus diesem Plan in 17-09 gehört

**Weg 0 trägt im Modus `oidc` genau so lange, wie der zwischengespeicherte Token gilt, und fällt danach auf 401.** Das ist keine Auslegung, sondern ein Paar von Läufen, das sich in einer einzigen Zahl unterscheidet: bei gültigem Zwischenspeicher wird `user_oidc` überhaupt nicht befragt (null Zeilen im Protokoll, 341 Bytes Antwort), bei abgelaufenem läuft die Ereigniskette an und endet an der Sitzung (vier Zeilen, 77 Bytes). Die Erneuerung, die S4 im Modus `oauth2` gemessen hat, existiert im OIDC-Zweig nicht; sie verlangt dort eine Sitzung, und eine ExApp unter Impersonation hat keine.

## Was an der Ausgangsvermutung stimmte und was nicht

Die Recherche hielt für offen, ob `isLoggedIn()` unter Impersonation `false` liefert und Weg 0 damit **vor** der Sitzungsfrage bricht (Annahme A9, zwei verwertbare Ausgänge). Gemessen ist der andere Ausgang: die Prüfung greift nicht, jeder Listener wird betreten, und die Diagnose aus `research/SUMMARY.md` ist damit **bestätigt statt ersetzt**.

**Das ist die teuerste Zeile des Plans, weil sie leicht falsch herum gelesen wird.** Im selben Protokoll steht `[TokenService] checkLoginToken: user not logged in`, aus einem anderen Aufrufweg desselben Zeitfensters. Wer nach der Zeichenkette `not logged in` greift, findet sie und schreibt genau die Ursache in den Bericht, die die Messung widerlegt. Die Listener-Zeile im selben Lauf beweist das Gegenteil für den Pfad, um den es geht, und der Bericht sagt das als eigenen Absatz.

## Der dritte Pfad, der nicht bricht, und die Grenze der Aussage

Von den drei Ereignispfaden aus K5 stellt genau einer die Sitzungsfrage nicht: `nextcloud_hub` reicht eine Nutzer-Id weiter statt eine Sitzung zu lesen. Der Kontrolllauf zeigt beides: der Listener läuft (`[InternalTokenRequestedListener] received request for audience: openproject`), und danach kommt **keine** Zeile über eine Sitzung. Er endet aber an `oidc app is not installed`, weil dieser Pfad Nextcloud selbst als Anbieter verlangt.

**Der Bericht sagt deshalb nicht, dass der OIDC-Betrieb Weg 0 verunmöglicht.** Er sagt: beide sitzungsgebundenen Pfade sind getroffen und brechen, der sitzungsfreie ist angelaufen und **ungemessen**. Das ist als DI-17-05 mit Kostenschätzung abgelegt, damit 17-09 den Unterschied zwischen "widerlegt" und "nicht gemessen" nicht einebnet (D-03).

## Die Gegenprobe ist halb gelungen, und das steht als Vermerk am Hauptlauf

Ohne Gegenprobe wäre jede 401 auch mit einer kaputten Keycloak-Kopplung erklärbar. Mit dem Sitzungscookie einer echten Anmeldung findet dieselbe Konfiguration am selben Konto Sitzungsdaten statt `no session data`, erneuert das Token gegen Keycloak und reicht es an `integration_openproject` weiter, das es unter dem Konto ablegt. **Damit ist die einzige Variable zwischen Hauptlauf und Gegenprobe das Sitzungscookie**, und die Ursache der sechs 401 ist gemessen.

Daten liefert die Gegenprobe nicht: OpenProject ist an dieselbe Keycloak nicht gebunden, weil ein eigener Keycloak-Client für OpenProject in `REQUIREMENTS.md` Out of Scope ist, und weist das sonst gültige Token mit `urn:openproject-org:api:v3:errors:Unauthenticated` ab. Der Hauptlauf trägt deshalb wörtlich den Vermerk **gegengeprobt auf die Sitzungsfrage, nicht gegengeprobt auf die Datenlieferung**. Eine als vollständig gebuchte Gegenprobe hätte behauptet, dass OIDC-gebundenes Weg 0 mit Sitzung Daten liefert, und das ist hier nicht gemessen.

## Der Entwurf zu `user_oidc#925`

Die Bedingung aus D-08 ist erfüllt: die Live-Reproduktion ist gelaufen, `TokenService.php:318` und `:328` stehen wörtlich im Protokoll. `docs/contrib/user-oidc-925-kommentar.md` liegt deshalb im Repository, englisch, mit der Statuszeile `Entwurf, nicht gesendet. Versand ausschliesslich durch den Owner.`

**Gesendet wurde nichts.** Kein `gh issue comment`, kein Browserversand, kein Playwright-Lauf, kein Aufruf an eine fremde Adresse. Der Text trägt die Einordnung, dass `#925` die Anfrage ist, aus der die heutige Implementierung entstanden ist, damit er nicht wie eine Fehlermeldung zu einem erledigten Feature liest. Er nennt die vier Fassungen aus `occ status` und `occ app:list`, die Reproduktionsschritte, die wörtlichen Log-Zeilen und die Codestellen mit Datei, Zeile und Tag. Er korrigiert außerdem die eigene Vorannahme des zurückgehaltenen Entwurfs vom 28.08.: der Blocker ist nicht die Anmeldeprüfung, sondern das fehlende Sitzungstoken eine Zeile später. Kein Token, kein Secret, kein Cookie, nur Loopback-Adressen.

## Deviations from Plan

**1. [Rule 3 - Der Aufbau des Plans startete nicht] `KC_HOSTNAME` als vollständige URL statt als `host:port`**
- **Gefunden bei:** Task 1, unmittelbar nach dem ersten `up`
- **Problem:** Der Plan nennt wörtlich `KC_HOSTNAME=kc.localtest.me:8083`. Keycloak 26.7.0 lief damit in eine Neustartschleife mit `ERROR: Failed to start server in (development) mode` und `Provided hostname is neither a plain hostname nor a valid URL`. 26.x nimmt entweder einen Namen ohne Port oder eine vollständige URL, nichts dazwischen. Ohne Fix hätte Stufe C nicht existiert und S5 wäre ungemessen geblieben, aus einem Aufbaugrund.
- **Fix:** `http://kc.localtest.me:8083`, mit dem Grund als Kommentar in der Compose-Datei und der wörtlichen Meldung als Rohwert in 5.6.2, damit ein Nachbau denselben Anlauf nicht wiederholt.
- **Dateien:** `compose.spike-opendesk.yml`, `docs/spike-opendesk.md`
- **Commit:** 9b5ad64, 83605bf

**2. [Rule 3 - Die Anmeldung über Keycloak war auf Loopback nicht möglich] `allow_insecure_http`**
- **Gefunden bei:** Task 1, beim Start des Anmeldeflusses
- **Problem:** `GET /apps/user_oidc/login/1` antwortete **404** mit der Seite `You must access Nextcloud with HTTPS to use OpenID Connect.` Ohne Anmeldung gäbe es kein OIDC-Konto, keine Nutzer-Id und keine Gegenprobe mit echter Sitzung; die halbe Aussagekraft von S5 hätte gefehlt.
- **Fix:** `LoginController::isSecure()` gelesen (`LoginController.php:121-126`, drei Bedingungen: https, Debug-Modus **oder** der App-Konfigwert `allow_insecure_http`), den App-Konfigwert gesetzt statt den Debug-Modus einzuschalten, und den Eingriff samt wörtlicher Meldung als Rohwert und als Absatz unter "Was diese Messung nicht beweist" protokolliert. Dasselbe Muster wie `allow_local_remote_servers` in 17-05: nicht stillschweigend setzen.
- **Dateien:** `docs/spike-opendesk.md`
- **Commit:** 83605bf

**3. [Rule 3 - Das Kommando des Plans existiert in 8.11.0 nicht] `user_oidc:providers` statt `user_oidc:provider:list`**
- **Gefunden bei:** Task 1, beim Kontrollschritt
- **Problem:** Der Plan und die Recherche nennen `occ user_oidc:provider:list`. 8.11.0 antwortet `Command "user_oidc:provider:list" is not defined` und schlägt selbst `user_oidc:providers` vor. Das Gate des Tasks hätte auf einem nicht existierenden Kommando bestanden.
- **Fix:** `occ user_oidc:providers` gefahren, Anbieter `spike` bestätigt (`clientId nextcloud`, Discovery-Adresse, Scope `openid email profile`, `clientSecret` vom Werkzeug selbst als `********` ausgegeben). Der Rohwertabschnitt nennt das richtige Kommando.
- **Dateien:** `docs/spike-opendesk.md`
- **Commit:** 83605bf

**4. [Rule 2 - Der bequeme Weg hätte jeden zweiten Lauf verfälscht] Realm per `kcadm.sh` statt `--import-realm`**
- **Gefunden bei:** Task 1
- **Problem:** Der Plan sieht `start-dev --import-realm` vor und nennt ihn selbst `[ASSUMED]` (Annahme A1). Der Import überspringt eine vorhandene Realm stillschweigend, also hätte jeder zweite Lauf ein `down -v` samt Neuaufbau von Stufe A verlangt, und ein vergessenes `down -v` hätte unbemerkt die Konfiguration des ersten Laufs gemessen.
- **Fix:** Realm, beide Clients und beide Konten mit `kcadm.sh` im laufenden Container angelegt, also vollständig skriptbar und ohne den Zustandsfehler des Imports. Das Client-Secret ist nach `.env.spike-opendesk` geschrieben und danach gegen den laufenden Wert verglichen worden (86 Zeichen, Keycloak 26.7.0 vergibt nicht mehr 32).
- **Dateien:** `.env.spike-opendesk.example`, `docs/spike-opendesk.md`
- **Commit:** 9b5ad64, 83605bf

**5. [Rule 2 - Der Moduswechsel hätte die Kontrolle vernichtet] `occ config:app:set` statt `PUT /admin-config`**
- **Gefunden bei:** Task 1, vor dem Schalten
- **Problem:** Hinweis 1 aus 17-06 warnt, dass ein Wechsel von `oauth2` auf `oidc` über den `ConfigController` einen Reset des anderen Zweigs auslöst (`setIntegrationConfig`, `clearUserInfo`). Damit wären `token` und `refresh_token` von `alice` weg gewesen, und der wertvollste Kontrolllauf des Plans, dieselbe Kette an demselben Konto einmal in `oauth2` und einmal in `oidc`, wäre unmöglich geworden.
- **Fix:** Erst gelesen, dann mit `occ config:app:set` geschaltet, was den Controller nicht durchläuft, und den Zustand von `alice` vor und nach dem Wechsel gemessen: `token` Länge 43 mit Präfix `Jm2D` und `token_expires_at 1787975808` unverändert. Der Kontrolllauf ist als Lauf 6 in der Messtabelle.
- **Dateien:** `docs/spike-opendesk.md`
- **Commit:** 83605bf

**6. [Rule 2 - Ohne diesen Lauf stünde der sitzungsfreie Pfad nur als Herleitung da] Kontrolllauf `nextcloud_hub`**
- **Gefunden bei:** Task 2
- **Problem:** Der Plan verlangt, alle drei Pfade im Bericht zu führen und den getroffenen zu markieren. Für `nextcloud_hub` hätte das geheißen, K5 zu zitieren und nichts zu messen, und der Bericht hätte über den einzigen Pfad, der unter Impersonation eine Aussicht hätte, ausschließlich fremden Code wiedergegeben.
- **Fix:** Einen sechsten Lauf mit `sso_provider_type=nextcloud_hub` gefahren. Ergebnis mit Belegwert: der Listener läuft, **keine** Sitzungszeile folgt, und er bricht an einer ganz anderen Stelle (`oidc app is not installed`). Als DI-17-05 mit Kostenschätzung abgelegt und in 2.5 als ungemessener Punkt benannt.
- **Dateien:** `docs/spike-opendesk.md`, `.planning/phases/17-opendesk-spike/deferred-items.md`
- **Commit:** 83605bf, dieses SUMMARY

**7. [Rule 2 - Die Behauptung von S5 wäre sonst nur indirekt belegt] Der Lauf gegen den gültigen Zwischenspeicher**
- **Gefunden bei:** Task 2, nach der Gegenprobe
- **Problem:** S5 behauptet einen Bruch **nach Ablauf des zwischengespeicherten Tokens**. Alle sechs Läufe stellen den Ablauf, also belegen sie den Bruch, aber nicht, dass der Ablauf die Ursache ist. Ein Prüfer dürfte fragen, ob der Aufruf im Modus `oidc` nicht ohnehin immer 401 antwortet.
- **Fix:** Die Gegenprobe hatte am Konto einen gültigen Token hinterlassen, und derselbe impersonierte Aufruf ist innerhalb seiner Restlaufzeit gefahren worden: **341 statt 77 Bytes** und **keine einzige** `user_oidc`-Zeile. Damit ist der Ablauf als Ursache isoliert und `getAccessToken()` Zeile 1748 als Mechanismus benannt.
- **Dateien:** `docs/spike-opendesk.md`
- **Commit:** 83605bf

**8. [Rule 2 - Eine halbe Gegenprobe als ganze zu buchen wäre die schwerste Ungenauigkeit des Plans] Der Vermerk am Hauptlauf**
- **Gefunden bei:** Task 2
- **Problem:** Der Plan verlangt, dass die Gegenprobe mit echter Sitzung Daten liefert, und sonst den Hauptlauf als nicht gegengeprobt zu markieren. Gemessen ist ein dritter Fall: sie gelingt an der Sitzungsfrage und scheitert danach an OpenProject, weil dessen Bindung an Keycloak in `REQUIREMENTS.md` Out of Scope ist. Beide vorgesehenen Buchungen wären falsch gewesen.
- **Fix:** Den Vermerk aufgeteilt und wörtlich hingeschrieben: gegengeprobt auf die Sitzungsfrage, nicht gegengeprobt auf die Datenlieferung, mit der Ursache und dem Verweis auf die Out-of-Scope-Grenze. Der Bericht behauptet damit nicht, dass OIDC-gebundenes Weg 0 mit Sitzung Daten liefert.
- **Dateien:** `docs/spike-opendesk.md`
- **Commit:** 83605bf

**9. [Rule 2 - Zwei gleichnamige Konten in einem Bericht] Die Nutzer-Id von `user_oidc` benannt**
- **Gefunden bei:** Task 1, nach der ersten Anmeldung
- **Problem:** `user_oidc` legt das Konto unter dem Streuwert `3855a8f7...` an, nicht unter `alice`. In einem Bericht, der neben dem Nextcloud-Konto `alice` auch ein Keycloak-Konto `alice` kennt, wäre jede Messzeile ohne diese Id mehrdeutig, und das Entscheidungskriterium dieses Berichts lautet: kein Nutzername, kein Messwert.
- **Fix:** `occ user:list` als Rohwert übernommen, die Id in 5.6.3 vollständig und in den Messtabellen gekürzt geführt, mit einem Absatz, der die zwei gleichnamigen Konten auseinanderhält.
- **Dateien:** `docs/spike-opendesk.md`
- **Commit:** 83605bf

**10. [Rule 1 - Verstoß gegen eine Projektregel im eigenen Text] Deutsche Kommentare mit ASCII-Ersatzschreibung**
- **Gefunden bei:** Task 1, bei der Stilprüfung vor dem Commit
- **Problem:** Der neue Caddy-Block war in deutschen Kommentaren mit `ae`, `oe`, `ue` und `ss` geschrieben, obwohl die Datei durchgehend englisch ist und die Projektregel ASCII-Ersatz für Umlaute verbietet.
- **Fix:** Den Block auf Englisch umgeschrieben, wie der Rest der Datei. Damit fällt die Umlautfrage weg, statt sie falsch zu lösen. Vor dem Commit geprüft: kein U+2014, kein U+2013, kein Zeichen oberhalb U+2600 in den geänderten Dateien.
- **Dateien:** `deploy/Caddyfile.spike-opendesk`
- **Commit:** 9b5ad64

**11. [Rule 2 - Die Beispieldatei hätte einen Nachbau raten lassen] Drei Schlüssel ergänzt**
- **Gefunden bei:** Task 1
- **Problem:** `.env.spike-opendesk.example` kannte nur `KC_BOOTSTRAP_ADMIN_*` und `KC_CLIENT_SECRET`. Der Lauf braucht zusätzlich die Realm und die zwei Konten in ihr, und die Compose-Datei verweist für die Benennung genau auf diese Beispieldatei.
- **Fix:** `KC_REALM`, `KC_ALICE_PASSWORD` und `KC_BOB_PASSWORD` mit Erklärung ergänzt, dazu der Hinweis, dass die Keycloak-Konten nicht die Nextcloud-Konten gleichen Namens sind, und die Anmerkung zur Länge des Client-Secrets in 26.7.0. Kein Wert, nur Platzhalter.
- **Dateien:** `.env.spike-opendesk.example`
- **Commit:** 9b5ad64

**12. [Rule 1 - Verfrühter Statuswechsel, wie in 17-01 bis 17-06] OD-02 bleibt Pending**
- **Gefunden bei:** Zustandsaktualisierung
- **Problem:** Die Frontmatter nennt `requirements: [OD-02]`, und `requirements mark-complete` hätte OD-02 abgehakt. OD-02 verlangt Weg 0 und Weg 1 mit Messwerten **nebeneinander**; Weg 0 ist mit diesem Plan vollständig, der Vergleich selbst ist 17-09.
- **Fix:** OD-02 bleibt `Pending` und wird von 17-09 abgehakt.
- **Dateien:** keine
- **Commit:** derselbe wie dieses SUMMARY

**13. [Bekannte Gate-Eigenheit, nicht behoben, hier benannt] `grep -v '^#'` entfernt jede Überschrift**
- **Gefunden bei:** Task 2, beim Lauf des Gates
- **Problem:** Dieselbe Eigenheit, die 17-03 (Abweichung 7), 17-04 (9), 17-05 (11) und 17-06 (6) gemeldet haben.
- **Fix:** Nicht umgeschrieben. Beide Prüfungen gefahren und beide grün: der gefilterte Griff für `S5a`, `S5c`, `TokenService`, `ungemessen` und `nextcloud_hub`, und ungefiltert der `artifacts`-Griff nach `S5` sowie nach `Entwurf` in der neuen Datei.
- **Dateien:** keine
- **Commit:** keiner

Sonst keine. Insbesondere ist keine der vier schreibenden und auch nicht die freiwillig ausgeschlossene Formularroute ausgelöst worden, kein `client_credentials`-Lauf gefahren, und nichts ist an einen Dritten gesendet worden.

## Authentication Gates

**Keiner.** Alle drei Tasks liefen autonom. Ein Owner-Schritt wäre nur nötig gewesen, wenn der Ungemessen-Fallback von Task 1 gegriffen hätte; er hat nicht gegriffen, nachdem die zwei Aufbaufehler aus den Abweichungen 1 und 2 aufgelöst waren.

Der Anmeldefluss über Keycloak ist per Formular gefahren worden, nicht über einen Browser: Start `GET /apps/user_oidc/login/1`, Anmeldeformular der Realm, Rückweg auf `/apps/user_oidc/code`, Ende **303** auf `/apps/dashboard/`. Die dabei verwendeten Zugangsdaten stammen aus der git-ignorierten Verbindungsdatei; kein Wert ist gedruckt worden, weder in einem Protokoll noch in einer verfolgten Datei noch in diesem SUMMARY.

**Ein Owner-Schritt bleibt offen und ist ausdrücklich keiner dieses Plans:** der Versand von `docs/contrib/user-oidc-925-kommentar.md`. Kein Agent hat ihn gesendet, und keiner darf es.

## Verification

- Task-1-Gate: Discovery-Adresse **200** vom Host und **200** aus dem Nextcloud-Container, unter demselben Namen `kc.localtest.me:8083`; der `issuer` im Dokument trägt genau diesen Namen und Port. `occ user_oidc:providers` nennt `spike` (Abweichung 3). `occ config:app:get integration_openproject authorization_method` ergibt `oidc`, `occ config:app:get user_oidc store_login_token` ergibt `1`.
- **Der Loglevel stand auf `Debug (0)`, bevor der erste S5-Lauf startete**, geprüft mit `occ log:manage` vor Task 2 und erneut danach. Ohne diesen Schritt hätten alle sechs Läufe eine nackte 401 ohne Ursache geliefert.
- Task-2-Gate: `S5a`, `S5c`, `TokenService`, `nextcloud_hub` im Bericht gefunden; der Griff nach dem JWT-Präfix und nach `refresh_token` mit Wert bleibt ohne Treffer.
- Task-3-Gate: die Datei existiert, trägt `Entwurf`, `Entwurf, nicht gesendet` und `TokenService.php`, und die Griffe nach dem JWT-Präfix, nach `Bearer` mit Wert und nach `client_secret` bleiben ohne Treffer.
- `artifacts`-Einträge: `contains: "S5"` in `docs/spike-opendesk.md` grün, `contains: "Entwurf"` in der neuen Datei grün. `key_links`-Muster `token_exchange` steht in 2.1 und in 5.6.
- Geheimnis-Gate: `git grep -F` über die Werte aller 30 Schlüssel aus `.env.spike-opendesk` mit mindestens acht Zeichen, über `compose.spike-opendesk.yml`, `deploy/Caddyfile.spike-opendesk`, `.env.spike-opendesk.example` und `docs/contrib/user-oidc-925-kommentar.md`: **kein Treffer**. Über `docs/spike-opendesk.md` vier Treffer, alle nachgesehen und alle keine Geheimnisse: `APP_ID` ist `mcp_connector`, und `NC_MCP_URL`, `NC_MCP_PUBLIC_URL` und `NC_MCP_EXAPP_BASE` sind Loopback-Adressen, die der Bericht ohnehin nennt. Muster-Gate über beide geschriebenen Dokumente ohne neuen Treffer; der eine Fund `Bearer TESTBEARERTOKEN` steht seit 17-05 in 5.4 und ist der wörtlich zurückgegebene Testwert einer Gegenprobe.
- **Jede übernommene Protokollzeile ist vor der Übernahme gegen jeden Wert der Verbindungsdatei geprüft worden.** Übernommen sind ausschließlich Meldungen der Apps `user_oidc` und `integration_openproject`, ohne die Kontextfelder mit Kopfzeilen (T-17-01). Der Token, den die Gegenprobe erzeugt hat, steht nur als Länge (1387) und Formbeschreibung im Bericht, nie als Wert.
- `uv run pytest -q` mit `env -u APP_ID -u APP_SECRET -u APP_VERSION`: Rücknahmewert **0**, dreimal gefahren (nach Task 2, vor dem Commit von Task 3, nach dem Commit von Task 3). Das Vokabular-Gate hängt an ganz `docs/` und ist damit mitgelaufen.
- Vokabular außerdem einzeln geprüft: das verbotene Wort kommt in `docs/spike-opendesk.md` und in `docs/contrib/user-oidc-925-kommentar.md` **null**mal vor. Kein U+2014 und kein U+2013, kein Zeichen oberhalb U+2600, keine ASCII-Ersatzschreibung von Umlauten (Abweichung 10), 0 CRLF in beiden Dokumenten.
- **Produktionsbaum unverändert (D-12):** `git status --short src/ appinfo/ pyproject.toml uv.lock` ist leer, nach jedem der drei Commits geprüft. `files_modified` des Plans nennt keinen Pfad unter `src/`. Werkzeugoberfläche und Budget-Gate sind nicht angefasst; `TokenService.php`, die drei Listener, `LoginController.php` und `OpenProjectAPIService.php` liegen in Containern und nicht in diesem Baum und wurden ausschließlich gelesen.
- Topologie: `docker compose config` gültig, `caddy validate` meldet `Valid configuration` im laufenden Container. Alle sechs Bildmarken gepinnt, Keycloak auf `quay.io/keycloak/keycloak:26.7.0` mit Digest `sha256:0f198be2`. Keine `ports`-Zeile bindet etwas anderes als `127.0.0.1`; die drei veröffentlichten Häfen sind `8091`, `8082`, `8083` und `5001`. Kein neues Geheimnis mit Vorgabewert in der Compose-Datei.
- Loopback: jeder Aufruf ging an `127.0.0.1:8091`, `kc.localtest.me:8083` oder `op.localtest.me:8082`, alle mit `curl -4`. Kein Aufruf an eine fremde Adresse, nichts an einen Dritten gesendet, keine gemietete Infrastruktur, kein `wsl --shutdown`, keine `.wslconfig`. Die zwei Container fremder Projekte (`findling-nextcloud`, `nc-mcp-test`) laufen unverändert weiter.
- Keiner der drei Commits löscht eine verfolgte Datei; `git status --short` ist nach dem letzten sauber bis auf die Dateien dieses SUMMARY.
- Zwischendateien der Messung (Skripte, Protokollauszüge, Cookie-Speicher) liegen im Temporärverzeichnis und **nicht** im Repository (D-12).

## Known Stubs

Beabsichtigt und im Bericht gekennzeichnet: 2.4 (17-09), 4 (17-08), "Was diese Messung nicht beweist" (17-09). Abschnitt 2.5 trägt weiter seine Zeile `noch nicht gemessen, Plan 17-09`, jetzt aber mit zwei vorgemerkten Blöcken (Weg A aus 17-05, die drei ungemessenen Punkte von S5 aus diesem Plan).

**Abschnitt 2.1 ist mit diesem Plan kein Stub mehr.** Von S0 bis S6 trägt jede Behauptung einen Messwert mit Gegenprobe; die Kopfzeilen `user_oidc` und Keycloak sind aus der laufenden Instanz gefüllt.

Kein Stub verhindert das Ziel dieses Plans.

## Threat Flags

Keine neue Fläche über das Bedrohungsmodell des Plans hinaus. Sechs Anmerkungen zu Einträgen daraus:

- **T-17-01 (Information Disclosure), gehalten:** kein Token, kein Client-Secret, kein Passwort, kein Cookie und kein `AUTHORIZATION-APP-API`-Wert steht in einer verfolgten Datei, in einem Protokoll oder in diesem SUMMARY. Von den Protokollzeilen sind ausschließlich die Meldungen samt Klassennamen übernommen, nie der Kontext mit Kopfzeilen. Der von der Gegenprobe erzeugte Token erscheint nur als Länge und Formbeschreibung.
- **T-17-06 (Information Disclosure), gehalten und benannt:** `occ log:manage --level 0` gilt einer Wegwerf-Instanz auf Loopback, verschwindet mit dem Nextcloud-Band, und der Bericht sagt unter "Was diese Messung nicht beweist" ausdrücklich, dass daraus keine Empfehlung für Produktion wird. Derselbe Absatz führt `allow_insecure_http` mit, das aus demselben Grund gesetzt wurde und dieselbe Einschränkung trägt.
- **T-17-02 (Spoofing, Tampering), gehalten:** `127.0.0.1:8083` und nicht `0.0.0.0`, `KC_BOOTSTRAP_ADMIN_*` ohne Vorgabewert in der Compose-Datei, Realm und beide Clients ausschließlich für diese Messung.
- **T-17-05 (Repudiation), gehalten und über den Plan hinaus:** jede der sechs Zeilen trägt ihre wörtliche Log-Zeile, und für die Ursache selbst ist eine zweite Art von Gegenprobe dazugekommen, die nicht den Messwert, sondern den **Mechanismus** isoliert (Abweichung 7). Die drei Pfade stehen vollständig mit Datei und Zeile im Bericht, und der ungemessene ist als ungemessen bezeichnet.
- **T-17-03 (Elevation of Privilege), gehalten:** der Client `openproject` in der Realm ist ausschließlich Zielgruppe des Austauschs, hat kein Dienstkonto und ist an keiner Stelle als solches benutzt worden. Der Bericht sagt genau das, und die Gegenprobe endet gerade deshalb an OpenProject.
- **T-17-04 (Tampering), gehalten:** geschrieben sind die Spike-Topologie, die Beispieldatei, der Bericht, der Entwurf unter `docs/contrib/` und die Fundliste der Phase. `src/` bleibt unberührt.

**Ein Zustand der Messumgebung, der benannt sein muss, weil ein Folgeplan ihn vorfindet:** `integration_openproject` steht am Ende dieses Plans auf `authorization_method oidc` mit `sso_provider_type external` und `token_exchange 0`, `alice` und `bob` tragen beide `token_expires_at 0`, und `user_oidc` trägt `store_login_token 1` und `allow_insecure_http 1`. Der Modus ist absichtlich **nicht** zurückgestellt worden: der Rückstellschritt des Plans gehört zum Ungemessen-Fallback, der nicht gegriffen hat, und ein Zurückschalten wäre eine ungemessene Änderung am gemessenen Zustand. Wer den `oauth2`-Zweig wieder braucht, schaltet ihn mit `occ config:app:set` zurück und stellt an `alice` einen Ablauf in der Zukunft ein; ihr `refresh_token` ist unversehrt.

## Hinweise für die Folgepläne

1. **Für 17-09 ist die Kernzeile fertig formuliert:** Weg 0 trägt im Modus `oidc` genau so lange, wie der zwischengespeicherte Token gilt. Sie steht in 2.1 mit dem Paar aus gültigem und abgelaufenem Zwischenspeicher und braucht in 2.4 nur noch das Urteil, nicht die Messung.
2. **Der Unterschied zwischen "widerlegt" und "ungemessen" hängt hier an einem einzigen Pfad.** Zwei der drei Ereignispfade sind gemessen gebrochen, der dritte ist ungemessen (DI-17-05). Ein Satz, der aus S5 folgert, dass Weg 0 im OIDC-Betrieb nicht geht, überdehnt die Messung genau um diesen Pfad.
3. **Für 17-08 ein Zusatz zu Frage 7 mit Grund:** falls openDesk `integration_openproject` im Modus `oidc` fährt, mit welchem `sso_provider_type`. Von der Antwort hängt ab, ob der einzige sitzungsfreie Pfad überhaupt in Betracht kommt, und die Frage ist ohne diesen Plan nicht stellbar gewesen.
4. **Der Entwurf zu `user_oidc#925` wartet auf den Owner.** Er liegt unter `docs/contrib/user-oidc-925-kommentar.md`, ist unversendet, und kein Agent sendet ihn.
5. **Wer S5 nachfährt, senkt zuerst den Loglevel.** Drei der vier entscheidenden Meldungen sind `logger->debug`, und der Vorgabewert `Warning (2)` verschluckt sie. Ein nachträglich gesenkter Level liefert sie nicht rückwirkend, und ein Lauf ohne sie sieht aus wie eine 401 ohne Ursache.
6. **Die Falle beim Lesen des Protokolls:** `checkLoginToken: user not logged in` stammt aus einem anderen Aufrufweg und beantwortet S5c nicht. Der Messwert für S5c ist die Anwesenheit der Listener-Zeile.
7. **Die zwei gleichnamigen Konten.** Das Keycloak-Konto `alice` und das Nextcloud-Konto `alice` sind verschiedene Konten; `user_oidc` führt das erste unter einem Streuwert. Jede Messzeile nennt deshalb ihre Id, und 5.6.3 nennt sie vollständig.
8. **Die drei Exporte vor jedem compose-Kommando gelten weiter** (`set -a && . ./.env.spike-opendesk && set +a`), `pytest` braucht weiter `env -u APP_ID -u APP_SECRET -u APP_VERSION`, `curl -4` bleibt Pflicht wegen der AAAA-Falle von `localtest.me`, und das Vokabular-Gate hängt an ganz `docs/`.

## Self-Check: PASSED

Die fünf genannten Dateien existieren (`compose.spike-opendesk.yml`, `deploy/Caddyfile.spike-opendesk`, `.env.spike-opendesk.example`, `docs/spike-opendesk.md`, `docs/contrib/user-oidc-925-kommentar.md`), und alle drei Commit-Kennungen (9b5ad64, 83605bf, 09e6707) sind im Repository auffindbar. `git status --short src/ appinfo/ pyproject.toml uv.lock` ist leer, `uv run pytest -q` gibt 0 zurück, und kein Wert aus `.env.spike-opendesk` steht im Bericht oder im Entwurf. Keine Behauptung dieses SUMMARY steht ohne den Messwert, aus dem sie kommt; wo eine Messung fehlt (der Pfad `nextcloud_hub`, die Datenlieferung mit Sitzung, die Betriebsart von openDesk), sagt der Text das mit dem Wort `ungemessen` samt Grund und nicht als Vermutung. `verworfen` steht über keinen Weg und über keine Frage.
