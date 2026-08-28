# Requirements: Milestone v1.5 "Vorlauf openDesk"

**Defined:** 2026-08-28
**Core Value:** Die zugänglichste und sauberste MCP-Anbindung für Nextcloud: per Klick installierbar, spec-konformes OAuth statt App-Passwort-Gebastel, und der Assistent sieht niemals mehr als der angemeldete Nutzer.

## Owner-Entscheidungen dieses Milestones

Vor der Anforderungsdefinition getroffen, aus den acht in `research/SUMMARY.md` gesammelten Punkten:

| Id | Entscheidung | Folge |
|----|--------------|-------|
| D-v1.5-01 | Das Audit-Log überlebt `occ mcp_connector:purge` und die Deinstallation | Das v1.0-Erfolgskriterium "eine Deinstallation entfernt alle Daten" und `docs/privacy.md` werden ausdrücklich umgeschrieben; einziger automatischer Löscher ist die Aufbewahrungsfrist |
| D-v1.5-02 | Die Einträge werden hash-verkettet, das Wort "Audit-Log" bleibt im Text | Der Anspruch hält einer Nachfrage stand (BSI OPS.1.1.5 Integritätssicherung); eine Grenzbeschreibung "was es nicht leistet" ist Pflichtbestandteil, die Verbotsliste gilt |
| D-v1.5-03 | Release 0.1.11 geht sofort und eigenständig raus | Der wartende Textrest wird abgeräumt, bevor das Audit-Log fertig ist; das Release für das Audit-Log selbst ist bewusst nicht Teil dieses Milestones (EXAPP-12 unter Future Requirements) |
| D-v1.5-04 | Der Audit-Schalter steht ab Werk aus, Inhaltsstufe `keys` | Keine ungefragte neue Datenerhebung bei bestehenden Nutzern; Parameternamen ja, Parameterwerte nein, Ergebnisinhalte nie; die Stufe `full` wird nicht angeboten |

Abgeleitet aus D-v1.5-01, als Regel für die Planung: Verbindung trennen und Pausieren lassen die Einträge stehen, die abgelaufene Aufbewahrungsfrist und die Löschung des Nutzers in Nextcloud löschen sie, Purge und Deinstallation löschen alles außer dem Audit-Log.

Nicht in diesem Milestone entschieden, weil Verhandlungssache: die AGPL-Konsequenz für die Enterprise-Positionierung und die Frage, ob der Ausgang des ISV-Calls die OpenProject-Architektur präjudiziert. Beide gehören auf die Fragenliste für den 14.09. (OD-03).

## v1.5 Requirements

### Release-Pflege

- [x] **EXAPP-11**: Die im `[Unreleased]`-Block wartenden Textänderungen (gekürzter Trifecta-Absatz samt Teilen-Formulierung, Autorenkontakt admin@infranode.dev; zwei Changelog-Punkte, drei inhaltliche Änderungen) sind als Release 0.1.11 im Nextcloud App Store, mit der Versionszeichenkette an allen sechs Stellen, einem Changelog-Block samt Linkdefinition, dem Branch-Push vor dem Tag, der ausdrücklichen Owner-Freigabe vor dem Tag und der Signatur über das heruntergeladene Asset

### openDesk-Erkundung (Erkenntnis, kein Produktionscode)

