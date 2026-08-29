---
phase: 17-opendesk-spike
verified: 2026-08-29T00:00:00Z
status: passed
score: 5/5 Erfolgskriterien verifiziert (OD-01, OD-02, OD-03 erfuellt)
overrides_applied: 0
gaps: []
---

# Phase 17: openDesk-Spike, Verifikationsbericht

**Phase-Ziel:** Die openDesk-Frage ist vor dem ISV-Call gemessen und schriftlich belegt, ohne dass eine Zeile Produktionscode entsteht
**Verifiziert:** 2026-08-29
**Status:** passed
**Re-Verifikation:** Nein, Erstverifikation

Dieser Bericht prueft nicht, ob die neun Plaene abgearbeitet wurden (das ist unstrittig, 9/9), sondern
ob `docs/spike-opendesk.md`, die drei Entwuerfe und der Produktionsbaum tatsaechlich das liefern, was
die fuenf Roadmap-Erfolgskriterien verlangen. Jede Zeile unten stammt aus einem selbst gelesenen
Ausschnitt der Datei, einem selbst ausgefuehrten Kommando oder einem selbst geprueften `git diff`, nicht
aus einer SUMMARY-Behauptung.

## Zielerreichung

### Beobachtbare Wahrheiten (Roadmap-Erfolgskriterien 1 bis 5)

| # | Wahrheit | Status | Beleg |
|---|----------|--------|-------|
| 1 | Ein Leser erfaehrt zuerst die Installierbarkeit, mit Quelle oder ISV-Frage je Huerde, samt Pin-Aussage 33.0.7 gegen 34.0.3 | VERIFIZIERT | Abschnitt 1 (Zeilen 36 bis 214) steht vor Abschnitt 2 (Auth). 1.1 App Store: Quelle `values-nextcloud-management.yaml.gotmpl` Zeile 79 bis 80. 1.2 Kubernetes: Quellenpaar `RegisterDaemon.php` stable33 gegen stable34, plus HTTP-404-gegen-200-Probe auf `KubernetesActions.php`. 1.3 Versionspin: Quelle `images.yaml.gotmpl` Zeile 344 bis 351, dazu ein selbst gemessener Wert S0 (Zeile 153 bis 197), der die Ein-Klick-Kette live auf 33.0.7 bestaetigt und damit den 34.0.3-Nachweis ausdruecklich ersetzt ("Was S0 fuer OD-01 bedeutet", Zeile 193). Vier verbleibende offene Punkte stehen namentlich in 1.4 mit Verweis auf die ISV-Fragen 1, 5, 6, 7 |
| 2 | Weg 0 und Weg 1 stehen mit Messwerten nebeneinander: PKCE, Token-Lebensdauer, Erneuerung ohne Browsersitzung, SSRF-Antwort | VERIFIZIERT | Abschnitt 2.1 (Weg 0, S1 bis S6) und 2.2 (Weg 1) sind eigene Abschnitte im selben Bericht. PKCE Weg 1: 200 mit `code_challenge`, 400 "Code challenge is required." ohne (Zeile 1120 ff). `expires_in` 7200 s (Weg 1, 2.2) gegen die unabhaengig gemessenen ~7200 s Restlaufzeit von Weg 0 (Zeile 421 bis 431). Erneuerung ohne Browsersitzung: Weg 0 S4 zweimal gemessen, kuenstlich und natuerlich verstrichen (Zeile 592 ff, 996), Weg 1 Zeile 1144 ff ohne `-b`/`-c`. SSRF-Antwort in 2.3 (Zeile 1296 bis 1351): `resolve_addresses()` verwirft Nachbardienste unter Compose-Namen dreifach mit `None`, oeffentliche Namen liefern Adresslisten |
| 3 | Der tragende Weg steht als Folge der Messung, nicht als Argument; Ungemessenes heisst "ungemessen", nicht "verworfen" | VERIFIZIERT | 2.4 (Zeile 1352 bis 1460) verweist in jedem Absatz auf eine Messzeile aus 2.1/2.2/2.3, keine eigene Behauptung ohne Zeilenanker. `nextcloud_hub`-Pfad (DI-17-05) steht explizit als "ungemessen" und nicht als widerlegt: "ein Satz 'Weg 0 traegt unter OIDC nicht' ginge deshalb um genau diesen Pfad ueber die Messung hinaus" (Zeile 1391 bis 1393). `file-links` (DI-17-04) steht als "ungemessen, belegt sind nur Existenz und Signatur" in der 2.5-Tabelle (Zeile 1472) und zusaetzlich in "Was diese Messung nicht beweist" (Zeile 2570 bis 2572). Der Bericht spricht wortwoertlich aus, dass "verworfen" kein zulaessiges Urteil ist (Zeile 34) |
| 4 | ISV-Fragenliste enthaelt ZenDiS-Aufnahmeverfahren, Installationsweg, AGPL-Konsequenz, Talk/Kontakte-Abschaltung | VERIFIZIERT | Abschnitt 4 (Zeile 1649 ff), vier Pflichtfragen Zeile 1679 bis 1729: Frage 1 Aufnahmeverfahren, Frage 2 Installationsweg, Frage 3 AGPL-Konsequenz fuer Enterprise-Positionierung, Frage 4 Talk/Kontakte-Abschaltung fuer zwei Werkzeugfamilien. Dieselbe Liste steht zusaetzlich in `Desktop/ISV-Call-Dossier-2026-09-14.md`, Abschnitt "Technische Fragen aus Phase 17" (Zeile 54 ff, selbst gelesen), mit denselben vier Themen wortgleich uebernommen |
| 5 | Produktionsbaum unveraendert: kein neues Werkzeug, kein neuer Client, Werkzeugoberflaeche und Budget-Gate stehen still | VERIFIZIERT | Selbst ausgefuehrt: `git diff --stat 90d2f68..HEAD -- src appinfo pyproject.toml uv.lock` liefert leere Ausgabe. `git status --short src/ appinfo/ pyproject.toml uv.lock` ebenfalls leer. `uv run python scripts/check_tool_budget.py` meldet `tools/list: 15712 bytes, 21 tools, budget 18000`, Zeichen fuer Zeichen die im Bericht behauptete Zahl. `uv run pytest -q` beendet mit Exit-Code 0, keine Fehlschlaege (40 Zeilen Punkte, keine `F`/`E`). `uv run ruff check .` meldet "All checks passed!", `uv run ruff format --check .` meldet "202 files already formatted" |

