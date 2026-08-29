---
phase: 17-opendesk-spike
plan: 09
subsystem: bericht-abschluss-und-nachweise
tags: [spike, opendesk, od-01, od-02, od-03, bericht, ungemessen, geheimnisgriff, produktionsbaum, d-02, d-03, d-12]
requires:
  - "17-01: Abschnitt 1 samt 1.4 und den vorab festgelegten Entscheidungskriterien, aus denen die Form von 2.4 stammt"
  - "17-02: S0 auf 33.0.7 und die SSRF-Messung (D-06), aus denen 2.4 den Erreichbarkeits- und den Entwurfsteil zieht; dazu die Wiederherstellungsnotiz zu compose.exapp.yml"
  - "17-03: Stufe B, der Grundzustand des Zwei-Konten-Negativbeweises und die Aufbaunotiz in 5.3"
  - "17-04: Weg 1 vollstaendig (PKCE, expires_in 7200, Erneuerung ohne Cookie, D-05), die Rohwerte fuer 5.0 Zeilen 24 bis 37"
  - "17-05: S1, S2, der Capability-Befund, die Egress-Kontrollmessung und der Eingriff allow_local_remote_servers"
  - "17-06: S3, S4 und S6 samt 5.5, die Rohwerte fuer 5.0 Zeilen 11 bis 17 und 21 bis 23"
  - "17-07: S5a bis S5c samt 5.6, die Rohwerte fuer 5.0 Zeilen 18 bis 20"
  - "17-08: Abschnitt 4 mit neun numerierten Fragen, auf die 2.4 und 2.5 verweisen statt zu wiederholen"
  - "deferred-items.md DI-17-01 bis DI-17-05: fuenf Funde, die in 2.5 oder in den Raendern eine Zeile bekommen mussten"
provides:
  - "docs/spike-opendesk.md Abschnitt 2.4: die Folgerung, jeder Satz an eine Messzeile aus 2.1, 2.2 oder 2.3 gebunden, mit der Bedingung (Betriebsart) im selben Satz"
  - "docs/spike-opendesk.md Abschnitt 2.5: 18 Zeilen, jeder Ungemessen-Punkt der Phase mit Zustand, Grund und Kostenschaetzung an einer Stelle"
  - "docs/spike-opendesk.md Abschnitt 5.0: 42 Rohwertzeilen in der Reihenfolge S0 bis S6, dann Weg 1, dann SSRF, je mit Aufruf, Status, Content-Type, Antwortform, Koerper und Konto"
  - "docs/spike-opendesk.md Abschnitt 'Reproduktion': die Befehlsfolge der Messumgebung samt Profilen, Oberflaechenschritten und down -v"
  - "docs/spike-opendesk.md Abschnitt 'Was diese Messung nicht beweist': fuenf Punkte, in denen der lokale Aufbau openDesk nicht reproduziert, drei protokollierte Eingriffe, DI-17-01"
  - "docs/spike-opendesk.md Abschnitt 'Der Produktionsbaum nach dieser Phase': vier Nachweise zu ROADMAP-Erfolgskriterium 5"
  - "Kopfblock auf Status done mit Ergebnis-Halbsatz und Entscheidungsdatum 2026-08-29; keine Zeile 'noch nicht gemessen' mehr in der Datei"
  - "Abgeraeumte Messumgebung: kein Container, kein Band und kein Netz mit dem Praefix nc-mcp-spike-od"
  - "Wieder benutzbare ExApp-Topologie aus compose.exapp.yml, gegengeprobt mit 401 auf der mcp-Route"
affects:
  - "OD-04 (v2.0) bekommt die Folgerung samt ihrer Bedingung und weiss, dass file-links und der Pfad nextcloud_hub ungemessen sind"
  - "Der ISV-Call am 14.09. bekommt mit 2.5 eine Liste, die zu Abschnitt 4 passt, ohne eine Frage doppelt zu fuehren"
  - "Phase 18 findet die ExApp-Topologie aus compose.exapp.yml wieder laufend vor, mit 0.1.11 registriert und aktiviert"
  - "Der Produktionsbaum ist belegt unveraendert: 15712 Bytes ueber 21 Werkzeuge gegen ein Budget von 18000, wie am 2026-08-28"
