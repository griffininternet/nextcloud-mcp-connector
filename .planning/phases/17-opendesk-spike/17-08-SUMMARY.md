---
phase: 17-opendesk-spike
plan: 08
subsystem: verhandlung-und-rueckkanaele
tags: [spike, opendesk, od-03, isv-call, fragenliste, entwuerfe, d-09, d-10, d-11, d-12]
requires:
  - "17-01: Abschnitt 1 des Berichts samt 1.4, das die Fragen 1, 5, 6 und 7 namentlich anspricht; die Nummerierung dieses Plans musste dazu passen"
  - "17-05: der Capability-Befund, der die dritte Ausgangsfrage beantwortet und sie damit von der Liste nimmt"
  - "17-06: S4, die serverseitige Erneuerung ohne Browsersitzung im Modus oauth2, als erste Haelfte des Aufhaengers von Frage 7"
  - "17-07: S5a bis S5c, die zweite Haelfte desselben Aufhaengers, und der bereits vorliegende unversendete Entwurf zu user_oidc#925"
  - "17-04: die PKCE-Gegenprobe (400 'Code challenge is required.') und die Metadatenluecke, aus denen Frage 9 besteht"
  - "deferred-items.md DI-17-01, DI-17-03, DI-17-04, DI-17-05: vier Funde, die in dieser Liste eine Frage oder eine Nachfrage bekommen mussten"
provides:
  - "docs/spike-opendesk.md Abschnitt 4: neun Fragen, jede mit einem Absatz Grund, der die Folge einer Antwort nennt und nicht das Interesse an ihr"
  - "Die vier Pflichtfragen aus OD-01 woertlich abgedeckt: ZenDiS-Aufnahmeverfahren (1), Installationsweg in openDesk (2), AGPL-Konsequenz fuer die Enterprise-Positionierung (3), Abschaltung von Talk und Kontakten (4)"
  - "Die fuenf in dieser Phase entstandenen Fragen: Termin Nextcloud 34 (5), app_api im openDesk-Image (6), Modus oauth2 gegen oidc (7), audience-korrektes Token ohne Browsersitzung (8), fehlendes code_challenge_methods_supported (9)"
  - "Tabelle 'Nicht mehr auf der Liste': genau drei Fragen der Ausgangsrecherche entfernt, jede mit dem Beleg, der sie erledigt hat"
  - "Sechs Nachfragen mit eigener Folge, in die vier zurueckgestellte Funde eingearbeitet sind (nativer MCP-Endpunkt von OpenProject unter 6, sso_provider_type, vorkonfigurierte Ablage und SSRF-Erlaubnisliste unter 7)"
  - "Derselbe Stand im Dossier Desktop/ISV-Call-Dossier-2026-09-14.md als Abschnitt 'Technische Fragen aus Phase 17 (Stand 2026-08-29)' samt Belegverweis (D-10)"
  - "docs/contrib/opendesk-forum-antwort-christianlupus.md: Antwort im Nextcloud-Forum, Entwurf, unversendet"
  - "docs/contrib/openproject-community-konto-anfrage.md: Konto-Anfrage an die OpenProject-Community, Entwurf, unversendet"
affects:
  - "17-09 kann 2.4 und 2.5 schreiben, ohne eine Frage doppelt zu fuehren: was offen bleibt, hat jetzt in Abschnitt 4 eine Nummer, und der Bericht kann darauf verweisen statt zu wiederholen"
  - "Der Owner geht am 14.09. mit neun Fragen ins Gespraech, deren Reihenfolge fest ist, weil fuenf Stellen des Berichts auf die Nummern zeigen"
  - "Drei unversendete Entwuerfe liegen versandfertig im Repository; der Rueckkanal zur OCS-Stabilitaetsfrage laeuft nach dieser Phase weiter"
  - "OD-03 ist erfuellt, OD-01 bekommt seine offenen Punkte als Fragen mit Nummer, OD-02 bleibt bei 17-09"
