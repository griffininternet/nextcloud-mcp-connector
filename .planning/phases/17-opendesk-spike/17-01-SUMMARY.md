---
phase: 17-opendesk-spike
plan: 01
subsystem: docs
tags: [spike, opendesk, od-01, installierbarkeit, appapi, kubernetes]
requires: []
provides:
  - "docs/spike-opendesk.md mit Kopfblock, vorab festgelegten Entscheidungskriterien und Gliederung nach D-09"
  - "OD-01 aus Quellen beantwortet: drei Hürden belegt, vier offene Punkte als ISV-Call-Fragen markiert"
  - "Geheimnisregel (Pitfall 7) steht in Abschnitt 5, bevor der erste Messwert entsteht"
affects:
  - "Plan 17-02 füllt Messteil S0 in 1.3 und den Kopfblock aus der laufenden Instanz"
  - "Plan 17-08 füllt Abschnitt 4 und muss die Fragen 1, 5, 6, 7 tragen, weil 1.4 namentlich darauf verweist"
  - "Plan 17-09 füllt 2.4, 2.5, Abschnitt 3 und Was diese Messung nicht beweist"
tech-stack:
  added: []
  patterns:
    - "Bericht nach dem Muster von docs/spike-mail.md: Kopf mit gelesenen Fassungen, vorab festgelegtes Kriterium, Behauptung/Messweg/Messwert, Gegenprobe"
    - "Kein Zitat ohne Repository, Tag, Datei und Zeile; jeder Abruf vor dem Schreiben selbst durchgeführt (Regel aus context_agent#230)"
key-files:
  created:
    - "docs/spike-opendesk.md"
  modified: []
decisions:
  - "Die Kubernetes-Aussage wird in der korrigierten Fassung geführt: nicht 'AppAPI kann kein Kubernetes', sondern auf app_api 33 existiert kubernetes-install nicht und auf app_api 34 existiert es; damit ist OD-01 eine Terminfrage an ZenDiS und keine Absage"
  - "Versionspin und Kubernetes-Hürde sind dieselbe Hürde und fallen mit demselben Schritt (openDesk auf Nextcloud 34 oder höher); der Bericht führt sie deshalb zusammen und nicht als zwei Absagen"
  - "Die Zielumgebung wird als ungetestet geführt, nicht als unzulässig: appinfo/info.xml Zeile 235 erlaubt min-version 32 bis max-version 34, aber alle Nachweise dieses Projekts stehen auf 34.0.x"
  - "Die Betriebsart von integration_openproject in openDesk bleibt unbehauptet: der Bootstrap-Job ist Indiz und nicht Beleg, die Frage geht als Frage 7 an den ISV-Call"
  - "Die Formulierung 'manual-install ist ausdrücklich für Entwicklung' wird nicht geführt, weil sie auf der heutigen Nextcloud-Doku-Seite nicht mehr auffindbar ist; der Bericht führt nur die aufgezählten Werte der occ-Hilfe, weil die im Quellcode stehen"
metrics:
  duration: 18 min
  completed: 2026-08-28
---

# Phase 17 Plan 01: OD-01 aus Quellen und Berichtsgerüst Summary

`docs/spike-opendesk.md` entsteht mit Kopfblock, vorab festgelegten Entscheidungskriterien und vollständigem Abschnitt 1: die drei Installierbarkeits-Hürden sind je mit Repository, Tag, Datei, Zeile und wörtlichem Zitat belegt, die vier Rest-Unbekannten stehen namentlich als ISV-Call-Fragen.

## Was entstanden ist

**`docs/spike-opendesk.md`**, 207 Zeilen, sieben `## `-Überschriften in der von D-09 verlangten Reihenfolge: Entscheidungskriterien, 1. Installierbarkeit, 2. Nutzeridentität, 3. API-Form, 4. Fragenliste, 5. Rohmesswerte, Was diese Messung nicht beweist. Abschnitte 2 bis 5 sind benannte, noch leere Gliederung mit je einer Zeile `noch nicht gemessen, Plan 17-NN`.

Drei Dinge stehen bewusst vor dem ersten Messwert:

1. **Die Antwortform als Kriterium**, nicht der Statuscode. Kein Schritt des Berichts prüft auf 200, weil eine 401 aus `validatePreRequestConditions()` antwortender App-Code ist. Übernommen aus `docs/spike-mail.md`, wo der Fehler "auf 200 prüfen" einmal schon verhindert wurde.
2. **Die Definitionen von `gemessen` und `ungemessen`.** `gemessen` verlangt vier Bestandteile, darunter den Nutzernamen, unter dem der Aufruf lief. `verworfen` ist ausdrücklich kein zulässiges Urteil (D-03, ROADMAP-Erfolgskriterium 3); das Wort kommt im Bericht nur in diesem Verbot vor.
3. **Die Geheimnisregel** als Kopf von Abschnitt 5, inklusive der Begründung, warum ein Wert des Headers `AUTHORIZATION-APP-API` genauso heikel ist wie `APP_SECRET` selbst (Base64 von `<user>:<APP_SECRET>`). Damit steht die Regel im Text, bevor in Plan 17-02 die erste Antwort protokolliert wird (T-17-01).