tech-stack:
  added: []
  patterns:
    - "Eine Folgerung wird an Messzeilen gebunden, indem jeder Satz auf 2.1, 2.2 oder 2.3 zeigt; wo die Messung nicht weit genug reicht, steht das im selben Satz und nicht in einer Fussnote. Ein Leser kann so nicht uebersehen, wo das Urteil aufhoert und die offene Frage anfaengt"
    - "Eine Folgerung mit Bedingung ist ehrlicher als eine ohne: 'laeuft es im Modus oauth2, dann X; laeuft es im Modus oidc, dann Y und fuer den dritten Pfad kein Messwert' sagt genau so viel, wie gemessen wurde"
    - "Alle Ungemessen-Punkte an einer Stelle sammeln, mit der Spalte 'Was es braeuchte': das macht aus einer Liste von Luecken eine Liste von Aufgaben mit Preis, und niemand muss sie beim Lesen zusammensuchen"
    - "Rohwerte doppelt ordnen: nach Plaenen (5.1 bis 5.6, so sind sie entstanden) und nach Behauptungen (5.0, so werden sie geprueft). Der Verweis in der Spalte Stelle verbindet beide, ohne einen Wert zweimal zu fuehren"
    - "Der Geheimnisgriff laeuft nicht nur nach Mustern, sondern gegen jeden Wert der Verbindungsdatei: 34 Werte, 3700 Treffer, und der Nachweis besteht darin, dass alle 3700 auf 12 nicht geheime Werte entfallen und alle 22 geheimen null Treffer haben"
    - "Ein global benannter Container gehoert zur Messumgebung, auch wenn er ihren Praefix nicht traegt: down -v allein raeumt ihn nicht ab, und der Nachweis 'kein Band mit Praefix' haette ihn uebersehen"
key-files:
  created:
    - ".planning/phases/17-opendesk-spike/17-09-SUMMARY.md"
  modified:
    - "docs/spike-opendesk.md"
decisions:
  - "2.4 faellt eine Folgerung, aber mit Bedingung: laeuft integration_openproject im Modus oauth2, traegt Weg 0 gemessen vollstaendig und billiger; laeuft es im Modus oidc, traegt er so lange wie das zwischengespeicherte Token gilt, und fuer die Zeit danach gibt es auf zwei von drei Pfaden einen Bruch und auf dem dritten keinen Messwert. Ein unbedingter Satz haette Frage 7 uebersprungen"
  - "Der Satz 'Weg 0 traegt unter OIDC nicht' ist ausdruecklich nicht geschrieben worden: er wuerde um genau den Pfad nextcloud_hub ueber die Messung hinausgehen, der als einziger sitzungsfrei ist und der angelaufen, aber nicht zu Ende gemessen ist (DI-17-05)"
  - "file-links steht in 2.4 im Begruendungssatz der Wahl und nicht in einer Fussnote: wer Weg 0 waehlt, waehlt ihn mit einer unerprobten Route, die zugleich das Unterscheidungsmerkmal aus research/FEATURES.md ist (DI-17-04)"
  - "Abschnitt 5 ist nicht umnummeriert worden. Die vorhandenen Unterabschnitte 5.1 bis 5.6 tragen Verweise aus dem ganzen Bericht; die geforderte Reihenfolge S0 bis S6, Weg 1, SSRF steht deshalb als neue Tabelle 5.0 davor, mit einer Spalte Stelle auf den ausfuehrlichen Rohwert"
  - "Wo ein Content-Type nicht protokolliert wurde, steht 'nicht protokolliert' und kein nachtraeglich erschlossener Wert. Ein erschlossener Content-Type waere genau die Art Wert, die dieser Bericht sonst als Vermutung zurueckweist"
  - "Zwei Behauptungen tragen den Vermerk 'nicht gegengeprobt' (die 401 der ExApp-Route in 1.3 und die 415 an /oauth/token in 2.2), statt sie stillschweigend als gegengeprobt mitlaufen zu lassen"
  - "Der stehengebliebene ExApp-Container nc_app_mcp_connector ist als Teil der Messumgebung entfernt worden, obwohl er den Praefix nicht traegt: er hing als einziger noch am Spike-Netz und blockierte dessen Entfernung. Ohne diesen Schritt waere die ExApp-Topologie mit 503 statt 401 zurueckgeblieben"
