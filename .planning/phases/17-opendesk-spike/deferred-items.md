# Zurückgestellte Funde, Phase 17

Funde, die während der Ausführung entstanden sind, aber nicht in den Auftrag des laufenden Plans
gehören. Sie werden hier festgehalten und **nicht** nebenbei behandelt.

## DI-17-01: OpenProject 17.7.2 bringt einen eigenen MCP-Server mit

**Gefunden:** 2026-08-28, Plan 17-03, Task 1, beim Prüfen der OAuth-Scopes für die Anweisungen an
den Owner (Task 2).

**Belege, alle aus dem laufenden Container `nc-mcp-spike-od-op`, Bildmarke
`openproject/openproject:17.7.2`, Digest `sha256:19a828d6`:**

| Beleg | Datei und Zeile | Inhalt |
|-------|-----------------|--------|
| ein montierter MCP-Endpunkt | `/app/config/routes.rb:48` | `mount API::Mcp => "/mcp"` |
| eine Verwaltungsseite dafür | `/app/config/routes.rb:676` | `resources :mcp_configurations, only: %i[index update], controller: "admin/mcp_configurations"` |
| ein eigener OAuth-Scope | `/app/config/initializers/doorkeeper.rb:136` | `optional_scopes :scim_v2, :mcp` |
| Seed-Schritt beim ersten Start | `/app/app/seeders/root_seeder.rb`, Logzeile des ersten Starts | `*** Seeding MCP configuration` |
| Antwortverhalten | `GET http://op.localtest.me:8082/mcp` unauthentifiziert | 500, also eine antwortende Route und keine 404. Die Form der Antwort ist **nicht** gemessen |

**Warum das hier steht und nicht im Bericht:** Dieser Plan hat den Auftrag, OpenProject
hochzufahren und den Grundzustand für den Zwei-Konten-Negativbeweis anzulegen. Über den nativen
MCP-Server von OpenProject ist damit **nichts** gemessen: nicht seine Werkzeugliste, nicht sein
Authentifizierungsweg, nicht ob er die Berechtigungen des angemeldeten Nutzers durchsetzt, und
nicht ob er in openDesk 1.18.0 überhaupt eingeschaltet ist. Eine Aussage darüber wäre eine
Behauptung über fremden Code ohne Messung und fällt unter dieselbe Regel wie Annahme A7.

**Warum es trotzdem nicht liegen bleiben darf:** Der Fund berührt die Fragestellung dieser Phase
an zwei Stellen.

1. **OD-04, der Weg-0-Client in v2.0.** Die Phase vergleicht zwei Wege, auf denen *diese* ExApp
   Arbeitspakete für einen Nutzer liest. Wenn OpenProject selbst einen MCP-Endpunkt anbietet, gibt
   es einen dritten Weg, der in der Weg-0-gegen-Weg-1-Tabelle heute nicht vorkommt: der Assistent
   spricht beide Server nebeneinander, und diese ExApp braucht für OpenProject gar kein Werkzeug.
   Das ist keine Entscheidung dieses Plans, aber es ist eine, die vor OD-04 fallen sollte.
2. **OD-03, die Fragenliste für den ISV-Call am 14.09.** Ob ZenDiS den MCP-Endpunkt von
   OpenProject in openDesk eingeschaltet hat, mit welchem Authentifizierungsweg, und wie er sich
   zum souveränen Arbeitsplatz verhält, ist eine Frage mit Grund und gehört auf die Liste.

**Vorgeschlagene Behandlung:** eine Frage in Plan 17-08 (Fragenliste OD-03) und ein Absatz in
Plan 17-09 unter "Was diese Messung nicht beweist". Eine eigene Messung ist in dieser Phase
**nicht** vorgesehen und würde den Stufenschnitt aus Pitfall 1 aufweichen.

## DI-17-02: Der vorherige `refresh_token` stirbt erst mit dem ersten Gebrauch des neuen `access_token`

**Gefunden:** 2026-08-28, Plan 17-04, Task 2, bei der zweiten Gegenprobe zur Erneuerung.

**Gemessen und im Bericht in Abschnitt 2.2 belegt:** ein bereits eingelöster `refresh_token` liefert
beim Wiedergebrauch **200** und ein weiteres vollständig gültiges Tokenpaar, solange das aus ihm
entstandene `access_token` noch nie benutzt wurde. Zwei Ketten, unmittelbar hintereinander im selben
Lauf und damit ohne Zeitunterschied: Kette A benutzt das neue `access_token` einmal, danach ist der
alte `refresh_token` **400 invalid_grant**; Kette B benutzt es nicht, danach liefert derselbe alte
Wert **200**. Der passende Beleg aus der laufenden Instanz ist die Spalte `previous_refresh_token` auf
`oauth_access_tokens` (`/app/db/structure.sql:4383`).