- [ ] **OD-01**: Es ist gemessen und schriftlich belegt, ob und auf welchem Weg diese ExApp in einer openDesk-Umgebung überhaupt installierbar ist, gegen die drei bekannten Hürden: abgeschalteter App Store, keine AppAPI in der Distribution, Kubernetes statt Docker. Der Befund nennt ausdrücklich, was die auf Nextcloud 33.0.7 gepinnte Zielumgebung für unsere auf 34.0.3 erbrachten Ein-Klick-Nachweise bedeutet
- [ ] **OD-02**: Der Zugangsweg zu OpenProject ist gemessen statt argumentiert. Weg 0 (über die vorhandene Nextcloud-App `integration_openproject` und ihre OCS-Routen) und Weg 1 (eigener OAuth-Autorisierungscode je Nutzer direkt gegen OpenProject) stehen mit Messwerten nebeneinander, mindestens zu PKCE-Unterstützung, Token-Lebensdauer und Erneuerung ohne Browsersitzung, und zur Frage, ob die SSRF-Grenze aus v1.1 eine Nachbarkomponente unter internem Dienstnamen durchlässt. Die Entscheidung fällt auf dieser Messung, nicht auf einem Argument
- [ ] **OD-03**: Eine Fragenliste für den ISV-Call am 14.09. liegt vor, die genau das enthält, was die Recherche nicht klären konnte: das ZenDiS-Aufnahmeverfahren, der Installationsweg in openDesk, die AGPL-Konsequenz für die Enterprise-Positionierung, und was die Abschaltung von Talk und Kontakten in openDesk für zwei unserer bestehenden Werkzeugfamilien bedeutet

### Audit-Log

- [ ] **AUDIT-01**: Jeder Werkzeugaufruf erzeugt einen Eintrag mit Nutzer, Werkzeugname, Zeitpunkt, aufrufendem Client und Ergebnisstatus, ohne Parameterwerte und ohne Ergebnisinhalte; eine Erlaubnisliste je Werkzeug hält fest, welche Parameternamen erscheinen, und ein Vertragstest hält diese Grenze nach dem Muster des Budget-Gates
- [ ] **AUDIT-02**: Jeder Eintrag ist mit seinem Vorgänger hash-verkettet, und ein Prüfkommando bestätigt die ungebrochene Kette oder benennt die erste gebrochene Stelle
- [ ] **AUDIT-03**: Das Log liegt dauerhaft in einer eigenen Ablage neben dem OAuth-Speicher, hat eine Obergrenze und eine Aufbewahrungsfrist, die mindestens 180 Tage erreichen kann, und kann bei vollem Volume den OAuth-Speicher nicht schreibunfähig machen
- [ ] **AUDIT-04**: Ein Administrator liest und exportiert das Log über ein `occ`-Kommando, ohne dass dafür eine neue Route im Manifest deklariert wird
- [ ] **AUDIT-05**: Das Audit-Log ist ab Werk abgeschaltet und über die Admin-Einstellungen einschaltbar; die Beschriftung sagt, was das Log leistet, was es nicht leistet, und dass ein nutzerbezogenes Protokoll mitbestimmungsrelevant sein kann
- [ ] **AUDIT-06**: Die bestehenden Aussagen ziehen mit: `docs/privacy.md` und `docs/uninstall.md` sagen die neue Wahrheit über Speicherung und Purge, und der Enterprise-Absatz nennt das Audit-Log nicht länger als geplant, in allen drei Sprachen und ohne die verbotenen Wörter revisionssicher, AI-Act-konform, DSGVO-konform und SIEM-zertifiziert

## Future Requirements

Anerkannt, aber nicht in diesem Milestone.

### Auslieferung des Audit-Logs

- **EXAPP-12**: Das Audit-Log samt den mitgezogenen Texten als Release 0.1.12 im Store, nach demselben Runbook wie jedes Release davor. Bewusst aus v1.5 herausgenommen (Owner-Entscheid 2026-08-28): das Modul entsteht im Repo, der Auslieferungszeitpunkt fällt erst, wenn der gebaute Stand vorliegt. Bis dahin bleibt der Store-Text wörtlich korrekt, weil der Store das Manifest nur beim Upload liest. Die Textänderungen aus AUDIT-06 warten so lange im `[Unreleased]`-Block

### openDesk in der Breite (v2.0)

- **OD-04**: OpenProject als Werkzeug `openproject_browse` mit fünf Ebenen plus `wp:<id>` als achte Id-Art für `fetch`; der Schnitt liegt fertig gerechnet in `research/FEATURES.md` bei rund 16700 von 18000 Bytes, wartet aber auf den Ausgang von OD-01 und OD-02
- **OD-05**: Die übrigen openDesk-Komponenten (XWiki, Matrix, OX)
- **OD-06**: Gruppen-Policies als zweiter Enterprise-Baustein
- **OD-07**: Anmeldung über den Identitätsanbieter, den eine Organisation bereits betreibt

