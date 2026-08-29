# Phase 18: Audit-Log Kern - Discussion Log

> **Nur Nachweisspur.** Nicht als Eingabe für Planung, Recherche oder Ausführung nutzen.
> Die Entscheide stehen in `18-CONTEXT.md`; dieser Log hält fest, was zur Wahl stand.

**Date:** 2026-08-29
**Phase:** 18-audit-log-kern
**Areas discussed:** Ablage und Kettenschnitt, Erfassungspunkt und Schreibzeitpunkt,
Verhalten bei Schreibfehler, Inhaltsgrenze je Eintrag, Betriebsgrenzen, Nutzerlöschung,
Eigenwacht

---

## Ablage

| Option | Beschreibung | Gewählt |
|--------|--------------|---------|
| Zweite SQLite-Datei | `audit.sqlite3` neben `store.sqlite3`, eigene Verbindung, eigenes WAL, Muster des OAuth-Speichers | ✓ |
| Append-only JSONL mit Rotation | Eine Zeile je Eintrag, klassische Form für Hash-Ketten, aber Aufbewahrung und Nutzerlöschung als Handarbeit | |
| SQLite in eigenem Unterverzeichnis | Wie Variante 1, getrennt einhängbar, kostet einen Pfad mehr in der Konfiguration | |

**User's choice:** Zweite SQLite-Datei
**Notes:** Gegen ein volles Volume hilft die Obergrenze, nicht die Dateiform. Das wurde in
der Frage ausdrücklich benannt und mitentschieden.

---

## Hash-Kette

| Option | Beschreibung | Gewählt |
|--------|--------------|---------|
| Kette je Nutzer | Nutzerlöschung entfernt eine ganze Kette, die übrigen bleiben ungebrochen; das Löschen eines Strangs fällt nicht auf | ✓ |
| Kette je Nutzer plus Grabstein | Zusätzlich Zeitpunkt, Anzahl und Endhash beim Löschen eines Nutzers; der Grabstein ist selbst ein Datum über einen gelöschten Nutzer | |
| Eine globale Kette, Bruch wird erklärt | Ehrlichste Manipulationserkennung, aber ein regulärer Vorgang hinterlässt dauerhaft eine gebrochene Kette | |

**User's choice:** Kette je Nutzer
**Notes:** Auslöser der Frage ist D-v1.5-01: das Log überlebt Purge und Deinstallation,
gelöscht wird nur durch Frist oder Nutzerlöschung. Für die Obergrenze wurde später (siehe
Betriebsgrenzen) der Grabstein doch gewählt, dort ohne Nutzerbezug.

---

## Erfassungspunkt

| Option | Beschreibung | Gewählt |
|--------|--------------|---------|
| Im `@graceful`-Dekorator | Hängt bereits an allen 21 Werkzeugen, sieht Ergebnis und Fehler; Lückenlosigkeit über einen Vertragstest | ✓ |
| Middleware im MCP-Server | Strukturell nicht umgehbar, hängt aber an dem, was mcp 2.x anbietet | |
| Beides | Auffangnetz plus genaue Werte, dafür doppelte Buchführung mit Entdopplungsregel | |

**User's choice:** Im `@graceful`-Dekorator
**Notes:** Der Vertragstest, der jedes registrierte Werkzeug gegen den Dekorator prüft, ist
Teil der Entscheidung und nicht optional.

---

## Schreibzeitpunkt

| Option | Beschreibung | Gewählt |
|--------|--------------|---------|
| Ein Eintrag nach dem Aufruf | Status und Dauer sofort dabei, eine Zeile je Aufruf; ein Absturz mitten im Aufruf bleibt unsichtbar | ✓ |
| Zwei Einträge, Start und Ende | Abgebrochene Aufrufe sichtbar, doppelte Zeilenzahl | |
| Einer nach dem Aufruf, Start nur bei Langläufern | Wenige Zeilen, hängende Aufrufe sichtbar, dafür eine Schwelle zu pflegen | |

**User's choice:** Ein Eintrag nach dem Aufruf
**Notes:** Die Unsichtbarkeit abgestürzter Aufrufe ist bewusst getragen.

---

## Parameter im Eintrag

| Option | Beschreibung | Gewählt |
|--------|--------------|---------|
| Nur gesetzte Namen aus der Erlaubnisliste | Je Werkzeug eine Liste zulässiger Namen, nie ein Wert, gehalten von einem Vertragstest nach Muster des Budget-Gates | ✓ |
| Gar keine Parameter | Nichts kann durchsickern, ein Prüfer sieht aber nicht einmal, ob ein Filter gesetzt war | |
| Namen plus grobe Form | Mehr Aussage, aber Wertlängen sind bereits ein schwaches Leck | |

**User's choice:** Nur gesetzte Namen aus der Erlaubnisliste

---

## Ergebnisstatus

| Option | Beschreibung | Gewählt |
|--------|--------------|---------|
| Klasse plus Grund bei Ablehnung | gelungen, abgelehnt, fehlgeschlagen; Ablehnungsgrund als feste Kennung, kein Freitext | ✓ |
| Nur gelungen oder fehlgeschlagen | Kürzeste Zeile, erfüllt aber die Forderung nach dem Grund einer Ablehnung nicht | |
| Klasse, Grund und Fehlertext der Werkzeugantwort | Beste Fehlersuche, trägt aber Ergebnisinhalte ins Log und widerspricht AUDIT-01 | |