## Die drei Hürden, alle selbst abgerufen

Jeder Beleg wurde am 2026-08-28 vor dem Schreiben selbst geholt, ohne Anmeldung, an einem festen Tag. Nichts ist aus 17-RESEARCH.md übernommen, ohne dass der Abruf es bestätigt hat.

| Hürde | Beleg | Messwert des Abrufs |
|-------|-------|---------------------|
| 1: App Store aus | `bmi/opendesk/deployment/opendesk` `v1.18.0`, `helmfile/apps/nextcloud/values-nextcloud-management.yaml.gotmpl`, `appstore: enabled: false` Zeile 79 bis 80 | HTTP 200, 11288 Bytes; Nebenbefunde `contacts` 61/62, `spreed` 75/76, `comments` 81/82, `circles` 83/84, `adminAudit` 77/78 |
| 2: kein Kubernetes-Daemon auf dem openDesk-Stand | `nextcloud/app_api` `RegisterDaemon.php:37` an `stable33` (ohne `kubernetes-install`) gegen `stable34` (mit), `--k8s` an `stable34` Zeile 54 | beide HTTP 200; `KubernetesActions.php` HTTP 404 an `stable33` gegen HTTP 200 mit 803 Zeilen an `stable34`, `DEPLOY_ID` Zeile 37, HaRP Zeile 77; `k8s` an `stable33` null Treffer |
| 2b: AppAPI kommt in openDesk nicht vor | Archiv `opendesk-v1.18.0.tar.gz` geladen und außerhalb des Repositories entpackt | HTTP 200, 2285825 Bytes, 349 Dateien; `app_api\|appapi\|external.app\|exapp` 0 Treffer, `authorization_method\|integration_openproject` 3 Dateien |
| 3: Versionspin | `helmfile/environments/default/images.yaml.gotmpl` `v1.18.0`: Nextcloud `33.0.7` Zeile 351, Keycloak `26.7.0` Zeile 413, OpenProject `17.7.2` Zeile 725 (Spiegel von `openproject/open_desk`, Zeile 720) | HTTP 200, 52487 Bytes |

Der Sichtbarkeitsvorbehalt aus K1 steht ehrlich dabei und ist selbst nachgezählt: `daemonTemplates.js` an `stable34` hat acht Vorlagen, sechs `docker-install` und zwei `manual-install`, keine für `kubernetes-install`. Der Vergleich gegen `stable33` ergibt genau drei geänderte Zeilen, alle drei ein hinzugefügtes `deprecated: true`.

Der eine verbleibende Vorbehalt steht ausdrücklich im Text: das openDesk-Nextcloud-Image wird aus einem nicht mitgelesenen Projekt gebaut, ob es `app_api` enthält und eingeschaltet hat, ist aus dem Deployment-Projekt nicht entscheidbar. Er geht als Punkt 1a in 1.4 und als Frage 6 in Abschnitt 4.

## Abschnitt 1.4 und der Schluss von Abschnitt 1

Vier offene Punkte als Tabelle mit Offener Punkt, Warum aus Quellen nicht entscheidbar, Verweis: `app_api` im Image (Frage 6), Betriebsart `oauth2` gegen `oidc` mit dem ausdrücklichen Wort `Indiz` (Frage 7), Aufnahme einer Dritt-ExApp (Frage 1), Termin von openDesk auf Nextcloud 34 (Frage 5). Der fünfte, kleinere Punkt (keine Oberflächenvorlage für `kubernetes-install`) reist als Nebenfrage zu Frage 5 mit, statt weggelassen zu werden.

Der Schlussabsatz beantwortet OD-01 in drei Sätzen und hält die von Pitfall 3 verlangte Trennung sichtbar: Abschnitt 1 ist vollständig "aus openDesk-Quellen belegt", der erste "lokal gemessene" Wert entsteht als S0 in Plan 17-02.

## Deviations from Plan

