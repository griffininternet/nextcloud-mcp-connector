# Phase 4: Per-User-Verwaltung und prepare_context - Context

**Gathered:** 2026-08-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Zwei Dinge, die beide dem Nutzer gehören: er kontrolliert den MCP-Zugriff selbst in den
Nextcloud-Einstellungen (EXAPP-02), und ein einziger `prepare_context`-Aufruf bündelt den
relevanten Cloud-Kontext token-effizient (TOOL-08).

NICHT in dieser Phase: alles, was der Admin steuert (die Client-Allowlist und der
DCR-Schalter sind AUTH-07 und stehen seit Phase 3), die Store-Einreichung und die
Signatur (Phase 5), die offenen Review-Punkte WR-08, WR-10 und WR-12 (Restrisiken
AR-03-06 bis AR-03-08, bewusst zurückgestellt), und die Cursor-Entscheidung aus BL-04,
die laut Roadmap zu Phase 5 SC 4 gehört.

</domain>

<decisions>
## Implementation Decisions

### Wo die Verwaltung lebt

- **D-44:** Geteilt, nach der Fähigkeit des jeweiligen Werkzeugs. Die Nextcloud-Einstellungen
  tragen über Declarative Settings den Ein/Aus-Schalter und einen Link; die Tabelle der
  verbundenen Clients mit Widerruf je Zeile liegt auf einer eigenen Seite dieser ExApp.
  Grund: Declarative Settings sind ein Formular ohne eigene Logik, eine Zeile mit Knopf je
  Verbindung ist damit nicht zu bauen, und SC 2 verlangt den Widerruf einzelner Tokens.
  Der Nutzer findet den Einstieg trotzdem dort, wo Nextcloud seine App-Schalter zeigt.
- **D-45:** Die eigene Seite baut auf der Seiten-Infrastruktur aus Phase 3 auf
  (`exapp/ui/layout.py`, `strings.py`, `icons.py`), nicht auf einer zweiten Bauweise.
  Dieselbe Kopfzeile, dieselbe Fußzeile, dieselben Sicherheitshinweise: die Consent-Seite
  hat den Ton dieser App bereits festgelegt.

### Was der Ausschalter tut

- **D-46:** Der Schalter sperrt, er widerruft nicht. Tokens überleben, Wiedereinschalten
  stellt jede Verbindung wieder her. Ein Widerruf bleibt die eigene, benannte Handlung
  (Zeile in der Tabelle, oder Nextclouds "Geräte und Sitzungen").
- **D-47:** Der Zustand des Schalters wird in unserem eigenen Store geführt, und die
  Bearer-Grenze liest ihn dort. Er darf **keinen** zweiten Nextcloud-Roundtrip je Anfrage
  kosten: Phase 3 hat einen Roundtrip je MCP-Aufruf gemessen (SC 5, `03-VERIFICATION.md`),
  und diese Zahl bleibt die Obergrenze. Wie die Änderung aus den Declarative Settings in
  den Store kommt, klärt die Recherche; ein Poll ist die schlechteste der denkbaren
  Antworten.
- **D-48:** "Sofort" heißt: der nächste Tool-Aufruf nach dem Umlegen scheitert, nicht der
  übernächste. Ein Zwischenspeicher, der das aufweicht, ist keine Lösung. Wenn eine
  Spiegelung ohne Verzögerung nicht möglich ist, wird das im Plan benannt und nicht
  weggerundet.
- **D-49:** Der Schalter sperrt **jeden** Zugriff auf `/mcp`, OAuth-Verbindungen und den
  App-Passwort-Pfad aus Phase 1 gleichermaßen. Ein Schalter, der sichtbar etwas sperrt und
  dabei einen zweiten Weg offen lässt, ist in einem Audit nicht zu verteidigen.