**Warum das hier steht und nicht als Aufgabe:** Der Befund ist eine Eigenschaft von OpenProject und
verlangt in dieser Phase keine Zeile Code (D-12). Er ist aber eine Vorgabe für den Client, der in
**OD-04** entsteht, und zwar in zwei Richtungen.

1. **Wer erneuert, muss das neue `access_token` auch benutzen.** Ein Client, der auf Vorrat erneuert
   und das Ergebnis wegwirft, sammelt gültige Tokenpaare an, ohne dass eines der alten entwertet wird.
   Wer nach der Erneuerung sofort einen Aufruf mit dem neuen Token macht, schließt das von selbst.
2. **Ein Wiederholungsversuch nach einer verlorenen Antwort ist ungefährlich.** Genau dafür ist die
   aufgeschobene Entwertung gedacht, und das ist die gute Nachricht in diesem Befund: ein Client, dem
   die Antwort auf die Erneuerung verloren geht, darf sie mit demselben Wert wiederholen.

**Nicht gemessen:** ob es eine obere Zeitgrenze für den alten `refresh_token` gibt, und ob openDesk
diese Doorkeeper-Einstellung mitbringt oder abweicht. Beides ist **ungemessen** und keine Vermutung.

**Vorgeschlagene Behandlung:** ein Satz in Plan 17-09 unter Abschnitt 3 (API-Form, Vorarbeit für
OD-04). Keine Frage für den ISV-Call, weil sie nicht ZenDiS betrifft, sondern OpenProject.

## DI-17-03: Weg A wäre messbar, kostet aber zwei Eingriffe in die Messumgebung

**Gefunden:** 2026-08-28, Plan 17-05, Task 2, vor dem ersten Klick und deshalb rechtzeitig.

**Gemessen und im Bericht in 5.4 belegt:** der Ablagen-Assistent von OpenProject scheitert in dieser
Topologie am Namenscheck von `NextcloudCompatibleHostValidator`, nicht an der Erreichbarkeit. Alle
vier Namen, unter denen Nextcloud hier zu erreichen wäre, liefern `safe_ip? = nil`, die Erlaubnisliste
ist leer, und die zwei Netzaufrufe, die danach kämen, gelingen beide (200 und 200).

**Was eine Messung von Weg A kosten würde, so genau wie es ohne Versuch geht:**

1. `OPENPROJECT_SSRF__PROTECTION__IP__ALLOWLIST` in `compose.spike-opendesk.yml` setzen, mindestens
   `127.0.0.0/8` und `172.16.0.0/12`. Der Schlüssel trägt `writable: false`, ist also nicht in der
   Oberfläche setzbar; der OpenProject-Container muss dafür neu erzeugt werden.
2. Ein Name, der aus dem Browser des Entwicklers **und** serverseitig aus dem OpenProject-Container an
   dieselbe Nextcloud führt. Den gibt die Topologie heute nicht her: `caddy` löst nur innen auf,
   `127.0.0.1:8091` nur außen. Nötig wären ein Caddy-Site-Block auf `:8091`, ein `extra_hosts`-Eintrag
   und eine Trusted-Domain.

**Der unsichere Teil, ausdrücklich ungemessen:** `OpenProject.httpx` trägt den Filter mit
`safe_private_ranges` (`/app/lib/open_project.rb:68`), und `SsrfProtection` löst Namen über
`Resolv::DNS` auf, also **ohne** `/etc/hosts`. Ob ein Name mit öffentlichem A-Eintrag auf `127.0.0.1`
nach der Erlaubnisliste dann zur Adresse aus `extra_hosts` verbindet oder zur öffentlich aufgelösten,
ist nicht gemessen. Der Ausgang von Schritt 2 ist damit offen, und deshalb steht hier eine Kostenschätzung
und keine Anleitung.

**Warum es nicht in diesem Plan behandelt wurde:** D-03 verbietet Eingriffe, die über die Messung
hinausgehen, das Neuerzeugen des OpenProject-Containers würde den in 5.3 aufgebauten Grundzustand
riskieren, den 17-06 braucht, und der Owner hat am 28.08. ausdrücklich Variante B gewählt. Weg A steht
deshalb als `ungemessen` mit Grund und nicht als `verworfen`.

**Vorgeschlagene Behandlung:** ein Absatz in Plan 17-09 unter 2.5 (dort schon vorgemerkt) und, falls
der ISV-Call einen Bootstrap-Weg nennt, eine Frage in 17-08 danach, ob openDesk eine
SSRF-Erlaubnisliste setzt. Eine eigene Messung nur, wenn der Owner den Eingriff ausdrücklich freigibt.