tech-stack:
  added: []
  patterns:
    - "Eine Fragenliste wird kuerzer, wenn gemessen wurde: beantwortete Fragen werden entfernt und in einer Tabelle mit ihrem Beleg gefuehrt, statt sicherheitshalber mitzulaufen. Gespraechszeit ist die knappe Groesse, und eine Frage mit bekannter Antwort verdraengt eine ohne"
    - "Jede Frage traegt ihre Folge und nicht ihren Anlass: 'heisst die Antwort X, aendert sich Y' macht im Gespraech sofort sichtbar, warum die Frage gestellt wird, und schuetzt vor einer hoeflichen Auskunft ohne Entscheidungswert"
    - "Nummern in einem Bericht sind eine Schnittstelle: fuenf Stellen zeigten schon auf die Fragen 1, 5, 6, 7 und 9, bevor es sie gab, also war die Reihenfolge nicht mehr frei. Der Abschnitt sagt das ausdruecklich, damit niemand spaeter umsortiert"
    - "Zurueckgestellte Funde als Nachfrage an die passende Hauptfrage haengen statt als zehnte und elfte Frage: die Liste bleibt bei neun, und kein Fund faellt unter den Tisch"
    - "Ein Entwurf, der keine gepruefte Empfaengeradresse hat, nennt keine: der Kanal steht als offene Owner-Entscheidung im Kopf, statt eine plausible Adresse zu erfinden"
key-files:
  created:
    - "docs/contrib/opendesk-forum-antwort-christianlupus.md"
    - "docs/contrib/openproject-community-konto-anfrage.md"
  modified:
    - "docs/spike-opendesk.md"
    - "C:/Users/Student/Desktop/ISV-Call-Dossier-2026-09-14.md (ausserhalb des Repositoriums, nicht versioniert und nicht committet)"
decisions:
  - "Die Reihenfolge der neun Fragen ist an die bestehenden Verweise gebunden und nicht nach Wichtigkeit sortiert worden: 1.2, 1.3, 1.4, 2.2 und 2.5 zeigen bereits auf die Nummern 1, 5, 6, 7 und 9. Eine Sortierung nach Wichtigkeit haette fuenf Verweise ins Leere zeigen lassen"
  - "Vier zurueckgestellte Funde sind als Nachfragen eingearbeitet statt als eigene Fragen: DI-17-01 (nativer MCP-Endpunkt von OpenProject) unter Frage 6, DI-17-05 (sso_provider_type), DI-17-04 (vorkonfigurierte Ablage) und DI-17-03 (SSRF-Erlaubnisliste) unter Frage 7. Die geforderte Zahl von neun Fragen bleibt, und keiner der Funde geht verloren"
  - "Bei den Kubernetes-Belegen von Frage 5 sind die vier Freigabearten und die vier CI-Ablaeufe ausdruecklich der Phasenrecherche zugeschrieben und nicht dem Bericht: der Bericht hat in 1.2 nur die Hilfetexte beider Zweige und das 404-gegen-200 selbst abgerufen"
  - "Die Konto-Anfrage nennt keine Empfaengeradresse: in dieser Phase wurde keine geprueft, und eine erfundene waere genau die Art Behauptung, die die Regel aus context_agent#230 verbietet. Der Kanal ist als Owner-Entscheidung markiert"
  - "Der Forumsentwurf bleibt bei einer einzigen offenen Frage (Stabilitaetszusage der 17 OCS-Routen) und stellt die drei Luecken nur als Stand dar, ohne erneut nach neuen Routen zu fragen: die Deckungsfrage stand schon im Ausgangsbeitrag, und eine Wiederholung haette die enge Frage verwaessert"
  - "Das Dossier auf dem Desktop bekommt einen ausdruecklichen Vorrangvermerk: bei einem Widerspruch gilt der versionierte Bericht. Sonst haette D-10 zwei Wahrheiten erzeugt, von denen eine nicht nachvollziehbar aelter werden kann"
metrics:
  duration: 20 min
  completed: 2026-08-29
---

# Phase 17 Plan 08: Die Fragenliste fuer den 14.09. und zwei unversendete Rueckkanaele Summary

OD-03 ist erfüllt: die Fragenliste für den ISV-Call am 14.09. steht als Abschnitt 4 versioniert im Spike-Bericht und mit demselben Stand im Dossier für den Termin. Neun Fragen, jede mit einem Absatz `Grund:`, der die **Folge** einer Antwort nennt. Drei Fragen der Ausgangsrecherche sind entfernt, weil diese Phase sie gemessen beantwortet hat; sie stehen mit ihrem Beleg in der Tabelle `Nicht mehr auf der Liste` und werden nicht vorsichtshalber mitgeführt. Dazu liegen zwei neue Entwürfe unversendet im Repository.

