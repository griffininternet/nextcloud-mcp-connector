# Requirements: MCP Connector für Nextcloud, Milestone v1.2

**Defined:** 2026-08-21
**Core Value:** Die zugänglichste und sauberste MCP-Anbindung für Nextcloud: per Klick installierbar, spec-konformes OAuth statt App-Passwort-Gebastel, und der Assistent sieht niemals mehr als der angemeldete Nutzer.
**Milestone:** v1.2 "Kuratierte Breite": Talk, Tables und Mail kommen dazu, ohne das Sicherheitsversprechen oder die Schlankheit aufzugeben. 5 neue Tools (21 gesamt) gegen 24 beim Platzhirsch für dieselben drei Familien.

## v1.2 Requirements

### Talk (TALK)

- [x] **TALK-01**: Nutzer kann seine Talk-Konversationen listen (Token, Name, Typ, Ungelesen-/Erwähnungs-Zähler, letzte Aktivität) über `talk_browse(level="conversations")`; archivierte Konversationen bleiben draußen, die Antwort ist gekappt (Max 50) und `noStatusUpdate=1` verhindert, dass das Listen den Online-Status setzt.
- [x] **TALK-02**: Nutzer kann den Verlauf einer Konversation lesen über `talk_browse(level="messages")`, nachweislich ohne Nebenwirkung: `setReadMarker=0`, `markNotificationsAsRead=0`, `noStatusUpdate=1`, `lookIntoFuture=0` sind per Test festgenagelt (Lesen setzt weder Lesemarker noch Online-Status noch quittiert es Benachrichtigungen); Platzhalter (`{actor}`, Mentions) sind aufgelöst, Systemnachrichten per Default draußen, Default 20 / Max 50 Nachrichten mit Byte-Kappe pro Nachricht und Paginierung über `lastKnownMessageId`.
- [x] **TALK-03**: Nutzer kann eine Nachricht in eine Konversation senden über `talk_send` (CREATE_ONLY): Adressierung ausschließlich per Token aus `talk_browse`, Vorprüfung `readOnly == 0` und Permission-Bit 128 mit hilfreicher Ablehnung, `@all`/`@here` werden abgelehnt, Längenkappe 32.000 Zeichen, kein `silent`-, kein Edit-, kein Delete-Pfad im Client.
- [x] **TALK-04**: Administrator kann `talk_send` instanzweit abschalten über einen neuen Admin-Settings-Schalter (Muster der bestehenden fünf OAuth-Werte, an per Default): mit abgeschaltetem Schalter antwortet das Tool mit einem Fehlersatz samt nächstem Schritt, und der Schalter ist Ende-zu-Ende getestet (Settings-Form, Overlay-Lesepfad, Wirkung am Tool).

### Tables (TABLES)

- [x] **TABLES-01**: Nutzer kann Tabellen, Spalten und Zeilen lesen über `tables_browse(level="tables"|"columns"|"rows")`: Spalten projiziert auf die interpretationsnötigen Felder, Zeilen über die dokumentierte v1-Route mit `limit`/`offset` (Default 25, Max 200), `rows/simple`-Kompaktformat als Default für Tabellen, `rowsCount` und benannte Truncation in der Antwort.
- [x] **TABLES-02**: Nutzer kann eine Zeile anlegen über `tables_create_row` (CREATE_ONLY) mit Spaltentiteln statt Spalten-Ids: Titel werden serverseitig auf Ids abgebildet, unbekannte oder mehrdeutige Titel und fehlende Pflichtspalten werden mit der Liste der gültigen Titel abgelehnt, und `onSharePermissions.create` wird vorab geprüft statt den Nutzer in ein 403 laufen zu lassen.

### Mail (MAIL)