metrics:
  duration: 35 min
  completed: 2026-08-29
---

# Phase 17 Plan 09: Der Bericht ist fertig, der Produktionsbaum steht still Summary

Der Spike-Bericht ist abgeschlossen: 2.4 zieht die Folgerung aus Messzeilen und nicht aus Argumenten, 2.5 sammelt achtzehn Ungemessen-Punkte mit Grund und Kostenschätzung an einer Stelle, 5.0 führt zweiundvierzig Rohwerte in der Reihenfolge der Behauptungen, und die Ränder stehen vollständig da. Kein Geheimnis ist im Repositorium gelandet, die Messumgebung ist restlos abgeräumt, die vorherige ExApp-Topologie läuft wieder, und der ausgelieferte Produktionsbaum ist mit vier Läufen belegt unverändert.

## Was entstanden ist

**Abschnitt 2.4, die Folgerung.** Jeder Satz zeigt auf eine Messzeile aus 2.1, 2.2 oder 2.3. Die Reihenfolge ist bindend gewesen und ist eingehalten: was Weg 0 gemessen leistet (S1 mit 200 und `ocs.data = http://op.localtest.me:8082` als `alice`, S2 mit `carol` 401 gegen `alice` 200/1702 Bytes und `bob` 200/1700 Bytes, S3 mit 0 gegen 1 Treffer und der Demo-Gegenprobe 14 ohne die 38, S4 zweimal mit gestelltem und mit natürlich verstrichenem Ablauf, S6 mit 4746 Bytes über 49 Relationen und 24 Felder), wo er kippt und wo er ungemessen bleibt, was Weg 1 leistet und kostet, und was die SSRF-Messung für einen künftigen zweiten Zugriffsweg bedeutet.

**Die Folgerung selbst trägt ihre Bedingung im selben Satz.** Im Modus `oauth2` trägt Weg 0 gemessen vollständig und ist der billigere der beiden; im Modus `oidc` trägt er gemessen genau so lange, wie das zwischengespeicherte Token gilt, und für die Zeit danach hat diese Phase auf zwei der drei Pfade einen gemessenen Bruch und auf dem dritten keinen Messwert. Weg 1 trägt in beiden Fällen, weil er die Betriebsart nicht berührt, und kostet vier bezifferte Posten. Eine Wahl trifft der Bericht nicht: sie ist OD-04 und fällt nach dem ISV-Call.

**Der Satz, der nicht geschrieben wurde.** "Weg 0 trägt unter OIDC nicht" steht nirgends. Er würde um genau den Pfad `nextcloud_hub` über die Messung hinausgehen: der ist der einzige sitzungsfreie, sein Listener läuft nachweislich und stellt keine Sitzungsfrage, und er bricht hier an `oidc app is not installed`, weil die Server-App fehlt, die Nextcloud selbst zum Anbieter macht. Der Bericht sagt das in 2.4 und noch einmal in den Rändern.

**Die unerprobte Stelle steht im Begründungssatz und nicht in einer Fußnote.** `GET /api/v1/work-packages/{id}/file-links` ist die einzige Route der Fläche, die eine Id eines Arbeitspakets annimmt, und zugleich das Unterscheidungsmerkmal aus `research/FEATURES.md`. Belegt sind Existenz und Signatur aus `appinfo/routes.php` 3.1.1; gemessen ist an ihr nichts, weil `GET /api/v3/storages` gemessen `total 0` und `count 0` antwortet. Wer Weg 0 wählt, wählt ihn mit dieser offenen Stelle.