**Ergebnis:** 5/5 Roadmap-Erfolgskriterien verifiziert, keines davon nur auf Basis der SUMMARY-Dateien, sondern jeweils gegen den Volltext von `docs/spike-opendesk.md` und/oder ein selbst ausgefuehrtes Kommando geprueft.

### Requirements-Abdeckung (OD-01, OD-02, OD-03)

| Requirement | Quell-Plan | Status | Beleg |
|-------------|-----------|--------|-------|
| OD-01 | 17-01, 17-02 | ERFUELLT | Abschnitt 1 vollstaendig aus Quellen belegt (drei Huerden), S0 als erster lokaler Messwert, vier offene Punkte namentlich mit ISV-Verweis. `.planning/REQUIREMENTS.md` Zeile 83 fuehrt OD-01 als "Complete", was mit dem Textbefund uebereinstimmt |
| OD-02 | 17-02 bis 17-07 | ERFUELLT | Weg 0 (S1 bis S6) und Weg 1 vollstaendig gemessen mit Gegenproben, SSRF gemessen (D-06), Entscheidung in 2.4 als Folge der Messung, nicht als Argument |
| OD-03 | 17-08 | ERFUELLT | Neun Fragen in Abschnitt 4, vier Pflichtfragen woertlich aus OD-01/REQUIREMENTS.md abgedeckt, Dossier auf dem Desktop aktualisiert (D-10) |

Keine verwaisten Requirements: `.planning/REQUIREMENTS.md` fuehrt fuer Phase 17 ausschliesslich OD-01 bis OD-03, alle drei sind in Plaenen deklariert und oben abgedeckt.

### Ehrlichkeits-Pruefungen