**User's choice:** Klasse plus Grund bei Ablehnung

---

## Benennung des Clients

| Option | Beschreibung | Gewählt |
|--------|--------------|---------|
| Client-Id, Verbindungs-Id und Client-Name | Aus dem OAuth-Speicher, ohne Adressen und ohne User-Agent | ✓ |
| Nur Verbindungs-Id | Sparsamste Variante, nach dem Trennen nicht mehr auflösbar | |
| Zusätzlich die IP-Adresse | Für Betreiber wertvoll, macht das Log aber zu einem Bewegungsprofil | |

**User's choice:** Client-Id und Verbindungs-Id (mit Client-Name)
**Notes:** Die IP-Variante wurde mit Blick auf die Mitbestimmungsfrage aus AUDIT-05
ausdrücklich verworfen.

---

## Obergrenze

| Option | Beschreibung | Gewählt |
|--------|--------------|---------|
| Älteste löschen plus Grabstein | Ringpuffer, die Lücke wird vom Prüfkommando erklärt statt als Bruch gemeldet | ✓ |
| Älteste löschen ohne Grabstein | Weniger Code, der Kettenanfang wandert unbelegt | |
| Schreibstopp mit Alarm | Nichts geht verloren, aber das Log verstummt, wenn niemand hinsieht | |

**User's choice:** Älteste löschen plus Grabstein

---

## Bereinigung

| Option | Beschreibung | Gewählt |
|--------|--------------|---------|
| Beim Schreiben, gebündelt | Jeder n-te Eintrag prüft Frist und Obergrenze; kein Cron, wirkt auch ohne occ-Aufruf | ✓ |
| Eigenes occ-Kommando | Voll steuerbar, läuft aber nur, wenn jemand daran denkt | |
| Am Heartbeat der ExApp | Kein Aufruf zahlt dafür, hängt aber an einem Pfad für Gesundheitsprüfung | |

**User's choice:** Beim Schreiben, gebündelt

---

## Schalter

| Option | Beschreibung | Gewählt |
|--------|--------------|---------|
| Kern schon hinter dem Schalter, ab Werk aus | Phase 19 hängt nur noch Oberfläche und Beschriftung an | ✓ |
| Kern läuft, Schalter erst in Phase 19 | Leichter zu testen, protokollierte im Zwischenstand aber ungefragt | |

**User's choice:** Kern schon hinter dem Schalter, ab Werk aus

---

## Vorgabewerte

| Option | Beschreibung | Gewählt |
|--------|--------------|---------|
| 180 Tage und 100 MB | Frist auf der geforderten Untergrenze, Größe großzügig, in der Praxis greift die Frist | ✓ |
| 365 Tage und 250 MB | Wie in Betriebsvereinbarungen üblich, aber ein Jahr nutzerbezogener Daten | |
| 90 Tage und 50 MB | Datensparsam, erfüllt die 180 Tage nur über die Einstellung | |

**User's choice:** 180 Tage und 100 MB

---

## Nutzerlöschung

| Option | Beschreibung | Gewählt |
|--------|--------------|---------|
| Beim gebündelten Aufräumen nachfragen | Prüft für alte Ketten, ob das Konto noch existiert; ein Weg, keine neue Route, verzögert die Löschung | ✓ |
| Eigenes occ-Kommando | Sofort und nachvollziehbar, passiert aber nur auf Zuruf | |
| Über AppAPI zustellen lassen, falls möglich | Sauberste Lösung, kostet eine Messung und fiele im Fehlschlag doch auf Variante 1 zurück | |

**User's choice:** Beim gebündelten Aufräumen nachfragen

---

## Eigenwacht

| Option | Beschreibung | Gewählt |
|--------|--------------|---------|
| Ja, als eigene Eintragsart mit Administrator | Ein Eintrag beim Ein- und beim Ausschalten in einer eigenen Kette für Instanzereignisse | ✓ |
| Ja, aber ohne Namen des Administrators | Lücke belegt, ohne dass ein Administrator selbst Protokollgegenstand wird | |
| Nein, nur Werkzeugaufrufe | Weniger Code, aber die Lücke nach Aus und Ein bleibt unerklärt | |

**User's choice:** Ja, als eigene Eintragsart

---

## Claude's Discretion

- Hash-Verfahren und Kanonisierung der Felder
- Tabellenschnitt, Indizes und Pragmas der neuen Datei
- Name und genaue Form des Prüfkommandos (der Weg über occ ohne Manifest-Route steht fest)
- Die Schwelle für die Existenzprüfung und das Bündelungsintervall der Bereinigung
- Zuschnitt der Erlaubnislisten je Werkzeug
- Aufteilung in Pläne und Wellen

## Deferred Ideas

- AUDIT-04 (Lesen und Exportieren), AUDIT-05 (Beschriftung, Mitbestimmungshinweis) und
  AUDIT-06 (Textnachzug) bleiben Phase 19
- EXAPP-12 (Release 0.1.12) bleibt ausserhalb des Milestones v1.5
- Ereignisweg über AppAPI für die Nutzerlöschung
- IP-Adresse oder User-Agent im Eintrag