- **D-50:** Standard für einen Nutzer, der die App nie geöffnet hat: **an**. Wer einen
  Connector verbindet, hat den Zugriff bereits bewusst genehmigt (Consent-Seite,
  Nextcloud-Anmeldung, "Approve access"). Ein zweiter Schalter davor erzeugt die Sackgasse,
  in der die Verbindung gelingt und der erste Tool-Aufruf trotzdem scheitert. Der Schalter
  ist die Notbremse, nicht der Türsteher.
- **D-51:** Die Ablehnung bei ausgeschaltetem Zugriff sagt, was los ist, und nennt den Ort,
  an dem der Nutzer es ändern kann. Sie ist von der Ablehnung eines ungültigen Tokens
  unterscheidbar, denn hier ist der Client in Ordnung und die Entscheidung war eine
  bewusste. Wortlaut gehört ins UI-SPEC.

### Wie prepare_context relevant findet

- **D-52:** Zwei Wege, nach der Art der Frage. Inhalte kommen über `unified_search`, Termine
  über einen direkten Aufruf mit Zeitfenster. Grund: "diese Woche" beantwortet keine
  Volltextsuche, und ein Bündel ohne die nächsten Termine verfehlt seinen Zweck.
- **D-53:** Kein Direktdraht zu einem Suchindex, auch nicht zu Findling. Alles läuft über
  die Unified Search, damit Nextcloud die einzige Berechtigungsgrenze bleibt. Nebeneffekt,
  der die Entscheidung trägt: Der Provider wird zur Laufzeit gelesen (D-08,
  `tools/search.py`), also liefert ein installiertes Findling automatisch Inhaltstreffer
  bis in gescannte PDFs, ohne eine Zeile Code hier. Siehe BL-01 bis BL-03.

### Antwortform und Degradation

- **D-54:** Kurz liefert je Treffer Titel, Quelle und die Id, mit der ein Folgetool nachladen
  kann. Voll hängt einen begrenzten Textauszug an. Der Assistent entscheidet selbst, ob er
  nachlädt, und das Token-Budget bleibt vorhersagbar.
- **D-55:** Degradation in derselben Form wie `unified_search` heute: eine Liste der
  ausgefallenen oder abgeschnittenen Quellen mit Name und Grund. Keine neue Form für
  dasselbe Problem, und SC 4 verbietet stille Teil-Ergebnisse.
- **D-56:** Hartes Gesamtbudget, deutlich unter dem Timeout eines üblichen Clients. Was
  nicht rechtzeitig da ist, erscheint unter `degraded`. Kein Budget-Parameter im Schema:
  ein Feld mehr zählt gegen das CI-Token-Budget, und ein Assistent trifft diese Wahl selten
  sinnvoll.

### Nachtrag Owner 17.08. (während der Recherche ergänzt)

- **D-57 (Injection):** `prepare_context` bündelt Inhalte, die andere geschrieben haben
  können: geteilte Dateien, Kalendereinladungen fremder Absender, Deck-Karten anderer
  Board-Mitglieder. Das Bündel-Tool vergrößert damit die Fläche für Prompt-Injection
  gegenüber Einzel-Reads, weil ein Aufruf viele fremde Texte auf einmal in den Kontext des
  Assistenten hebt. Der Plan muss das im Threat-Model führen und mindestens festschreiben:
  jeder Treffer trägt seine Herkunft (Quelle + Id) als Struktur, nie als Fließtext;
  Auszüge sind Daten und werden nicht mit Anweisungs-Rahmung ("the user wants…")
  angereichert; die Tool-Description warnt den Client, dass Inhalte Dritter enthalten sein
  können (dieselbe Ehrlichkeit wie die "Unverified client"-Callout in Phase 3); und es
  gibt einen Guard-Test, der belegt, dass ein Treffertext mit Anweisungs-Injection
  unverändert als Datenfeld ankommt statt Struktur oder Felder der Antwort zu verschieben.
  Keine Inhalts-Filterung/Maskierung (Owner-Entscheid 14.08.: Maskierung ist
  Scheinsicherheit); die Verteidigung ist Struktur und Kennzeichnung, nicht Zensur.