**Abschnitt 2.5, achtzehn Zeilen mit vier Spalten.** Punkt, Zustand, Grund, was es bräuchte. Darin: Weg A des Einrichtungswegs (DI-17-03), `file-links` (DI-17-04), der Pfad `nextcloud_hub` (DI-17-05), die Datenlieferung mit Sitzung, die Betriebsart von openDesk (Frage 7), `app_api` im openDesk-Image (Frage 6), die SSRF-Erlaubnisliste von openDesk, der Termin von Nextcloud 34 (Frage 5), das ZenDiS-Aufnahmeverfahren (Frage 1), die fehlende Oberflächenvorlage für `kubernetes-install`, der Keycloak-Umleitungsschritt in Weg 1, die Scope-Pflicht seit OpenProject 16.0.0, die Zeitgrenze des alten `refresh_token` (DI-17-02), der Sprachwechsel der Doorkeeper-Meldung, der native MCP-Endpunkt von OpenProject (DI-17-01), elf nicht ausgelöste OCS-Routen, das abweichende Seed-Passwort und der Egress in einer Behördeninstallation. Kein Punkt steht als `verworfen`, und keiner ist stillschweigend weggefallen.

**Abschnitt 5.0, zweiundvierzig Rohwertzeilen in der Reihenfolge der Behauptungen.** S0 bis S6, danach Weg 1, danach die SSRF-Grenze, je mit Aufruf ohne Kopfzeilenwerte, Statuscode, Content-Type, Antwortform, höchstens 120 Zeichen Körper und dem Konto. Die nach Plänen geordneten Unterabschnitte 5.1 bis 5.6 sind unberührt geblieben, weil der ganze Bericht auf ihre Nummern verweist; die neue Tabelle steht davor und verbindet beide über eine Spalte Stelle.

**Abschnitt Reproduktion.** Die Befehlsfolge samt beider `export`, dem Bootstrap, `set -a && . ./.env.spike-opendesk && set +a`, den Profilen `op` und `oidc`, den zwei Schritten, die nur über eine Oberfläche gehen (mit Verweis auf 17-03 und 17-05), und `down -v` samt der Begründung, warum das `-v` für Keycloak Pflicht ist. Dazu der Hinweis, dass die Verbindungsdatei git-ignoriert ist und `.env.spike-opendesk.example` nur die Variablennamen führt.

**Abschnitt Was diese Messung nicht beweist.** Die Wegwerf-Instanz auf SQLite und die gepinnten Fassungen; fünf benannte Punkte, in denen der lokale Aufbau openDesk nicht reproduziert; die Egress-Messung, die über eine Behördeninstallation nichts sagt; die Zahlen von `community.openproject.org` als Kontext; die drei Eingriffe (`allow_local_remote_servers`, das per `rails runner` gesetzte Admin-Passwort mit nicht untersuchter Ursache, Keycloak und `user_oidc` ausschließlich für S5) und die zwei aus 17-07 (Loglevel `debug`, `allow_insecure_http`).

## Die drei Anforderungen, je mit dem Ort ihres Nachweises

| Anforderung | Ort des Nachweises im Bericht | Zustand |
|-------------|-------------------------------|---------|
| **OD-01** (Installierbarkeit in einer openDesk-Umgebung) | Abschnitt 1 vollständig: 1.1 App Store, 1.2 Deploy-Daemon und Kubernetes, 1.3 Versionspin samt S0 auf 33.0.7, 1.4 "Was offen bleibt" mit der Antwort in drei Sätzen | **erfüllt, mit ausgewiesenen ungemessenen Punkten in 2.5.** Alle drei Hürden sind aus openDesk-Quellen belegt, der Ein-Klick-Nachweis steht jetzt auf der gepinnten Hauptversion 33.0.7 statt auf 34.0.3, und was der Pin für die geerbten Nachweise bedeutet, steht ausdrücklich in 1.3. Vier Punkte bleiben ungemessen (Fragen 1, 5, 6 und die Oberflächenvorlage) und sind je als offene ISV-Call-Frage markiert |
| **OD-02** (Weg 0 und Weg 1 mit Messwerten nebeneinander, die Entscheidung als Folge der Messung) | Abschnitt 2 vollständig: 2.1 (S0 bis S6), 2.2 (Weg 1), 2.3 (SSRF), 2.4 (Folgerung), 2.5 (Ungemessen), Rohwerte in 5.0 | **erfüllt, mit ausgewiesenen ungemessenen Punkten in 2.5.** Beide Wege stehen mit Messwerten nebeneinander, alle vier wörtlich verlangten Punkte sind gemessen (PKCE, Token-Lebensdauer, Erneuerung ohne Browsersitzung, SSRF-Grenze gegen den internen Dienstnamen), und 2.4 folgert ausschließlich aus Messzeilen. Die Folgerung trägt eine Bedingung (Betriebsart, Frage 7), und drei Punkte bleiben ungemessen: Weg A, `file-links`, der Pfad `nextcloud_hub` |
| **OD-03** (Fragenliste für den 14.09.) | Abschnitt 4, neun Fragen, geschlossen in Plan 17-08 | **erfüllt.** Dieser Plan hat daran nichts geändert; 2.4 und 2.5 verweisen auf die Nummern 1, 5, 6 und 7, statt Fragen zu wiederholen |