- [x] **MAIL-01**: Nutzer kann Konten, Postfächer und Nachrichten-Envelopes lesen über `mail_browse(level="accounts"|"mailboxes"|"messages")`, strikt lesend: Envelopes mit `previewText` statt Body (Default 20, Max 50), Postfächer mit `specialRole` und Ungelesen-Zähler; kein Send-, Flag-, Move-, Delete- oder Draft-Pfad existiert im Client (AST-Grep-Gate erweitert).
- [x] **MAIL-02**: Nutzer kann eine einzelne Mail im Volltext lesen über das bestehende `fetch` mit neuem Präfix `mail:<databaseId>` (offizielle OCS-Route): HTML wird zu Text, die bestehende Byte-Kappe und Truncation-Markierung greifen, und Nextclouds Vertrauens-Signale (`isSenderTrusted`, `phishingDetails`, DKIM) werden als Datenfelder durchgereicht.
- [x] **MAIL-03**: Die Mail-Filtergrammatik (`is:unread`, `from:`, `subject:`, `start:`, `tags:`) ist als `filter`-Parameter von `mail_browse(level="messages")` dokumentiert und getestet.
- [x] **MAIL-04**: Der Mail-Zugang ist im AppAPI-Modus live bewiesen, nicht nur mit App-Passwort: ein Integrationstest gegen eine echte Instanz belegt die internen Listen-Routen (accounts, mailboxes, messages) und die OCS-Volltext-Route unter Impersonation, und das SCOPE_IGNORE-Risiko der internen Routen ist im Code und in der Doku benannt.

### Server und Erkennung (SRV)

- [ ] **SRV-06**: Alle drei neuen Familien degradieren sauber, wenn die App fehlt: Talk und Tables über den bestehenden Capabilities-Weg (`spreed`, `tables`), Mail über `GET /ocs/v2.php/core/navigation/apps` (Mail hat keinen Capabilities-Eintrag), gecacht wie das bestehende Modul; ein Tool gegen eine fehlende App antwortet mit einem Fehlersatz samt konkretem nächsten Schritt, nie mit Stacktrace oder Loginseite.

### prepare_context (CTX)

- [ ] **CTX-01**: `prepare_context` enthält einen Talk-Digest aus einem einzigen Request (die Konversationsliste trägt alles Nötige): maximal 3 Konversationen mit Erwähnung oder Ungelesenem, `lastMessage`-Vorschau hart gekappt (~200 Zeichen), eigenes Zeit-Budget und eigener `degraded`-Eintrag; das bestehende Timeout-/Degradations-Verhalten der anderen Quellen bleibt gemessen unverändert.
- [ ] **CTX-02**: `prepare_context` enthält Mail-Ungelesen-Zähler (nur Zahlen pro Konto/Inbox, keine Betreffs, kein Inhalt aus fremder Hand im Standardbündel), mit eigenem Zeit-Budget und `degraded`-Eintrag; die 1+N-Request-Kosten sind gemessen und dokumentiert.

### Tool-Infrastruktur (TOOL)

- [ ] **TOOL-15**: Das Budget-Gate ist auf die neue Messung angehoben (Regel Messung plus 15 Prozent, aufgerundet auf die nächsten 500, erwartet 17.500 bis 18.000 Bytes) mit neuer Messzeile im Skript; alle fünf neuen Tools sind schema-diätet, die Annotationen sind ehrlich (drei READ_ONLY, zwei CREATE_ONLY), und README-Tool-Tabelle plus Contract-Tests (Tool-Zahl 21) sind nachgezogen.
- [ ] **TOOL-16**: Unified-Search-Treffer aus Talk und Tables sind auflösbar statt `kind=url`: `provider_map`-Einträge für `talk-message` (über die mitgelieferten Attribute `conversation`/`messageId`) und `tables-search-tables` (Id steckt im URL-Fragment, nicht im Pfad); Mail-Treffer bleiben ehrlich `kind=url`, weil die Deep-Link-Auflösung ungemessen ist.

### Sicherheit (SEC)

- [x] **SEC-01**: Die Kombination Mail-Lesen plus Talk-Senden ("Lethal Trifecta": private Daten + fremder Inhalt + Ausgangskanal) ist ausdrücklich adressiert: ein Doku-Abschnitt benennt Mail- und Talk-Inhalte als fremde Daten und die Exfiltrationskette beim Namen, verweist auf den TALK-04-Schalter als Gegenmaßnahme, und die Store-Beschreibung (EN/DE/FR) sagt den Mail-ist-strikt-lesend-Satz.

### Store und Release (EXAPP)

- [ ] **EXAPP-07**: Release 0.1.6 ist im Store (0.1.4 am 21.08.2026 und 0.1.5 am 22.08.2026 vorgezogen, Owner-Entscheid): Version an allen vier Stellen, Changelog-Block, READMEs EN/DE/FR und Store-Texte nachgezogen (Vokabular-Gate), alle Gates grün, Tag erst nach Owner-Freigabe, Runbook docs/store-submission.md Schritte 4 bis 8 mit Proof-Zeilen.

## Future Requirements

Vorgemerkt, nicht in v1.2:

- CLIENT-01 (MUCGPT live), CLIENT-02 (F13), CLIENT-03 (BaerGPT): unverändert deferred, extern getaktet (it@M-Antwort, Owner-Kontakte).
- Mail-Entwürfe (`create draft`, nie Senden): Trigger Store-Feedback; Vorbild Gmail-MCP.
- Talk-Threads (capability-gated): Trigger, wenn ein Abnehmer Threads nachweislich braucht.
- Mail-Deep-Link-Auflösung (RFC-Message-Id zu databaseId): Trigger, sobald an einer echten Instanz gemessen.
- v2.0 "openDesk/Behörden": OpenProject, XWiki, Matrix, OX, Gruppen-Policies, Audit-Log, ZenDiS-Kontakt.
- Tech-Debt v1.1-Audit: acceptance_all_tools-Zählung (wird von TOOL-15 miterledigt, sonst hier), CIMD-E2E-Live-Rerun, E5-Wortlaut bei CIMD-off.
- Prototype-Fund-Antrag (Frist 1.10. bis 30.11.2026; Querschnitt, kein Code-Requirement).

## Out of Scope

| Feature | Reasoning |
|---------|-----------|
| Mail senden (auch als "nur mit Bestätigung") | Irreversibel, nach außen wirksam, schließt die Trifecta vollständig; Google zieht beim eigenen Gmail-MCP dieselbe Grenze. AST-Grep-Gate erzwingt das Nicht-Vorhandensein |
| Mail-Flags, Tags, Verschieben, Löschen, Als-gelesen-markieren | Zustandsänderungen in fremden Systemen (IMAP), teils destruktiv; bricht die Aussage der Familie |
| Mail-Anhänge herunterladen | Binärdaten sprengen jedes Token-Budget, Malware-Fläche; Metadaten plus Instanz-Link genügen |
| Talk-Nachricht löschen/bearbeiten, Konversation anlegen, Reaktionen, Teilnehmerlisten, Umfragen, Threads | Destruktiv, Nebenwirkungs-reich oder Budget-Bytes ohne belegten Nutzen; Threads erst auf Abnehmer-Nachweis |
| `lookIntoFuture=1` (Long Polling) | Blockiert bis 60 s pro Aufruf, läuft in jedes Client-Timeout; Aktualität kommt vom nächsten Aufruf |
| Eigene Suchtools pro Familie | Redundant: `unified_search`/`prepare_context` decken Talk, Mail und Tabellen-Namen berechtigungstreu ab; drei Tool-Slots gespart |
| Tabellen-Schema ändern, Zeile updaten/löschen, Import, Shares | Destruktiv im Wortsinn (gelöschte Spalte nimmt alle Zeilendaten mit); Update ist Überschreiben ohne Historie |
| Credential-abhängige `tools/list` | Bricht Caching, Budget-Gate und Clients, die Tool-Listen persistieren; etablierte Antwort ist der Fehlersatz zur Laufzeit (SRV-04) |
| Semantische Suche / Vektorindex für Mail und Talk | Ein Mail-Vektorindex ist eine Kopie der sensibelsten Daten neben der Nextcloud; bleibt bei der v1.0-Entscheidung |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| TALK-01 | Phase 9 | Complete |
| TALK-02 | Phase 9 | Complete |
| TALK-03 | Phase 9 | Complete |
| TALK-04 | Phase 9 | Complete |
| TABLES-01 | Phase 8 | Complete |
| TABLES-02 | Phase 8 | Complete |
| MAIL-01 | Phase 10 | Complete |
| MAIL-02 | Phase 10 | Complete |
| MAIL-03 | Phase 10 | Complete |
| MAIL-04 | Phase 8 | Complete |
| SRV-06 | Phase 10 | Pending |
| CTX-01 | Phase 11 | Pending |
| CTX-02 | Phase 11 | Pending |
| TOOL-15 | Phase 11 | Pending |
| TOOL-16 | Phase 11 | Pending |
| SEC-01 | Phase 10 | Complete |
| EXAPP-07 | Phase 11 | Pending |

**Coverage:**
- v1.2 requirements: 17 total
- Mapped to phases: 17 (Phase 8: 3, Phase 9: 4, Phase 10: 5, Phase 11: 5)
- Unmapped: 0

---
*Requirements defined: 2026-08-21*
*Last updated: 2026-08-21 nach Roadmap-Erstellung (Phasen 8-11 zugeordnet)*
</content>