- **D-58 (Contract-Gate):** Das bestehende Gate in `tests/contract/test_tool_surface.py`
  ist die Wahrheit über die Tool-Oberfläche und bleibt es: `EXPECTED_TOOLS` ist ein
  eingefrorenes Literal (ein 16. Tool schlägt fehl, bis es bewusst eingetragen wird), und
  `test_the_readme_permission_table_matches_the_live_registry` erzwingt Mengengleichheit
  README-Tabelle vs. Live-Registry samt Permission-Level. Der Plan für `prepare_context`
  muss daher in EINEM Zug liefern: Eintrag in `EXPECTED_TOOLS`, Zeile in der
  README-Permission-Tabelle (`read`), ehrliche Annotationen im Stil der bestehenden
  Einzeltests, und einen eigenen Oberflächen-Test wie ihn jedes andere Tool hat. Das
  CI-Token-Budget (`scripts/check_tool_budget.py`) gilt unverändert.

### Claude's Discretion

- Die Zahl der Treffer je Quelle in Kurz und Voll, die konkreten Sekunden des Gesamtbudgets
  und die Aufteilung auf die Teilquellen. Größenordnungen gehören in den Plan, nicht in
  diese Diskussion.
- Ob die Client-Tabelle eine eigene Route bekommt oder unter den bestehenden `/connect`-Pfad
  wächst, und wie die Declarative Settings technisch registriert werden.
- Wortlaut aller Seitentexte, im Rahmen des Tons, den Phase 3 gesetzt hat.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Was die Phase schuldet
- `.planning/ROADMAP.md` §"Phase 4" — Ziel, vier Erfolgskriterien, `UI hint: yes`
- `.planning/REQUIREMENTS.md` — EXAPP-02 (Declarative Settings ist dort ausdrücklich
  genannt) und TOOL-08

### Woran sich Phase 4 messen lassen muss
- `.planning/phases/03-oauth-2-1/03-VERIFICATION.md` — SC 5, ein Nextcloud-Roundtrip je
  MCP-Aufruf. D-47 darf diese Zahl nicht verschlechtern
- `.planning/phases/03-oauth-2-1/03-SECURITY.md` — die zehn Restrisiken AR-03-01 bis
  AR-03-10 und der Grund, warum `/mcp` PUBLIC ist
- `.planning/phases/03-oauth-2-1/03-REVIEW.md` — WR-08, WR-10, WR-12 stehen offen und
  gehören **nicht** in diese Phase, dürfen aber nicht schlimmer werden
- `.planning/phases/02-exapp-shell/02-SECURITY.md` — AR-02-04 samt Nachtrag: wie eine
  Access-Level-Entscheidung im Manifest zu begründen ist

### Wie hier gebaut wird
- `docs/oauth-setup.md` §"Security notes for production" — der Widerruf, die Allowlist und
  warum das Entfernen im Client nichts widerruft
- `docs/client-setup.md` — der Ton der Nutzertexte und die Client-Eigenheiten
- `src/mcp_connector/tools/search.py` — Fan-out, Timeout je Provider, `degraded` mit Grund.
  Das Muster für D-52, D-55 und D-56 existiert dort bereits
- `src/mcp_connector/exapp/ui/layout.py`, `strings.py`, `icons.py` — die Seiten-Bauweise
  aus Phase 3, auf der D-45 aufsetzt
- `appinfo/info.xml` — die zwölf deklarierten Routen und der lange Kommentar dazu. Jede
  neue Route dieser Phase erweitert die Angriffsfläche und braucht dieselbe Begründung
