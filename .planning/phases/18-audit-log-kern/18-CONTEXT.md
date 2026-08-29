# Phase 18: Audit-Log Kern - Context

**Gathered:** 2026-08-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Jeder Aufruf eines der 21 Werkzeuge hinterlässt einen prüfbaren Eintrag, der weder
Parameterwerte noch Ergebnisinhalte trägt, mit seinem Vorgänger hash-verkettet ist und in
einer eigenen Ablage neben dem OAuth-Speicher liegt. Die Ablage hat eine Obergrenze und
eine Aufbewahrungsfrist und kann den OAuth-Speicher nicht schreibunfähig machen.

Diese Phase liefert den Kern: Erfassung, Ablage, Kette, Grenzen, Prüfkommando.

Nicht in dieser Phase: die Bedienung (AUDIT-04 Lesen und Exportieren über occ), die
sichtbare Admin-Beschriftung samt Mitbestimmungshinweis (AUDIT-05) und der Textnachzug in
`docs/privacy.md`, `docs/uninstall.md` und dem Enterprise-Absatz (AUDIT-06). Alle drei sind
Phase 19. Die Auslieferung als Release 0.1.12 (EXAPP-12) ist bewusst nicht Teil des
Milestones v1.5.

</domain>

<decisions>
## Implementation Decisions

### Ablage

- **D-01:** Das Log liegt in einer **zweiten SQLite-Datei** neben `store.sqlite3` im selben
  Volume, mit eigener Verbindung und eigenem WAL, nach dem Muster von
  `src/mcp_connector/oauth/store.py`. Begründung: Prüfkommando, Aufbewahrung und
  Nutzerbereinigung sind damit SQL statt Dateiakrobatik. Die Trennung vom OAuth-Speicher ist
  eine Trennung der Dateien und der Verbindungen, nicht der Volumes: gegen ein volles Volume
  hilft die Obergrenze aus D-08, nicht die Dateiform. Ein eigenes Verzeichnis für getrenntes
  Einhängen wurde erwogen und verworfen (ein Pfad mehr in der Konfiguration ohne Gewinn für
  die geforderten Kriterien).

### Hash-Kette

- **D-02:** **Eine Kette je Nutzer.** Die Löschung eines Nutzers in Nextcloud entfernt dann
  eine ganze Kette am Stück, ohne die Ketten der übrigen Nutzer zu brechen (D-v1.5-01
  verlangt genau diese Löschung). Der bewusst getragene Preis: das Verschwinden eines
  kompletten Nutzerstrangs fällt dem Prüfkommando nicht auf. Eine globale Kette wurde
  verworfen, weil ein regulärer Vorgang sie dauerhaft gebrochen zurückließe.
- **D-03:** Instanzereignisse (D-15) laufen in einer **eigenen zweiten Kettenart**, getrennt
  von den Nutzerketten.

### Erfassung

- **D-04:** Erfasst wird im vorhandenen **`@graceful`-Dekorator** in
  `src/mcp_connector/server/__init__.py`, der bereits an allen 21 Werkzeugen hängt und
  Ergebnis wie Fehler sieht. "Kein Werkzeug kann daran vorbei" wird nicht behauptet, sondern
  von einem **Vertragstest** gehalten, der jedes registrierte Werkzeug gegen den Dekorator
  prüft; ein künftiges Werkzeug ohne Dekorator lässt diesen Test fehlschlagen. Eine
  Server-Middleware wurde verworfen, weil sie an dem hängt, was mcp 2.x an dieser Stelle
  anbietet, und Werkzeugnamen und Fehlerklassen ungenauer sieht.
- **D-05:** **Ein Eintrag nach dem Aufruf**, mit Ergebnisstatus und Dauer, eine Zeile je
  Aufruf. Bewusst getragen: ein Absturz mitten im Aufruf hinterlässt keinen Eintrag, der
  Aufruf bleibt unsichtbar. Start- und Ende-Paare wurden verworfen, weil sie die Zeilenzahl
  und damit den Verbrauch der Obergrenze verdoppeln.