Keine Anforderung ist als erfüllt gemeldet, deren Nachweis im Bericht fehlt. **Warum OD-01 und OD-02 trotz offener Punkte als erfüllt und nicht als `teilweise` gemeldet sind:** beide verlangen im Wortlaut, dass gemessen und schriftlich belegt wird, und OD-02 zusätzlich, dass die Entscheidung auf der Messung fällt und nicht auf einem Argument. Keine der beiden verlangt die Abwesenheit offener Punkte, und ROADMAP-Erfolgskriterium 3 verlangt ausdrücklich das Gegenteil: ein nicht gemessener Weg soll als `ungemessen` dastehen. Genau das leistet 2.5. Eine Meldung als `teilweise` würde einen Maßstab anlegen, den der Anforderungstext nicht setzt, und die Kennzeichnung offener Punkte in einen Mangel umdeuten.

## Der Geheimnisgriff, mit Zahlen

**Griff 1** (`eyJ`, Bearer mit Wert, `refresh_token=`, `client_secret=`, `code_verifier=`, `AUTHORIZATION-APP-API:` mit Wert, über `docs compose.spike-opendesk.yml deploy scripts .gitignore`): **26 Treffer, kein einziger mit einem Wert.** Verteilung: 6 in `docs/oauth-setup.md`, 8 in `docs/spike-discovery.md`, 3 in `docs/exapp-install.md`, 1 in `docs/client-setup.md`, je 3 in den beiden Bootstrap-Skripten, 1 in `docs/spike-opendesk.md` und 1 in `scripts/oauth_flow_check.py`. Alle sind erklärende Sätze über das Bearer-Schema, Kommentare der Bootstrap-Skripte ("bearer equivalent"), die wörtliche Testzeichenkette `Bearer TESTBEARERTOKEN` aus dem Quelltext von `integration_openproject` und ein Schlüsselwortargument `client_secret=client_secret` (Abweichung 2).

**Griff 2** (`client_credentials`, `GLOBAL__BASIC__AUTH`, `apikey:`): **11 Treffer, alle erwartet und alle in `docs/spike-opendesk.md`.** Vier auf `client_credentials`, davon einer im wörtlichen Zitat des Serverdokuments und drei im Absatz, der erklärt, warum dieser Grant ausgeschlossen ist; sieben auf den Platzhalter `apikey:<OP_API_TOKEN>`, also den als Aufbau gekennzeichneten Messweg. `GLOBAL__BASIC__AUTH` kommt **null** Mal vor.

**Der Griff, den der Plan nicht verlangt hat und der schärfer ist als beide: jeder Wert der Verbindungsdatei gegen den ganzen verfolgten Baum.** 34 Variablen mit einem Wert von mindestens vier Zeichen, je ein `git grep -F` über das Repositorium. Ergebnis: **3710 Treffer insgesamt, alle auf zwölf nicht geheime Werte, und null auf jeden der zweiundzwanzig geheimen.**