## Was entstanden ist

**Abschnitt 4 des Berichts, 210 Zeilen, neun Fragen.** Die vier Pflichtfragen aus OD-01 stehen an den Nummern 1 bis 4 und sind namentlich erkennbar: ZenDiS-Aufnahmeverfahren, Installationsweg in openDesk, AGPL-Konsequenz für die Enterprise-Positionierung, und die Folge der abgeschalteten Apps Talk und Kontakte für zwei der neun Werkzeugfamilien. Die Nummern 5 bis 9 sind in dieser Phase erst entstanden: der Termin von openDesk auf Nextcloud 34 oder höher, `app_api` im openDesk-Nextcloud-Image, der Betriebsmodus von `integration_openproject`, das audience-korrekte Token ohne Browsersitzung und das fehlende `code_challenge_methods_supported`.

**Die Nummerierung war nicht frei.** Fünf Stellen des Berichts zeigten schon auf Nummern, bevor es die Liste gab: 1.2 und 1.3 auf Frage 5, 1.4 auf die Fragen 1, 5, 6 und 7, 2.2 auf Frage 9, 2.5 auf Frage 7. Der Abschnitt sagt das im ersten Absatz ausdrücklich, damit niemand später nach Wichtigkeit umsortiert und dabei fünf Verweise ins Leere zeigen lässt.

**Der stärkste Aufhänger der Liste ist Frage 7, und er ist beidseitig gemessen.** Im Modus `oauth2` erneuert `integration_openproject` das Nutzertoken serverseitig: 200 mit Treffer, `token_expires_at` danach 7200 Sekunden in der Zukunft, Tokenpaar ausgetauscht, kein Cookie und kein App-Passwort (S4). Im Modus `oidc` fällt derselbe Aufruf desselben Kontos nach Ablauf auf 401 mit 77 Bytes, und `user_oidc` protokolliert wörtlich `getToken: no session data` (S5a bis S5c). Damit ist der Quellcodekommentar aus `OpenProjectAPIService.php:1764-1765` nicht mehr nur zitiert, und die Frage nach dem Modus in openDesk hat eine bezifferte Folge statt eines Verdachts.

**Vier zurückgestellte Funde sind als Nachfragen eingearbeitet, nicht als zusätzliche Fragen.** DI-17-01 (OpenProject 17.7.2 bringt einen eigenen MCP-Endpunkt mit) hängt an Frage 6, weil es dieselbe Frage für die Nachbarkomponente ist. DI-17-05 (`sso_provider_type`), DI-17-04 (vorkonfigurierte Ablage, ohne die `file-links` leer bleibt) und DI-17-03 (SSRF-Erlaubnisliste) hängen an Frage 7, weil sie alle den Bootstrap-Job betreffen. Die Liste bleibt bei neun, und kein Fund fällt unter den Tisch.

**Drei Fragen sind entfernt worden.** Die AppAPI-Aktivierungsfrage ist zur Hälfte beantwortet (null Treffer über 349 Dateien des Deployment-Projekts) und im Rest präziser als Frage 6 gefasst. Die PKCE-Annahme ist in beide Richtungen gemessen (mit `code_challenge` 200 und ein Code, ohne 400 mit `Code challenge is required.`), der Rest ist Frage 9. Die Capability-Frage ist gemessen beantwortet, sogar unauthentifiziert und mit Fassungsnummer. Der Grund für das Streichen steht im Bericht: Gesprächszeit am 14.09. ist die knappe Größe, und eine Frage mit bekannter Antwort lädt eine Auskunft ein, die wir schon haben, und verdrängt eine, die wir brauchen.