### Inhalt eines Eintrags

- **D-06:** Ein Eintrag trägt: Nutzer, Werkzeugname, Zeitpunkt, aufrufenden Client,
  Ergebnisstatus, Dauer, Hash des Vorgängers und eigenen Hash. **Von den Parametern nur die
  gesetzten Namen aus einer Erlaubnisliste je Werkzeug, niemals ein Wert.** Ein Vertragstest
  nach dem Muster des Budget-Gates (`scripts/check_tool_budget.py`,
  `tests/contract/test_tool_surface.py`) schlägt fehl, sobald ein Werkzeug diese Grenze
  überschreitet. Grobe Formangaben wie Wertlängen wurden verworfen: eine Länge ist bereits
  ein schwaches Leck.
- **D-07:** Der Ergebnisstatus ist eine **Klasse** (gelungen, abgelehnt, fehlgeschlagen);
  bei einer Ablehnung kommt der Grund als **feste Kennung** dazu (fehlende Berechtigung,
  unbekannte Id, Zeitüberschreitung, Sicherung gegriffen). Kein Freitext und kein Fehlersatz
  der Werkzeugantwort, denn das wäre Ergebnisinhalt und verstieße gegen AUDIT-01.
- **D-08:** Der aufrufende Client steht als **Client-Id, Verbindungs-Id und der bei der
  Registrierung genannte Client-Name** aus dem OAuth-Speicher. **Keine IP-Adresse und kein
  User-Agent**: das machte das Log zu einem Bewegungsprofil und verschärfte die
  Mitbestimmungsfrage aus AUDIT-05 unnötig.

### Grenzen und Aufbewahrung

- **D-09:** Vorgabewerte: **Aufbewahrungsfrist 180 Tage, Obergrenze 100 MB**, beide
  einstellbar. Die Frist liegt damit genau auf der geforderten Untergrenze, die Größe
  großzügig, so dass in der Praxis die Frist greift und nicht die Größe.
- **D-10:** Ist die Obergrenze erreicht, weichen die **ältesten Einträge, und ein Grabstein**
  hält Zeitpunkt, Anzahl und Endhash fest, damit das Prüfkommando die Lücke erklären kann
  statt sie als Bruch zu melden. Ein Schreibstopp wurde verworfen: das Log verstummte genau
  dann, wenn niemand hinsieht.
- **D-11:** Abgelaufene Einträge räumt der **Schreibpfad selbst gebündelt ab** (jeder n-te
  Eintrag prüft nebenbei Frist und Obergrenze). Kein Cron, kein Hintergrunddienst, wirksam
  auch auf einer Instanz, die nie ein occ-Kommando sieht. Der Preis, dass gelegentlich ein
  Aufruf die Aufräumkosten trägt, ist bewusst getragen.
- **D-12:** Von der **Löschung eines Nutzers in Nextcloud** erfährt das Modul über denselben
  gebündelten Aufräumlauf: für Nutzer, deren letzter Eintrag älter als eine Schwelle ist,
  wird geprüft, ob das Konto noch existiert; fehlt es, fällt die ganze Kette samt Grabstein.
  Ein Weg, keine neue Route. Bewusst getragen: die Löschung verzögert sich bis zum nächsten
  Lauf. Ein Ereignisweg über AppAPI wurde nicht gewählt, weil er erst gemessen werden müsste
  und im Fehlschlag doch auf diesen Weg zurückfiele.

### Verhalten im Fehlerfall

- **D-13:** **Fail-open mit Alarm.** Kann das Log nicht schreiben (Volume voll, Datei
  defekt), läuft der Werkzeugaufruf trotzdem; der Fehlschlag geht ins Nextcloud-Log und wird
  vom Prüfkommando als Lücke sichtbar. Nextcloud bleibt bedienbar, das Log ist dann
  nachweislich unvollständig. Fail-closed wurde verworfen: ein volles Volume legte sämtliche
  KI-Zugriffe still.