| Wert | Treffer | Einordnung |
|------|---------|------------|
| `APP_SECRET` (64), `HP_SHARED_KEY` (64), `SECRET_KEY_BASE` (128), `KC_CLIENT_SECRET` (86), `OP_API_TOKEN` (70), beide App-Passwörter (je 72), `NC_OP_CLIENT_ID`/`_SECRET`, `OP_OAUTH_CLIENT_ID`/`_SECRET` (je 43), alle sechs Wegwerf-Passwörter, `NC_CAROL_PASSWORD`, `OP_ADMIN_PASSWORD`, die vier Dateinamen der Testfreigaben | **je 0** | kein geheimer Wert steht in einer verfolgten Datei |
| `APP_ID` (`mcp_connector`), `APP_VERSION` (`0.1.11`), `KC_REALM` (`spike`), `NC_MCP_TEST_USER` (`alice`), `NC_MCP_URL`, `NC_MCP_EXAPP_BASE`, `NC_MCP_PUBLIC_URL`, beide Talk-Raumnamen, `KC_BOOTSTRAP_ADMIN_USERNAME` (`kcadmin`) | 3702 | Bezeichner, Fassungsnummer, Loopback-Adressen und Namen. Keiner davon ist ein Geheimnis, und jeder steht schon seit früheren Phasen im Repositorium |
| `NC_MCP_TEST_PASSWORD` (`alice-...`), `NC_MCP_TEST_PASSWORD2` (`bob-...`) | 8 | die **Vorgabewerte der Bootstrap-Skripte selbst**, im Repositorium seit Commit `cd0e520` vom 2026-08-15 (Plan 02-04), für Wegwerf-Instanzen auf 127.0.0.1. Sie sind kein Fund dieser Phase und stehen in `scripts/bootstrap_exapp.sh:97-98`, `scripts/bootstrap_spike_opendesk.sh:93-94`, `scripts/bootstrap_test_nc.sh:24-25` und einem Testfall |

Kein echter Wert war zu entfernen, und es ist deshalb auch keiner entfernt worden.

## Der Produktionsbaum, vier Nachweise

| # | Nachweis | Ergebnis |
|---|----------|----------|
| 1 | `git status --short src/ appinfo/ pyproject.toml uv.lock` und `git diff --stat 90d2f68..HEAD -- src appinfo pyproject.toml uv.lock` | beide **leer**. `90d2f68` (`docs(state): record phase 17 context session`) ist der letzte Commit vor `docs(17): research openDesk spike domain` (`00abdcf`). Die Phase hat 33 Dateien geändert, keine unter `src/` oder `appinfo/` |
| 2 | `uv run python scripts/check_tool_budget.py` | `tools/list: 15712 bytes, 21 tools, budget 18000`, Zeichen für Zeichen wie am 2026-08-28. Keine Grenze angehoben |
| 3 | `uv run pytest -q` | **2813 passed, 163 deselected** in 72,69 s. Keine Test-Datei entstanden |
| 4 | `uv run ruff check .` und `uv run ruff format --check .` | `All checks passed!` und `202 files already formatted` |

## Die Messumgebung, abgeräumt

`docker compose -f compose.spike-opendesk.yml --profile op --profile oidc down -v` hat die sechs Container mit dem Präfix `nc-mcp-spike-od` und alle fünf Bände entfernt. Danach gilt gemessen: kein Container, kein Band und kein Netz mit diesem Präfix.

**Ein siebter Container trug den Präfix nicht.** Der Deploy-Daemon benennt den ExApp-Container global `nc_app_<appid>`. Nach dem `down -v` lief er weiter, hing als einziger noch am Netz `nc-mcp-spike-od-net` (dessen Entfernung deshalb mit `Resource is still in use` scheiterte) und trug das Bild aus der Spike-Registry. Entfernt mit `docker rm -f nc_app_mcp_connector`, danach `docker network rm nc-mcp-spike-od-net`.

**Die vorherige ExApp-Topologie ist wieder benutzbar**, wie es die Wiederherstellungsnotiz aus 17-02 verlangt: `compose.exapp.yml` läuft wieder mit fünf gesunden Containern, `occ app_api:app:list` nennt `mcp_connector (MCP Connector): 0.1.11 [enabled]`, der Container hängt am Netz `nc-mcp-exapp-net`, und ein `POST http://127.0.0.1:8081/exapps/mcp_connector/mcp` ohne Token antwortet **401** statt der 503 davor.

**Fremde Projekte sind nicht angefasst worden:** `findling-nextcloud` läuft unverändert seit 13 Tagen, `nc-mcp-test` seit zwei Wochen, `infranode-redis-dev` liegt unverändert seit zwei Monaten gestoppt.

## Abweichungen vom Plan

