# Phase 4: Per-User-Verwaltung und prepare_context - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-08-16
**Phase:** 4-Per-User-Verwaltung und prepare_context
**Areas discussed:** Wo die Verwaltung lebt, Was der Ausschalter tut, Wie prepare_context relevant findet, Antwortform und Degradation, Standardzustand, Reichweite des Schalters, Zeitbudget

---

## Wo die Verwaltung lebt

| Option | Description | Selected |
|--------|-------------|----------|
| Schalter in NC, Liste bei uns | Declarative Settings tragen Schalter und Link, die Client-Tabelle mit Widerruf je Zeile liegt auf einer eigenen Seite | ✓ |
| Alles auf unserer Seite | In den Nextcloud-Einstellungen nur ein Link | |
| Alles in Declarative Settings | Client-Liste als Nur-Text, Widerruf nur alles oder nichts | |

**User's choice:** Schalter in NC, Liste bei uns
**Notes:** Die dritte Option hätte SC 2 verfehlt, das den Widerruf einzelner Tokens verlangt. Declarative Settings sind ein Formular ohne eigene Logik.

---

## Was der Ausschalter tut

| Option | Description | Selected |
|--------|-------------|----------|
| Sperren, im eigenen Store gespiegelt | Flag im eigenen Store, Bearer-Prüfung liest es mit, kein zweiter Nextcloud-Roundtrip | ✓ |
| Sperren, Flag je Aufruf aus Nextcloud lesen | Immer die Wahrheit aus Nextcloud, dafür doppelte Last | |
| Ausschalten widerruft alle Tokens | Unmissverständlich, aber nicht umkehrbar | |

**User's choice:** Sperren, im eigenen Store gespiegelt
**Notes:** Die zweite Option hätte SC 5 aus Phase 3 (ein Roundtrip je MCP-Aufruf, live gemessen) hinfällig gemacht. Der Widerruf bleibt als eigene, benannte Handlung erhalten.

---

## Wie prepare_context relevant findet

| Option | Description | Selected |
|--------|-------------|----------|
| Suche plus Zeitfenster | Inhalte über unified_search, Termine über einen direkten Aufruf | ✓ |
| Nur unified_search | Ein Einstieg, ein Berechtigungspfad | |
| Fan-out je Quelle, ohne unified_search | Jede Quelle direkt, volle Kontrolle | |

**User's choice:** Suche plus Zeitfenster
**Notes:** Der Owner hat auf die parallel entstehende Suche Findling hingewiesen und auf die dort bereits erkannte Verbindung. Sie trägt die Entscheidung: Solange alles über die Unified Search läuft, liefert ein installiertes Findling automatisch Inhaltstreffer bis in gescannte PDFs, ohne Code hier und ohne Nextcloud als einzige Berechtigungsgrenze aufzugeben. Die dritte Option hätte genau das zerstört.

---

## Antwortform und Degradation

| Option | Description | Selected |
|--------|-------------|----------|
| Kurz = Titel und Ids, Voll = mit Auszug | Der Assistent entscheidet selbst, ob er nachlädt | ✓ |
| Kurz = weniger Treffer, Voll = mehr | Gleiche Tiefe, andere Anzahl | |
| Kurz = nur die stärkste Quelle | Sehr sparsam, verfehlt das Bündeln | |

**User's choice:** Kurz = Titel und Ids, Voll = mit Auszug
**Notes:** Die Degradation war nicht zur Wahl gestellt, sondern als gesetzt benannt: dieselbe Form wie unified_search heute, eine Liste ausgefallener Quellen mit Grund.

---

## Standardzustand für einen neuen Nutzer

| Option | Description | Selected |
|--------|-------------|----------|
| An | Wer verbindet, hat bereits zugestimmt; der Schalter ist die Notbremse | ✓ |
| Aus, Nutzer muss erst zustimmen | Opt-in, strenger, erzeugt aber eine Sackgasse nach erfolgreicher Verbindung | |
| Aus, aber die Consent-Seite schaltet mit ein | Vermeidet die Sackgasse, macht den Schalter aber schwer erklärbar | |

**User's choice:** An
**Notes:** Ausschlaggebend war die Sackgasse: Verbindung gelingt, erster Tool-Aufruf scheitert, Ursache steht woanders.

---

## Reichweite des Schalters

| Option | Description | Selected |
|--------|-------------|----------|
| Jeden Zugriff auf /mcp | OAuth und App-Passwort-Pfad gleichermaßen | ✓ |
| Nur OAuth-Verbindungen | Passt zur Verbindungsverwaltung dieser Phase, lässt aber einen zweiten Weg offen | |

**User's choice:** Jeden Zugriff auf /mcp
**Notes:** Ein Schalter, der sichtbar sperrt und dabei einen Weg offen lässt, ist in einem Audit nicht zu verteidigen.

---

## Zeitbudget von prepare_context

| Option | Description | Selected |
|--------|-------------|----------|
| Schnell antworten, Ausfall benennen | Hartes Gesamtbudget, Rest unter degraded mit Grund | ✓ |
| Warten, bis alles da ist | Vollständigkeit vor Tempo | |
| Der Aufrufer entscheidet per Parameter | Ein Feld mehr im Schema | |

**User's choice:** Schnell antworten, Ausfall benennen
**Notes:** Deckt sich mit dem Verhalten von unified_search und hält das CI-Token-Budget frei.

---

## Claude's Discretion

- Trefferzahlen je Quelle in Kurz und Voll, die konkreten Sekunden des Gesamtbudgets und deren Aufteilung
- Ob die Client-Tabelle eine eigene Route bekommt oder unter `/connect` wächst
- Der technische Weg, auf dem Declarative Settings registriert werden und ihre Änderung den Store erreicht
- Wortlaut aller Seitentexte im Ton von Phase 3

## Deferred Ideas

- Cursor und private-use URI schemes (BL-04), Entscheidung gehört zu Phase 5 SC 4
- Client ID Metadata Documents (BL-05)
- WR-08, WR-10, WR-12 als Restrisiken AR-03-06 bis AR-03-08, vor der Store-Einreichung prüfen
- Admin-Sicht auf die Verbindungen aller Nutzer, gehört zu AUTH-07 und nicht hierher