**Das Dossier auf dem Desktop (D-10).** `C:\Users\Student\Desktop\ISV-Call-Dossier-2026-09-14.md` trägt jetzt den Abschnitt "Technische Fragen aus Phase 17 (Stand 2026-08-29)" mit denselben neun Fragen, ihren Gründen, der Streichtabelle und dem Verweis auf `docs/spike-opendesk.md`, Abschnitt 4. Die drei nicht-technischen Fragen des Validierungsplans (Verkaufsmechanik, Referenz-ISVs, Kanal des Enterprise-Flags) sowie die Frage zur Rechtsform sind unberührt geblieben. **Diese Datei liegt außerhalb des Repositoriums, ist nicht versioniert und ist nicht committet worden**; deshalb trägt sie einen Vorrangvermerk: bei einem Widerspruch gilt der Bericht.

## Die drei Entwürfe, und was mit ihnen nicht passiert ist

| Datei | Kanal | Stand |
|-------|-------|-------|
| `docs/contrib/opendesk-forum-antwort-christianlupus.md` | Nextcloud-Forum, bestehender Faden zu den OCS-Routen | **Entwurf, nicht gesendet** |
| `docs/contrib/openproject-community-konto-anfrage.md` | Kanal offen, vom Owner zu wählen | **Entwurf, nicht gesendet** |
| `docs/contrib/user-oidc-925-kommentar.md` (aus 17-07) | `nextcloud/user_oidc#925` | **Entwurf, nicht gesendet**, geprüft und zulässig |

Der Forumsentwurf dankt für den Hinweis auf die OpenProject-Community, nennt in einem Absatz den gemessenen Stand (die OCS-Fläche antwortet unter reiner AppAPI-Impersonation, die Berechtigung hängt am Nutzer, die Erneuerung trägt im Modus `oauth2` und bricht im Modus `oidc`, 17 Routen an Tag `v3.1.1`, die drei Lücken, `work-packages/{id}/file-links`) und stellt genau eine Frage: sind diese Routen als Schnittstelle für andere Apps gedacht, gilt für sie also eine Stabilitätszusage. Nach neuen Routen fragt er nicht noch einmal, das stand schon im Ausgangsbeitrag.

Die Konto-Anfrage nennt den gemessenen HTTP-Status der Selbstregistrierung mit Datum (HTTP 400, `Registration not allowed`, 2026-08-28), sagt wer fragt und in welchem Zusammenhang, wofür das Konto gebraucht wird, und bittet um den vorgesehenen Weg. Eine Empfängeradresse nennt sie ausdrücklich nicht, weil in dieser Phase keine geprüft wurde.

**Die Prüfung nach D-08 ist gelaufen:** der Entwurf zu `user_oidc#925` darf existieren, weil Plan 17-07 die Live-Reproduktion protokolliert hat (die Meldungen aus `TokenService.php:318` und `:328` stehen wörtlich im Protokoll, und `isLoggedIn()` ist gemessen statt vermutet). Er ist deshalb nicht entfernt worden.

## Owner-Freigabe

**Freigegeben am 2026-08-29, gelesener Zeitstempel `2026-08-29T05:09:25Z` (UTC).** Der Owner hat Abschnitt 4, die drei Streichungen und die drei Entwürfe gelesen und **ohne inhaltliche Änderung** freigegeben, wörtlich "ok" beziehungsweise "freigegeben". Es war also keine Nacharbeit an Liste oder Entwürfen einzuarbeiten; der Stand, den der Owner gelesen hat, ist der Stand, der committet ist.