**1. [Rule 3 - Blockierend] Der stehengebliebene ExApp-Container und die Neuregistrierung**
- **Gefunden bei:** Task 3, nach dem `down -v`
- **Problem:** `down -v` allein hat die Messumgebung nicht restlos abgeräumt. `nc_app_mcp_connector` lief weiter, hielt das Spike-Netz fest und blockierte die Route der wiederhergestellten Topologie: `POST http://127.0.0.1:8081/exapps/mcp_connector/mcp` antwortete **503**. Der idempotente `bootstrap_exapp.sh` hat den Container nicht neu ausgerollt, weil `ensure_exapp()` bei vorhandener Registrierung abbricht (`scripts/bootstrap_exapp.sh:1201-1204`) und die Registrierung in der Nextcloud der ExApp-Topologie die Phase überdauert hatte.
- **Fix:** Container und Netz entfernt, danach den im Skript selbst dokumentierten Weg gegangen (`scripts/bootstrap_exapp.sh:1465`): `occ app_api:app:unregister mcp_connector --force`, dann `bash scripts/bootstrap_exapp.sh`. Kein `git clean`, kein Eingriff in fremde Projekte, kein Band der ExApp-Topologie angefasst.
- **Gegenprobe:** die mcp-Route antwortet **401** statt 503, und `occ app_api:app:list` nennt `0.1.11 [enabled]` statt der vorher registrierten `0.1.9`.
- **Commit:** `ad256bb`

**2. [Befund, nicht behoben] Der Geheimnisgriff des Plans hat einen Falschtreffer, und er ist Bestand**
- **Gefunden bei:** Task 2, beim Lauf der `<verify>`-Kette
- **Sachverhalt:** Das Muster `client_secret=[A-Za-z0-9_-]{8}` trifft auch den Bezeichner selbst. `scripts/oauth_flow_check.py:450` schreibt `client_secret=client_secret`, also ein Schlüsselwortargument, das eine Variable weiterreicht und keinen Wert nennt. Die Zeile stammt aus Commit `edb2571` vom 2026-08-16 (Phase 03) und ist von dieser Phase nicht angefasst worden.
- **Behandlung:** **nicht geändert.** Eine Umbenennung wäre eine Änderung an Bestandscode ohne Anlass und läge außerhalb des Auftrags dieses Plans. Der Griff ist stattdessen mit ausgeschlossenem Falschtreffer nachgefahren: **0 verbleibende Treffer**. Der Befund steht hier, damit er beim nächsten Lauf nicht als neu gilt.
- **Datei:** `scripts/oauth_flow_check.py:450`, unverändert

**3. [Befund, nicht behoben] Die automatisierte Prüfung von Task 1 prüft die Überschriften anders, als sie aussieht**
- **Gefunden bei:** Task 1, beim Lauf der `<verify>`-Kette
- **Sachverhalt:** `grep -v '^#' | grep -q "### 2.4"` schließt jede Zeile aus, die mit `#` beginnt, also auch die gesuchte Überschrift selbst. Die Prüfung verlangt damit eine Zeile, die `### 2.4` **erwähnt**, ohne eine Überschrift zu sein.
- **Behandlung:** Der Bericht trägt in 2.4 einen Satz, der die beiden Überschriften als Ankerpunkte benennt und vor dem Umbenennen warnt, weil 1.4, 3.3 und Abschnitt 4 namentlich auf sie zeigen. Das ist inhaltlich richtig (Abschnitt 4 führt denselben Hinweis für die Fragennummern) und erfüllt die Prüfung, ohne den Text zu verbiegen. Zusätzlich ist `grep -q "^### 2.4"` gefahren worden, also die Prüfung, die offensichtlich gemeint war: ebenfalls grün.
- **Commit:** `21fb6d0`

