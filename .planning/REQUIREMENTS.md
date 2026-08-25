# Requirements: MCP Connector für Nextcloud, Milestone v1.3

**Defined:** 2026-08-25
**Core Value:** Die zugänglichste und sauberste MCP-Anbindung für Nextcloud: per Klick installierbar, spec-konformes OAuth statt App-Passwort-Gebastel, und der Assistent sieht niemals mehr als der angemeldete Nutzer.
**Milestone:** v1.3 "Pflege und 0.1.9": die beim v1.2-Abschluss bewusst zurückgestellten Konsistenz- und Härtungs-Schulden abräumen, solange sie frisch sind, und die Fassung als Release 0.1.9 in den Store bringen. Keine neuen Familien, keine neuen Tools.

## v1.3 Requirements

### Tool-Infrastruktur (TOOL)

- [x] **TOOL-17**: `truncated` auf Nachrichtenebene von `talk_browse(level="messages")` heißt `message_truncated` (DF-11-01, Muster von IN-01/`preview_truncated` in Mail): die Antwortebene behält `truncated`, der Tool-Docstring sagt die eine Bedeutung je Ebene, die Umbenennung steht als Formatänderung im Changelog von 0.1.9, und Tests decken beide Ebenen getrennt ab.
- [x] **TOOL-18**: Der Id-Codec ist die einzige Quelle für Id-Strings: der `_ID_KIND`-Workaround in `tools/mail.py` (Definition :70, Nutzung :490; die Fundstellenangabe "chatgpt.py" der ersten Fassung war falsch) ist durch `ids.encode_mail` ersetzt, und `ids.parse` lehnt eine `url:`-Id mit Whitespace im Rest ab statt sie durchzureichen; Negativtests für beide Wege.
- [ ] **TOOL-19**: Öffentliche Schnittstellen statt Privat-Durchgriffen: `tools/context.py` bzw. `tools/chatgpt.py` rufen keine `_`-präfixte Funktion eines fremden Tool-Moduls mehr auf (heute `talk_tools._room`), und das README-Beispiel für einen unbekannten Suchprovider nutzt eine echte, nie registrierte Provider-Id statt `spreed` (IN-Reste aus 11-REVIEW.md); ein Gate oder Test hält den Privat-Durchgriff fest.

### Sicherheit (SEC)

- [x] **SEC-02**: Die drei Security-Nachzieher aus 11-SECURITY.md sind geschlossen: (a) alle Einträge in `PROVIDER_KINDS` tragen den Verifikationskommentar mit Repository, Datei und Klasse (UF-1, heute fehlen `files` und `notes`), (b) das Quelltext-Gate aus T-11-29 existiert als Regressionstest statt als einmaliger Prüfschritt (UF-2), (c) das Vokabular-Gate prüft über `appinfo/info.xml` hinaus mindestens die drei READMEs und `CHANGELOG.md`, und `docs/store-submission.md` ist als interne Ausnahme begründet oder bereinigt (UF-3).

### Store und Release (EXAPP)

- [ ] **EXAPP-08**: Der CIMD-Weg ist nach den v1.1-Review-Fixes live nachgemessen (v1.1-Tech-Debt): ein E2E-Lauf gegen die laufende Topologie zeigt, dass ein CIMD-Client sich weiterhin ohne Registrierung verbindet, mit Proof-Zeile (Datum, Befehl, Ergebnis) in der Doku oder dem Messdokument der Phase.
- [ ] **EXAPP-09**: Release 0.1.9 ist im Store: Version an allen fünf Stellen (vier Code-Stellen plus README-Statuszeile in drei Sprachen), Changelog-Block mit `message_truncated` als Formatänderung, alle Gates grün (inkl. Vokabular-Gate in seiner neuen Reichweite), Branch-Push vor dem Tag, Signatur über das heruntergeladene Asset, Tag `v0.1.9` erst nach Owner-Freigabe, Runbook-Schritte 4 bis 8 mit Proof-Zeilen.

## Future Requirements

Vorgemerkt, nicht in v1.3:

- Mail-Entwürfe (`create draft`, nie Senden): Trigger Store-Feedback; Vorbild Gmail-MCP.
- Talk-Threads (capability-gated): Trigger, wenn ein Abnehmer Threads nachweislich braucht.
- Mail-Deep-Link-Auflösung (RFC-Message-Id zu databaseId): Trigger, sobald an einer echten Instanz gemessen.
- CLIENT-01..03 (MUCGPT live, F13, BaerGPT): unverändert deferred, extern getaktet (it@M-Antwort, Owner-Kontakte).
- v2.0 "openDesk/Behörden": OpenProject, XWiki, Matrix, OX, Gruppen-Policies, Audit-Log, ZenDiS-Kontakt.
- E5-Wortlaut bei CIMD-off (v1.1-Debt-Rest, nur falls beim CIMD-Rerun auffällig).

## Out of Scope

| Feature | Reasoning |
|---------|-----------|
| Neue Tools oder Familien | v1.3 ist reiner Pflege-Milestone; die Breite-2-Entscheidung fällt nach Store-Feedback und Conference |
| UF-4 (uv.lock-Versionszeile im Release-Commit) | Dokumentiert-akzeptiertes Verhalten von uv, identisch seit 0.1.5; keine Aktion |
| Anhebung von MAX_TOOL_BYTES oder BUDGET_BYTES | Gates bleiben auf der v1.2-Messung; eine Diät-Runde über title-Schlüssel ist benannt, aber nicht Teil von v1.3 |
| Destruktive Operationen | Unverändertes Sicherheitsversprechen |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| TOOL-17 | Phase 12 | Complete |
| TOOL-18 | Phase 12 | Complete |
| TOOL-19 | Phase 12 | Pending |
| SEC-02 | Phase 12 | Complete |
| EXAPP-08 | Phase 13 | Pending |
| EXAPP-09 | Phase 13 | Pending |

**Coverage:**
- v1.3 requirements: 6 total
- Mapped to phases: 6 von 6 (Phase 12: 4, Phase 13: 2); keine Waisen, keine Dopplungen