- `.planning/BACKLOG.md` — BL-01 bis BL-03 (Findling-Synergie, Grundlage von D-53),
  BL-04 und BL-05

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `tools/search.py`: paralleler Fan-out mit hartem Timeout je Provider
  (`PER_PROVIDER_TIMEOUT = 15.0`) und einer `degraded`-Liste mit Name und Grund. Genau die
  Eigenschaft, die SC 4 verlangt, in erprobter Form.
- `exapp/ui/`: `layout.py`, `strings.py`, `icons.py`, dazu `consent.py` und `connect.py` als
  zwei fertige Beispiele einer Seite dieser App, samt strenger CSP und `form-action 'self'`.
- `oauth/store.py`: der Ort, an dem Verbindungen, Autorisierungen und Tokens liegen. Die
  Tabelle der verbundenen Clients (SC 2) liest von dort, und der Widerruf ist als
  `/revoke`-Weg bereits gebaut und live gemessen.
- Die vier Client-Module unter `nextcloud/clients/` für den Zeitfenster-Teil von D-52.

### Established Patterns
- Eine Route existiert nur, wenn sie im Manifest deklariert ist, mit vollständig verankertem
  Muster (AR-02-06 wurde in Phase 3 genau daran geschlossen).
- Jede Ablehnung nennt die Regel und niemals einen Wert aus der Anfrage (T-03-66).
- Jeder Fund bekommt einen Wächter-Test, der ohne den Fix rot ist. Das gilt in dieser Phase
  auch für den Schalter: ein Test, der ohne die Sperre grün bliebe, ist keiner.
- Zahlen in Dokumenten nennen den Befehl, der sie erzeugt hat, und das Datum.

### Integration Points
- Die Bearer-Grenze in `exapp/middleware.py` ist der Ort, an dem D-47 und D-49 wirken. Sie
  entscheidet heute über Token und Identität; sie entscheidet künftig auch über den Schalter,
  und zwar für beide Anschlussarten.
- Die Tool-Registrierung, in die `prepare_context` als weiteres Tool einzieht. Das
  CI-Token-Budget (`scripts/check_tool_budget.py`) ist die Grenze, die dabei gilt.
- Die Declarative Settings müssen bei Nextcloud registriert werden; der Weg dorthin führt
  über AppAPI und ist Sache der Recherche.

</code_context>

<specifics>
## Specific Ideas

- Der Owner hat auf die parallel entstehende Suche **Findling** hingewiesen und auf die
  Verbindung, die dort schon erkannt wurde. Sie ist der Grund für D-53: `prepare_context`
  erbt die Inhaltstreffer geschenkt, solange alles über die Unified Search läuft. Ein
  Direktdraht würde diese Eigenschaft zerstören und Nextcloud als einzige
  Berechtigungsgrenze aufgeben, was beide Threat-Models verbieten.
- Der Schalter soll eine Notbremse sein, kein Türsteher (D-50). Diese Haltung entscheidet im
  Zweifel auch alle Folgefragen zum Standardzustand.

</specifics>

<deferred>
## Deferred Ideas

- **Cursor und private-use URI schemes** (BL-04): zwei getrennte Entscheidungen, ob
  unzulässige `redirect_uris` verworfen statt die ganze Registrierung abgelehnt wird, und ob
  private-use Schemata zugelassen werden. Gehört zu Phase 5 SC 4.
- **Client ID Metadata Documents** (BL-05): der Nachfolger von DCR laut Spec. Zukunftssicherung,
  keine Voraussetzung.
- **WR-08, WR-10, WR-12** (AR-03-06 bis AR-03-08): bewusst zurückgestellt, in
  `03-SECURITY.md` als Restrisiken mit Datum verzeichnet. Vor der Store-Einreichung prüfen.
- **Admin-Sicht auf die Verbindungen aller Nutzer**: kam nicht auf, wäre aber die
  naheliegende Erweiterung. Admin-Belange sind AUTH-07 und gehören nicht hierher.

</deferred>

---

*Phase: 4-Per-User-Verwaltung und prepare_context*
*Context gathered: 2026-08-16*