**Gesendet wurde nichts, und das ist keine Formel.** Kein `gh issue comment`, kein Mailversand, kein Browserversand, kein Playwright-Lauf, kein Registrierungsversuch und kein Forumsaufruf. Alle drei Entwürfe in `docs/contrib/` bleiben unversendet; gesendet wird ausschließlich vom Owner (D-11, `feedback_owner_sends_outreach`, Regel aus context_agent#230). Jeder der drei trägt die Statuszeile in seinem Kopfkommentar.

## Abweichungen vom Plan

**Eine, und sie macht die Liste enger statt weiter.**

**1. [Rule 2 - Belegtreue] Die Kubernetes-Nebenbelege sind zugeschrieben statt behauptet**
- **Gefunden bei:** Task 1, beim Ausformulieren von Frage 5
- **Sachverhalt:** Der Plan nennt als Aufhänger "vier Freigabearten, vier CI-Workflows". Der Bericht selbst hat diese beiden Zahlen in 1.2 nie abgerufen; er belegt die Hilfetexte beider Zweige, das 404 gegen 200 an `KubernetesActions.php` und die fehlende Oberflächenvorlage. Die zwei Zahlen stammen aus `17-RESEARCH.md` (Zeilen 1704 bis 1711), wo sie an denselben Zweigen gelesen wurden.
- **Behandlung:** Beide Zahlen stehen in Frage 5, aber ausdrücklich der Phasenrecherche zugeschrieben und nicht dem Bericht. Ein Bericht, der eine fremde Zählung als eigene Messung führt, verletzt genau die Regel, die dieser Phase ihren Wert gibt.
- **Datei:** `docs/spike-opendesk.md`, Abschnitt 4, Frage 5
- **Commit:** `e2c014b`

Sonst keine: kein Produktionscode, keine neue Datei außerhalb von `docs/`, keine Änderung an bestehenden Berichtsabschnitten außer dem Ersetzen des Platzhalters von Abschnitt 4 samt dem dort vorgemerkten Absatz zu Frage 9, der jetzt in der Frage selbst aufgegangen ist.

## Gates

| Gate | Ergebnis |
|------|----------|
| `git status --short src/ appinfo/ pyproject.toml uv.lock` | **leer**, der Produktionsbaum ist unberührt (D-12, ROADMAP-Erfolgskriterium 5) |
| Geheimnis-Gate über die geänderten Dateien (`eyJ`, `client_secret=`, `refresh_token=`, Bearer mit Wert) | **kein Treffer** in `docs/contrib/` und keiner in Abschnitt 4. Die zwei Treffer in `docs/spike-opendesk.md` liegen in den Zeilen 1154 und 1903, stammen aus 17-04 und 17-06 und sind ein Platzhalter beziehungsweise die wörtliche Testzeichenkette `TESTBEARERTOKEN` |
| Vokabular-Gate (das eine Wort aus `FORBIDDEN_VOCABULARY` in `tests/unit/test_exapp_env_setup.py`, teilzeichenkettenweise und ohne Rücksicht auf Groß- und Kleinschreibung; hier umschrieben statt zitiert, sonst findet der Griff diese Zeile selbst) | **0 Treffer** in `docs/spike-opendesk.md` und in allen vier Dateien unter `docs/contrib/` |
| Gedankenstriche (U+2014, U+2013) | **0 Treffer** im Bericht, in den Entwürfen und im Dossier |
| Neun numerierte Fragen und `Grund:` | Abschnitt 4 trägt neun numerierte Fragen; `grep -c "Grund:"` über die Datei ergibt 10 |
| Die vier Pflichtbegriffe (`ZenDiS`, `AGPL`, `spreed`, `kubernetes-install`, `code_challenge_methods_supported`, `Nicht mehr auf der Liste`) | alle vorhanden |
| Statuszeile in beiden neuen Entwürfen | vorhanden, je mit `nicht gesendet` und dem Hinweis auf den Owner |

## Was dieser Plan nicht getan hat

Er hat keine Frage beantwortet, sondern neun gestellt. Er hat nichts gemessen: jeder Messwert in Abschnitt 4 ist ein Verweis auf einen Abschnitt, in dem er entstanden ist. Er hat keinen Kanal bedient und keine Adresse geprüft. Und er hat über den nativen MCP-Endpunkt von OpenProject nichts behauptet außer seiner Existenz an einer gelesenen Zeile, weil über ihn in dieser Phase nichts gemessen ist.

## Self-Check: PASSED

- `docs/spike-opendesk.md` Abschnitt 4 vorhanden, neun numerierte Fragen, Tabelle `Nicht mehr auf der Liste` mit genau drei Zeilen: FOUND
- `docs/contrib/opendesk-forum-antwort-christianlupus.md`: FOUND
- `docs/contrib/openproject-community-konto-anfrage.md`: FOUND
- `docs/contrib/user-oidc-925-kommentar.md` (Bestand aus 17-07, nach D-08 geprüft und zulässig): FOUND
- `C:\Users\Student\Desktop\ISV-Call-Dossier-2026-09-14.md`, Abschnitt "Technische Fragen aus Phase 17": FOUND (nicht versioniert, nicht committet)
- Commit `e2c014b` (Abschnitt 4): FOUND
- Commit `4568111` (zwei Entwürfe): FOUND