| Punkt | Geprueft | Ergebnis |
|-------|----------|----------|
| Drei Eingriffe in die Messumgebung offengelegt | Ja | Abschnitt "Was diese Messung nicht beweist" (Zeile 2551 bis 2566) nennt `allow_local_remote_servers=true`, den per `rails runner` gesetzten OpenProject-Admin-Passwort mit ausdruecklich ungeklaerter Ursache ("ist nicht untersucht", Zeile 2561), und Keycloak/`user_oidc` als ausschliesslich fuer S5 hinzugefuegt. Zwei weitere Eingriffe (Debug-Loglevel, `allow_insecure_http`) stehen zusaetzlich offen (Zeile 2584 bis 2589), mehr als die drei geforderten |
| Alle Entwuerfe als unversendet markiert | Ja | Alle drei Dateien in `docs/contrib/` tragen im HTML-Kommentarkopf "Status: Entwurf, nicht gesendet. Versand ausschliesslich durch den Owner." und "Kein Agent hat diesen Text gesendet, gepostet oder eingereicht" |
| Hinweis auf tatsaechlichen Versand (git log, gh, Browser) | Selbst gesucht, keiner gefunden | `git log 90d2f68..HEAD -p -- docs/contrib/` enthaelt keine `gh issue`/`gh pr`-Aufrufe und keine Versandbestaetigung; alle Commit-Nachrichten der Entwuerfe tragen "unversendet" |
| `user_oidc#925`-Entwurf nur bei geglueckter Repro (D-08) | Ja | Abschnitt 2.1 "Was aus dieser Messung nach draussen geht" (Zeile 882 bis 894): "Sie ist gelungen: die Meldungen aus `TokenService.php:318` und `:328` stehen woertlich im Protokoll" und der Entwurf verweist im Kopf auf S5a bis S5c als Beleg der Reproduktion |

### Geheimnisse

| Pruefung | Ergebnis |
|----------|----------|
| `git ls-files \| grep env.spike` | Nur `.env.spike-opendesk.example` getrackt, jede Geheimniszeile darin auskommentiert und mit Platzhaltern (`xxxxx-xxxxx-...`) belegt |
| `.gitignore` traegt `.env.spike-opendesk` | Ja, Zeile 17, mit Begruendung im Kommentar |
| Griff auf Bearer/JWT/`refresh_token=`/`client_secret=`-Muster im Diff `90d2f68..HEAD` fuer `docs/`, Compose- und Skriptdateien | Drei Treffer, alle Platzhalter: `<Wert aus dem Hauptlauf>` und `TESTBEARERTOKEN` (letzteres ein dokumentierter Testwert der App selbst, kein echtes Geheimnis) |

### Produktionsbaum nach dieser Phase (Kriterium 5, eigenstaendig nachvollzogen)

| # | Nachweis | Kommando | Selbst erhaltenes Ergebnis |
|---|----------|----------|------------------------------|
| 1 | Kein Eingriff in `src/`, `appinfo/`, `pyproject.toml`, `uv.lock` | `git diff --stat 90d2f68..HEAD -- src appinfo pyproject.toml uv.lock` | leer |
| 2 | Werkzeugoberflaeche unveraendert | `uv run python scripts/check_tool_budget.py` | `tools/list: 15712 bytes, 21 tools, budget 18000` |
| 3 | Vorgabesuite gruen | `uv run pytest -q` | Exit-Code 0, ausschliesslich Punkte in der Fortschrittsanzeige, keine Fehlschlaege |
| 4 | Lint und Format gruen | `uv run ruff check .` / `uv run ruff format --check .` | "All checks passed!" / "202 files already formatted" |

Alle vier Werte stimmen mit den im Bericht (Zeile 2605 bis 2610) behaupteten Zahlen ueberein.

### Anti-Patterns gefunden