### Schalter

- **D-14:** Der Kern liegt **schon in dieser Phase hinter dem Schalter, ab Werk aus**, als
  Konfigurationswert nach dem Muster von `src/mcp_connector/exapp/config_values.py`. Phase 19
  hängt nur noch Bedienoberfläche und Beschriftung daran. Kein Zwischenstand, in dem ein
  nutzerbezogenes Protokoll ungefragt mitläuft.
- **D-15:** Das **Ein- und Ausschalten des Logs wird selbst protokolliert**, als eigene
  Eintragsart in der Kette der Instanzereignisse (D-03), mit Zeitpunkt, Richtung und dem
  handelnden Administrator. Sonst ließe sich das Log abschalten, handeln und wieder
  einschalten, ohne dass die Lücke einen Namen hat.

### Claude's Discretion

- Das Hash-Verfahren und die Kanonisierung der Felder (naheliegend SHA-256 über eine
  festgelegte Feldreihenfolge, wie `store.py` es für Token-Digests hält).
- Tabellenschnitt, Indizes und Pragmas der neuen Datei, solange sie dem Muster von
  `store.py` folgen (WAL, `busy_timeout`, Arbeit in `asyncio.to_thread`).
- Name und genaue Form des Prüfkommandos. Der Weg steht fest: über AppAPI-`PublicFunctions`
  wie `occ mcp_connector:purge`, **ohne neue Route im Manifest** (`exapp/purge.py` erklärt,
  warum eine deklarierte Route eine instanzweite Wirkung ins Internet stellte).
- Die Schwelle in D-12 und das Bündelungsintervall in D-11.
- Der Zuschnitt der Erlaubnislisten je Werkzeug, solange kein Wert und kein Inhalt darin
  landet.
- Die Aufteilung in Pläne und Wellen.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Auftrag und Anforderungen
- `.planning/ROADMAP.md` §Phase 18 — Ziel und die fünf Erfolgskriterien, darunter D-v1.5-01
- `.planning/REQUIREMENTS.md` — AUDIT-01, AUDIT-02, AUDIT-03 (diese Phase); AUDIT-04 bis
  AUDIT-06 (Phase 19, nicht hier bauen); EXAPP-12 (Auslieferung, nicht im Milestone)

### Muster, denen dieses Modul folgt
- `src/mcp_connector/oauth/store.py` — SQLite ohne Fremdbibliothek, WAL, `busy_timeout`,
  `asyncio.to_thread`, kein modulweiter Zustand, Digest statt Klartext. Das Vorbild der
  neuen Ablage
- `src/mcp_connector/exapp/purge.py` — occ-Kommando über AppAPI-`PublicFunctions` ohne Route
  im Manifest, und die Begründung, warum eine Route hier gefährlich wäre. Vorbild für das
  Prüfkommando; ausserdem der Ort, an dem D-v1.5-01 (Log überlebt Purge) sichtbar wird
- `src/mcp_connector/server/__init__.py` — `graceful`, `compact` und die Registrierung aller
  Werkzeuge. Der Erfassungspunkt aus D-04
- `scripts/check_tool_budget.py` und `tests/contract/test_tool_surface.py` — das Muster des
  Budget-Gates, dem der Vertragstest aus D-06 nachgebaut wird
- `src/mcp_connector/exapp/config_values.py` und
  `src/mcp_connector/exapp/admin_settings.py` — wie ein Admin-Wert gelesen und gehalten wird
  (Schalter aus D-14)
- `appinfo/info.xml` — der Kommentar über die bewusst abwesenden Routen

### Texte, die erst in Phase 19 mitziehen (hier nur lesen, nicht ändern)
- `docs/privacy.md` — sagt heute, was gespeichert wird
- `docs/uninstall.md` — sagt heute, was beim Entfernen verschwindet

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `oauth/store.py`: vollständiges Muster für eine SQLite-Ablage in diesem Projekt, samt
  Begründung gegen aiosqlite und für die drei Pragmas. Die neue Datei erbt Aufbau und Regeln,
  teilt aber weder Verbindung noch Datei.