**4. [Rule 2 - Projektregel] Gedankenstriche aus den vom SDK geschriebenen STATE.md-Zeilen entfernt**
- **Gefunden bei:** dem Zustandsschreiben nach Task 3
- **Sachverhalt:** `state.advance-plan` schreibt in die Statuszeile `Phase complete`, `ready for verification` und dazwischen einen Gedankenstrich (U+2014, hier umschrieben statt gesetzt). Die Projektregel verbietet U+2014 und U+2013 ausnahmslos.
- **Behandlung:** Die drei Zeilen zur laufenden Phase (Current focus, Current Position, Status) tragen jetzt Komma statt Gedankenstrich und sind zugleich sachlich richtig gestellt (`abgeschlossen` statt `EXECUTING`). Die stale Zeile `Naechster Schritt`, die noch auf 16-02 zeigte, ist auf die Verifikation von Phase 17 aktualisiert. Der eine verbliebene Gedankenstrich in Zeile 513 ist ein Bestandseintrag aus Phase 09 und außerhalb des Auftrags dieses Plans.
- **Datei:** `.planning/STATE.md`

Sonst keine. Kein Produktionscode, keine neue Datei außerhalb von `.planning/`, keine Änderung an den Abschnitten 1, 3 und 4 des Berichts.

## Gates

| Gate | Ergebnis |
|------|----------|
| `grep -q "noch nicht gemessen" docs/spike-opendesk.md` | **0 Treffer**, keine Zeile mehr offen |
| Kein Weg als `verworfen` bezeichnet | **0 Treffer** auf `Weg [01] (ist\|wird) verworfen`; das Wort steht ausschließlich in den Regelsätzen, die es untersagen |
| `^### 2.4`, `^### 2.5`, `^## Was diese Messung nicht beweist`, `^## Reproduktion`, `^## Der Produktionsbaum nach dieser Phase` | alle vorhanden |
| Verweis von 2.4 auf die Messabschnitte | `Abschnitt 2.1`, `Abschnitt 2.2` und `Abschnitt 2.3` je namentlich, dazu S1 bis S6 mit ihren Zahlen |
| Beide `git grep`-Griffe | kein Treffer mit einem echten Wert; Zahlen und Einordnung oben |
| Griff über jeden Wert der Verbindungsdatei | 34 Werte geprüft, 22 geheime mit **je 0** Treffern |
| `check_tool_budget.py` | `15712 bytes, 21 tools, budget 18000` |
| `uv run pytest -q`, `ruff check .`, `ruff format --check .` | grün, grün, grün |
| `git status --short src/ appinfo/ pyproject.toml uv.lock` | **leer** |
| Kein Band, kein Container, kein Netz mit Präfix `nc-mcp-spike-od` | bestätigt mit `docker ps -a`, `docker volume ls`, `docker network ls` |
| Gedankenstriche (U+2014, U+2013) | **0 Treffer** im Bericht |
| Vokabular-Gate (das Wort aus `FORBIDDEN_VOCABULARY`, hier umschrieben) | **0 Treffer** in `docs/spike-opendesk.md` |

## Was dieser Plan nicht getan hat

Er hat nichts Neues gemessen: jede Zahl in 2.4, 2.5 und 5.0 stammt aus einem der Pläne 17-02 bis 17-07 und ist mit ihrer Stelle belegt. Er hat keine Wahl zwischen Weg 0 und Weg 1 getroffen, weil die OD-04 gehört. Er hat keinen Punkt zu `verworfen` erklärt, auch keinen, der bequem gewesen wäre. Er hat keine Zeile Produktionscode angefasst, kein Paket gezogen und keine Grenze angehoben. Und er hat nichts gesendet.

## Self-Check: PASSED

- `docs/spike-opendesk.md`, Abschnitt `### 2.4`: FOUND
- `docs/spike-opendesk.md`, Abschnitt `### 2.5` mit 18 Tabellenzeilen: FOUND
- `docs/spike-opendesk.md`, Abschnitt `### 5.0` mit 42 Rohwertzeilen: FOUND
- `docs/spike-opendesk.md`, Abschnitt `## Reproduktion`: FOUND
- `docs/spike-opendesk.md`, Abschnitt `## Was diese Messung nicht beweist`: FOUND
- `docs/spike-opendesk.md`, Abschnitt `## Der Produktionsbaum nach dieser Phase`: FOUND
- Kopfblock `Status: done` und `Entscheidungsdatum: 2026-08-29`: FOUND
- Commit `21fb6d0` (2.4, 2.5, Ränder, Kopf): FOUND
- Commit `34ffa36` (5.0, Reproduktion, Geheimnisgriff): FOUND
- Commit `ad256bb` (Produktionsbaum, Abräumen): FOUND