| Datei | Zeile(n) | Muster | Schweregrad | Auswirkung |
|-------|----------|--------|-------------|------------|
| `docs/contrib/opendesk-forum-antwort-christianlupus.md` | 4, 10, 20 | ASCII-Ersatz statt echter Umlaute im HTML-Kommentarkopf ("ausschliesslich", "raet", "wuerde") | Warnung | Verstoesst gegen die globale CLAUDE.md-Regel und `PROJECT.md`-Constraint "echte Umlaute in deutschen Texten"; betrifft nur den unversendeten Metadaten-Kopf, nicht den eigentlichen englischen Forumstext |
| `docs/contrib/openproject-community-konto-anfrage.md` | 4, 6, 9, 11, 13, 22 | Dieselbe ASCII-Ersatz-Klasse ("waehlen", "veroeffentlichten", "geprueft", "wuerde") | Warnung | Gleiche Einordnung, Kommentarkopf, nicht der zu versendende englische Text |
| `docs/contrib/user-oidc-925-kommentar.md` | 4, 15 | Dieselbe Klasse ("ausschliesslich", "wuerde") | Warnung | Gleiche Einordnung |
| `.planning/phases/17-opendesk-spike/17-02-, 17-04-, 17-06-, 17-07-, 17-09-SUMMARY.md` | mehrere | ASCII-Ersatz in Fliesstext ("koennen", "natuerlich", "ausschliesslich", "wuerde") | Warnung | SUMMARY-Dateien sind interne Ausfuehrungsprotokolle, kein Nutzer-sichtbares Deliverable; `docs/spike-opendesk.md` selbst ist frei davon (eigens geprueft, ein einziger Regex-Treffer war die Fehlmeldung "betriebsreif", kein echter ASCII-Ersatz) |

Kein `TBD`/`FIXME`/`XXX` als echter Schulden-Marker gefunden: die drei Rohtreffer waren `Plans: TBD` fuer die noch ungeplanten Phasen 18/19 (Roadmap-Konvention, ausserhalb dieser Phase) und zweimal `\uXXXX` als Escape-Notation in Prosa ueber PHP-JSON-Kodierung, kein Marker.

Keine Em-Dashes, keine En-Dashes, keine Emojis in den 34 durch diese Phase veraenderten Dateien gefunden (eigener Regex-Griff auf die Unicode-Bereiche U+2014, U+2013 sowie gaengige Emoji-Bloecke, null Treffer).

Diese Anti-Pattern-Funde aendern den Gesamtstatus nicht: sie betreffen keine der fuenf Roadmap-Wahrheiten und keinen der drei Requirements, sondern eine Stilregel in sekundaeren/internen Dateien. Empfehlung: bei Gelegenheit (z. B. als Teil von Phase 18/19-Aufraeumarbeiten) die betroffenen Dateien auf echte Umlaute umstellen.

### Human Verification Required

Keine. Diese Phase liefert Erkenntnis-Dokumente (Messbericht, Fragenliste, Entwuerfe), keine Benutzeroberflaeche und keinen Produktionscode. Alle fuenf Erfolgskriterien sind durch Lesen des Volltexts und durch selbst ausgefuehrte Kommandos programmatisch nachvollziehbar; nichts davon erfordert visuelle, zeitkritische oder externe Pruefung durch einen Menschen. Insbesondere der ISV-Call selbst (14.09.) ist kein Teil des Phasenziels, sondern der naechste Schritt danach.

### Gaps Summary

Keine. Alle fuenf Roadmap-Erfolgskriterien und alle drei Requirements (OD-01, OD-02, OD-03) sind mit eigens nachvollzogener Evidenz erfuellt: der Bericht fuehrt Installierbarkeit vor jeder Auth-Frage, stellt Weg 0 und Weg 1 mit Messwerten nebeneinander, zieht den tragenden Weg als Folge der Messung und haelt zwei konkrete Unschaerfen (`nextcloud_hub`-Pfad, `file-links`-Route) korrekt als "ungemessen" statt "verworfen" fest, die Fragenliste deckt alle vier Pflichtthemen ab und steht sowohl im Repository als auch im externen Dossier, und der Produktionsbaum ist nachweislich unveraendert (leerer Diff, gruene Tests, unveraenderte Werkzeugoberflaeche, gruenes Lint). Der einzige Fund ist eine Stilfrage (ASCII-Ersatz statt Umlaute) in sekundaeren Dateien, als Warnung dokumentiert, ohne Einfluss auf die Zielerreichung.

---

*Verifiziert: 2026-08-29*
*Verifier: Claude (gsd-verifier)*