**1. [Rule 2 - Fehlende Belegpflicht] Quellzeile für die `--k8s`-Option nachgetragen**
- **Gefunden bei:** Task 2, nach dem Schreiben von 1.2
- **Problem:** Der Satz "nur über `occ app_api:daemon:register --k8s` erreichbar" stand ohne Datei und Zeile im Bericht. Nach der Nachweisform dieses Projekts (17-RESEARCH.md §Nachweisform, Regel 1 aus context_agent#230) gilt eine Behauptung über fremden Code ohne Zeile nicht, und der Plan verlangt genau das für jede Hürde.
- **Fix:** `RegisterDaemon.php` an `stable34` Zeile 54 wörtlich zitiert (`'Flag to indicate Kubernetes daemon (uses kubernetes-install deploy ID). Requires --harp flag.'`), die sechs weiteren `k8s_`-Optionen in Zeile 55 bis 60 genannt und die Gegenprobe geführt: dieselbe Datei an `stable33` enthält `k8s` null Mal.
- **Dateien:** `docs/spike-opendesk.md`
- **Commit:** 694f6ae

**2. [Rule 1 - Verfrühter Statuswechsel] OD-01 bleibt in REQUIREMENTS.md Pending**
- **Gefunden bei:** Zustandsaktualisierung nach dem Bericht
- **Problem:** `requirements mark-complete OD-01` hat die Anforderung abgehakt und die Rückverfolgungstabelle auf Complete gesetzt. Der Wortlaut von OD-01 verlangt aber "Es ist **gemessen** und schriftlich belegt, ob und **auf welchem Weg** diese ExApp in einer openDesk-Umgebung überhaupt installierbar ist". Gemessen ist in diesem Plan nichts: S0 steht als `noch nicht gemessen, Plan 17-02` im eigenen Bericht, und der Weg selbst ist ausdrücklich offen. OD-01 wird außerdem von 17-02 und 17-09 mitgetragen; 17-09 ist der Plan, der sie schließt.
- **Fix:** Die Änderung an `.planning/REQUIREMENTS.md` zurückgenommen. OD-01 steht weiter auf Pending und wird am Ende der Phase abgehakt. Das folgt dem Muster früherer Phasen (TOOL-09, EXAPP-10) und der Projektregel, Nachweise wörtlich zu nehmen: ein Abhaken auf halbem Weg wäre genau die Aussage, die dieser Bericht über openDesk nicht machen darf.
- **Dateien:** keine (Rücknahme)
- **Commit:** derselbe wie dieses SUMMARY

Sonst keine. Drei Feinheiten, in denen der Bericht genauer ist als die Recherchevorlage, sind keine Abweichungen vom Plan, sondern Folge der Regel "nur schreiben, was der eigene Abruf bestätigt":

- Die HaRP-Verwendung in `KubernetesActions.php` steht im Bericht mit Zeile 77 (`buildHarpK8sUrl`) und den Zeilen 88 und 91, weil der eigene Abruf diese Zeilen zeigte; 17-RESEARCH.md nennt 765 und 69.
- `daemonTemplates.js` ist zwischen `stable33` und `stable34` nicht "unverändert", sondern unterscheidet sich in genau drei Zeilen (`deprecated: true`). Für die Aussage (keine `kubernetes-install`-Vorlage) ändert das nichts, der Bericht sagt es aber genau.
- `sharereview: enabled: false` (Zeile 73 bis 74) wurde beim Abruf mitgesehen und nicht in den Bericht genommen, weil es kein Werkzeug dieser App betrifft.

## Authentication Gates

Keine. Alle Abrufe dieses Plans sind ohne Anmeldung erreichbar. Die eine Stelle, die eine Anmeldung verlangt, ist die GitLab-Blob-Suche (HTTP 401); sie wurde nicht benutzt, stattdessen das Repository-Archiv, und genau dieser Umweg steht im Bericht.

## Verification

- `grep -c '^## ' docs/spike-opendesk.md` ergibt 7.
- Alle neun Zeichenketten des Task-2-Gates gefunden (`appstore`, `kubernetes-install`, `stable33`, `stable34`, `33.0.7`, `17.7.2`, `26.7.0`, `min-version`, `v1.18.0`).
- `Abschnitt 4` kommt neun Mal vor, `Terminfrage` und `Indiz` je vorhanden.
- Kein U+2014 und kein U+2013 in der Datei, keine ASCII-Ersatzschreibung von Umlauten.
- Die Formulierung "ausdrücklich für Entwicklung" kommt nicht vor.
- `git status --short src/ appinfo/ pyproject.toml uv.lock` ist leer: der Produktionsbaum steht still (Erfolgskriterium 5, T-17-04). `files_modified` nennt keinen Pfad unter `src/` (D-12).
- Kein `eyJ`, kein `Bearer `-Wert, kein `refresh_token`-Wert und kein `client_secret`-Wert in der Datei; die vier Zeichenketten kommen nur als Suchmuster in der Geheimnisregel selbst vor. In diesem Plan lief keine Instanz, es konnte kein Geheimnis entstehen.

## Known Stubs

Beabsichtigt und im Bericht gekennzeichnet: die Abschnitte 2 bis 5 und "Was diese Messung nicht beweist" tragen je eine Zeile `noch nicht gemessen, Plan 17-NN` samt Planzuordnung. Das ist die von D-10 verlangte Gerüstfunktion (der Abschnitt für die ISV-Fragenliste existiert, damit die Liste versioniert im Repository steht) und kein unvollständiges Ergebnis dieses Plans. Aufgelöst werden sie durch die Pläne 17-02, 17-04, 17-05, 17-06, 17-08 und 17-09.

## Threat Flags

Keine. Dieser Plan legt keine neue Netzwerkfläche, keinen Auth-Pfad und kein Schema an; er schreibt eine Datei unter `docs/`, die nicht Teil des Store-Assets ist.

## Self-Check: PASSED

Alle in diesem SUMMARY genannten Dateien existieren (`docs/spike-opendesk.md`, `.planning/phases/17-opendesk-spike/17-01-SUMMARY.md`), und alle vier Commit-Kennungen (9366b32, cf749e7, af43861, 694f6ae) sind im Repository auffindbar. Der Produktionsbaum ist unverändert.