- `@graceful` in `server/__init__.py`: hängt bereits an allen 21 Werkzeugen und sieht
  Rückgabe wie Ausnahme. Erfassung braucht dort keinen neuen Aufrufweg.
- `exapp/purge.py`: zeigt den occ-Weg über `PublicFunctions` und die Doppelprüfung
  (`x-origin-ip` bedeutet PHP-Proxy und wird mit 404 beantwortet, dann `require_appapi`).
- `scripts/check_tool_budget.py`: gewachsenes Gate-Muster, an dem sich der Vertragstest für
  die Erlaubnisliste ausrichtet.

### Established Patterns
- Kein modulweiter veränderlicher Zustand: Speicher sind Objekte, die ihren Pfad und ihren
  Schlüssel bekommen.
- Keine neue direkte Abhängigkeit ohne Not (`docs/dependency-audit.md` ist eine bewusste
  Entscheidung). Das Audit-Log kommt mit der Standardbibliothek aus.
- Keine neuen Routen im Manifest. Was ein Administrator tut, tut er über occ.
- Verbotene Wörter in allen öffentlichen Texten: revisionssicher, AI-Act-konform,
  DSGVO-konform, SIEM-zertifiziert (AUDIT-06). Gilt schon hier für Kommentare und Doku, die
  in dieser Phase entstehen.

### Integration Points
- `@graceful` schreibt den Eintrag (D-04).
- Der Admin-Schalter kommt aus den bestehenden ExApp-Konfigurationswerten (D-14).
- Client- und Verbindungs-Id kommen aus dem OAuth-Speicher (D-08); das Audit-Log liest sie,
  schreibt aber nie in `store.sqlite3`.
- `purge.py` und die Deinstallation lassen die neue Datei ausdrücklich stehen (D-v1.5-01) —
  das ist eine Änderung an der Aufräumlogik, die belegt werden muss.

</code_context>

<specifics>
## Specific Ideas

- Der Vertragstest ist ausdrücklich nach dem Muster des Budget-Gates zu bauen: eine Messung
  über alle registrierten Werkzeuge, die bei Überschreitung fehlschlägt, nicht eine
  Stichprobe.
- Das Prüfkommando muss bei einer gebrochenen Kette **die erste gebrochene Stelle benennen**,
  nicht nur "gebrochen" melden. Eine nachträglich veränderte Zeile muss es finden; das gehört
  als Test mit einer von Hand veränderten Zeile in die Phase.
- Grabsteine (D-10, D-12) sind der Unterschied zwischen einer erklärten und einer
  unerklärten Lücke. Das Prüfkommando muss beide auseinanderhalten können.

</specifics>

<deferred>
## Deferred Ideas

- Ausgabe und Export des Logs für Administratoren — AUDIT-04, Phase 19.
- Sichtbare Admin-Beschriftung samt Mitbestimmungshinweis — AUDIT-05, Phase 19. Der Schalter
  selbst entsteht schon hier (D-14), nur ohne Oberfläche.
- Textnachzug in `docs/privacy.md`, `docs/uninstall.md` und im Enterprise-Absatz — AUDIT-06,
  Phase 19.
- Auslieferung als Release 0.1.12 — EXAPP-12, bewusst ausserhalb des Milestones v1.5.
- Ein Ereignisweg über AppAPI für die Nutzerlöschung — verworfen für diese Phase (D-12),
  könnte später gemessen werden, falls AppAPI so etwas anbietet.
- IP-Adresse oder User-Agent im Eintrag — verworfen (D-08), nicht wieder aufmachen ohne
  ausdrücklichen Owner-Entscheid.

</deferred>

---

*Phase: 18-audit-log-kern*
*Context gathered: 2026-08-29*