### Fortgeschriebenes aus v1.1 bis v1.4

- **CLIENT-01..03**: MUCGPT, F13 und BaerGPT live verproben, sobald externer Zugang besteht (extern getaktet)
- **MAIL-05**: Mail-Entwürfe anlegen, nie senden (Trigger: Store-Feedback)
- **TALK-05**: Talk-Threads, capability-gated

## Out of Scope

| Feature | Reason |
|---------|--------|
| Schreibende OpenProject-Operationen | PATCH ist Überschreiben samt Versionskonflikten, DELETE ist destruktiv; beides bricht das Versprechen "kann konstruktionsbedingt nichts zerstören". Auch "als gelesen markieren" fällt darunter, weil es die teuer erkaufte Eigenschaft "Lesen verändert nichts" aufgäbe |
| Inhaltsstufe `full` im Audit-Log | Erzeugt eine zweite, schlechter geschützte Kopie genau der Mail- und Talk-Inhalte, die der Rest der Architektur schützt |
| Nutzungsstatistiken oder Dashboards über die Audit-Daten | Verhaltens- und Leistungskontrolle löst Mitbestimmung aus und verlängert die Beschaffung, statt sie zu gewinnen; die DSK-Orientierungshilfe nennt Leistungskontrolle aus Protokolldaten ausdrücklich unzulässig |
| Ein Werkzeug `audit_search` | Wäre eine Rechte-Umkehr und Prompt-Injection-Beute: der Assistent könnte lesen, wer ihn wozu benutzt hat |
| Eine Weboberfläche für das Audit-Log | Die belastbare Admin-Erkennung in einer ExApp-Seite ist ungelöst; `occ` ist per Definition administrativ und kostet keine neue Angriffsfläche |
| Ein eigener Keycloak-Client oder ein Dienstkonto für OpenProject | Beide brechen das Versprechen "der Assistent sieht nie mehr als der angemeldete Nutzer" konstruktionsbedingt, nicht durch Nachlässigkeit |
| Das MCP-Token an OpenProject weiterreichen | Von der MCP-Spezifikation ausdrücklich verboten: ein Server darf keine fremden Token annehmen oder weiterleiten |
| Anhebung des Werkzeug-Budgets | Keines der beiden Features fasst die Werkzeugoberfläche an; 15712 von 18000 Bytes bleiben stehen |

## Traceability

Bei der Roadmap-Erstellung am 2026-08-28 gefüllt. Die Phasennummerierung setzt bei 16 fort, weil v1.4 die Phasen 14 und 15 verbraucht hat.

| Requirement | Phase | Status |
|-------------|-------|--------|
| EXAPP-11 | Phase 16 (Release 0.1.11) | Complete |
| OD-01 | Phase 17 (openDesk-Spike) | Pending |
| OD-02 | Phase 17 (openDesk-Spike) | Pending |
| OD-03 | Phase 17 (openDesk-Spike) | Pending |
| AUDIT-01 | Phase 18 (Audit-Log Kern) | Pending |
| AUDIT-02 | Phase 18 (Audit-Log Kern) | Pending |
| AUDIT-03 | Phase 18 (Audit-Log Kern) | Pending |
| AUDIT-04 | Phase 19 (Audit-Log Bedienung und Textnachzug) | Pending |
| AUDIT-05 | Phase 19 (Audit-Log Bedienung und Textnachzug) | Pending |
| AUDIT-06 | Phase 19 (Audit-Log Bedienung und Textnachzug) | Pending |

**Coverage:**
- v1.5 requirements: 10 total
- Mapped to phases: 10
- Unmapped: 0

EXAPP-12 steht per Owner-Entscheid unter Future Requirements und ist bewusst in keiner Phase dieses Meilensteins abgebildet.

---
*Requirements defined: 2026-08-28*
*Last updated: 2026-08-28 nach der Roadmap-Erstellung (Traceability gefüllt, Phasen 16-19)*
