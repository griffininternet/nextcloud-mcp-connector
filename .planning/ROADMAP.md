# Roadmap: MCP Connector für Nextcloud

## Milestones

- **v1.0 MVP im Store**: Phasen 1-5 (shipped 2026-08-20, Release 0.1.2 live im Nextcloud App Store)
- **v1.1 Verwaltungs-Clients und Härtungs-Reste**: Phase 6 (shipped 2026-08-20; Phase 7 deferred, extern getaktet)
- **v1.2 Kuratierte Breite**: Phasen 8-11 (shipped 2026-08-25, Release 0.1.8 live im Store; Talk, Tables und Mail dazu, ohne das Sicherheitsversprechen oder die Schlankheit aufzugeben)
- **v1.3 Pflege und 0.1.9**: Phasen 12-13 (aktiv; die beim v1.2-Abschluss zurückgestellten Konsistenz- und Härtungs-Schulden abräumen und als Release 0.1.9 in den Store bringen, keine neuen Familien)

## Phases

<details>
<summary>v1.0 MVP im Store (Phasen 1-5), SHIPPED 2026-08-20</summary>

- [x] Phase 1: Server-Kern (14/14 Pläne), completed 2026-08-14
- [x] Phase 2: ExApp-Shell (7/7 Pläne), completed 2026-08-15
- [x] Phase 3: OAuth 2.1 (9/9 Pläne), completed 2026-08-16
- [x] Phase 4: Per-User-Verwaltung und prepare_context (4/4 Pläne), completed 2026-08-17
- [x] Phase 5: Hardening und Store-Einreichung (16/16 Pläne inkl. Gap-Closure), completed 2026-08-20

Volle Phasendetails: [milestones/v1.0-ROADMAP.md](milestones/v1.0-ROADMAP.md)
Audit: [milestones/v1.0-MILESTONE-AUDIT.md](milestones/v1.0-MILESTONE-AUDIT.md) (passed, 27/27 Requirements)

</details>

<details>
<summary>v1.1 Verwaltungs-Clients und Härtungs-Reste (Phase 6), SHIPPED 2026-08-20</summary>

- [x] Phase 6: Härtung, Eigennachweise und Conference-Reife (11/11 Pläne inkl. Gap-Closure), completed 2026-08-20
- [ ] Phase 7: Verwaltungs-Clients live verprobt, DEFERRED per Owner-Entscheid 2026-08-20 (extern getaktet: it@M-Antwort, Owner-Kontakte; CLIENT-01..03 als Future Requirements vorgemerkt, Protokoll in docs/client-setup.md bleibt einlösbar)

Volle Phasendetails: [milestones/v1.1-ROADMAP.md](milestones/v1.1-ROADMAP.md)
Audit: [milestones/v1.1-MILESTONE-AUDIT.md](milestones/v1.1-MILESTONE-AUDIT.md) (passed, 7/7 Requirements)

</details>

<details>
<summary>v1.2 Kuratierte Breite (Phasen 8-11), SHIPPED 2026-08-25</summary>

- [x] Phase 8: Erreichbarkeits-Spike und Tables (5/5 Pläne), completed 2026-08-21
- [x] Phase 9: Talk (5/5 Pläne), completed 2026-08-21
- [x] Phase 10: Mail strikt lesend und die Trifecta-Grenze (8/8 Pläne), completed 2026-08-24
- [x] Phase 11: Bündelung, Budget und Release 0.1.8 (10/10 Pläne; der Phasentitel "0.1.6" war überholt), completed 2026-08-25

Volle Phasendetails: [milestones/v1.2-ROADMAP.md](milestones/v1.2-ROADMAP.md)
Audit: [milestones/v1.2-MILESTONE-AUDIT.md](milestones/v1.2-MILESTONE-AUDIT.md) (passed, 17/17 Requirements)

</details>

### v1.3 Pflege und 0.1.9 (Phasen 12-13)

- [ ] **Phase 12: Konsistenz und Härtungs-Nachzieher** - Die vier Schulden aus 11-REVIEW und 11-SECURITY abräumen: eine Bedeutung je Antwortschlüssel, der Id-Codec als einzige Quelle, keine Privat-Durchgriffe zwischen Tool-Modulen, und die drei Security-Nachzieher als Test statt als Prüfschritt
- [ ] **Phase 13: CIMD-Nachmessung und Release 0.1.9** - Den CIMD-Weg nach den v1.1-Review-Fixes live nachmessen und die Fassung mit Proof-Zeilen als 0.1.9 in den Store bringen, Tag nur nach Owner-Freigabe

## Phase Details

### Phase 12: Konsistenz und Härtungs-Nachzieher

**Goal**: Die beim v1.2-Abschluss bewusst zurückgestellten Konsistenz- und Härtungs-Schulden sind geschlossen, solange sie frisch sind: ein Antwortschlüssel bedeutet je Ebene genau eine Sache, Id-Strings entstehen ausschließlich im Codec, kein Tool-Modul greift in die Privatteile eines anderen, und die drei Security-Nachzieher aus 11-SECURITY.md sind Tests statt einmaliger Prüfschritte. Keine neuen Tools, keine neuen Familien, keine Anhebung eines Gates.
**Depends on**: Phase 11 (v1.2 abgeschlossen, Release 0.1.8 live im Store)
**Requirements**: TOOL-17, TOOL-18, TOOL-19, SEC-02
**Success Criteria** (was wahr sein muss):

  1. Die Nachrichtenebene von `talk_browse(level="messages")` heißt `message_truncated`, die Antwortebene behält `truncated`, der Tool-Docstring nennt für jede Ebene genau eine Bedeutung, und Tests decken beide Ebenen getrennt ab (Muster von IN-01/`preview_truncated` in Mail). Die Umbenennung ist als Formatänderung im Changelog-Block für 0.1.9 vermerkt, nicht stillschweigend gemacht.
  2. Kein Produktionsmodul baut einen Id-String außerhalb des Codecs: `tools/mail.py` ruft `ids.encode_mail` statt des `_ID_KIND`-Workarounds (Fundstelle mail.py:70/:490, nicht chatgpt.py wie zuerst notiert), und `ids.parse` lehnt eine `url:`-Id mit Whitespace im Rest ab statt sie durchzureichen; für beide Wege existiert je ein Negativtest.
  3. Kein Tool-Modul ruft eine `_`-präfixte Funktion eines fremden Tool-Moduls: der heutige Aufruf von `talk_tools._room` läuft über eine öffentliche Schnittstelle, und ein Gate oder Test wird rot, wenn ein Privat-Durchgriff zurückkehrt. Das README-Beispiel für einen unbekannten Suchprovider nennt eine echte, nie registrierte Provider-Id statt `spreed`.
  4. Die drei Nachzieher aus 11-SECURITY.md sind geschlossen: jeder Eintrag in `PROVIDER_KINDS` trägt den Verifikationskommentar mit Repository, Datei und Klasse (auch `files` und `notes`), das Quelltext-Gate aus T-11-29 läuft als Regressionstest in der Suite, und das Vokabular-Gate prüft über `appinfo/info.xml` hinaus mindestens die drei READMEs und `CHANGELOG.md`, wobei `docs/store-submission.md` entweder bereinigt oder als interne Ausnahme im Gate begründet ist.
  5. Die Werkzeugoberfläche ist unverändert groß und alle Gates bleiben ohne Anhebung grün: `BUDGET_BYTES` steht weiter auf 18000, `MAX_TOOL_BYTES` weiter auf 1400, die Zahl der Werkzeuge bleibt 21, und die einzige nutzersichtbare Änderung ist der umbenannte Nachrichten-Schlüssel.

**Plans**: 4 plans (2 Wellen: 12-01, 12-02 und 12-03 parallel, danach 12-04)

Plans:
**Wave 1**

- [x] 12-01-PLAN.md — TOOL-17: `message_truncated` auf der Nachrichtenebene von `talk_browse`, Verbraucher in `fetch` zieht mit, Tool-Docstring mit einer Bedeutung je Ebene
- [ ] 12-02-PLAN.md — TOOL-18: `ids.encode_mail` statt `_ID_KIND`, und `ids.parse` liest im `url`-Zweig nur noch, was `ids.encode_url` bauen kann
- [ ] 12-03-PLAN.md — SEC-02: Verifikationskommentare für `files` und `notes`, T-11-29 als Regressionstest, Vokabular-Gate über READMEs und Changelog

**Wave 2** *(blocked on Wave 1 completion)*

- [ ] 12-04-PLAN.md — TOOL-19: `talk.one_room` statt `talk_tools._room`, AST-Gate gegen Privat-Durchgriffe, README-Beispiel mit `talk-conversations`

### Phase 13: CIMD-Nachmessung und Release 0.1.9

**Goal**: Der CIMD-Weg ist nach den v1.1-Review-Fixes nicht mehr behauptet, sondern gegen die laufende Topologie nachgemessen, und die Fassung aus Phase 12 liegt als Release 0.1.9 im Nextcloud App Store, mit Proof-Zeilen für jeden Runbook-Schritt und einem Tag, der erst nach ausdrücklicher Owner-Freigabe entsteht.
**Depends on**: Phase 12
**Requirements**: EXAPP-08, EXAPP-09
**Success Criteria** (was wahr sein muss):

  1. Ein E2E-Lauf gegen die laufende Topologie zeigt, dass ein CIMD-Client sich weiterhin ohne Registrierung verbindet (client_id = https-URL seines Dokuments), und die Proof-Zeile mit Datum, Befehl und Ergebnis steht in der Doku oder im Messdokument der Phase, nicht in einer Zusammenfassung.
  2. Die Version 0.1.9 steht als derselbe String an allen fünf Stellen (vier Code-Stellen plus README-Statuszeile in EN, DE und FR), und der Changelog-Block 0.1.9 nennt jede nutzerrelevante Änderung der Phase 12, `message_truncated` ausdrücklich als Formatänderung.
  3. Alle Gates laufen lokal grün, das Vokabular-Gate in seiner neuen Reichweite aus Phase 12 eingeschlossen, und der Branch ist gepusht, bevor irgendein Tag existiert (Runbook Schritt 4); der Tag `v0.1.9` entsteht erst nach ausdrücklicher Owner-Freigabe.
  4. Release 0.1.9 ist im Store gelistet: signiert wurde das heruntergeladene Release-Asset und nicht das lokal gebaute (Runbook Schritt 6), und die Runbook-Schritte 4 bis 8 tragen je eine Proof-Zeile mit Datum, Befehl und Ergebnis in `docs/store-submission.md`.

**Plans**: TBD

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Server-Kern | v1.0 | 14/14 | Complete | 2026-08-14 |
| 2. ExApp-Shell | v1.0 | 7/7 | Complete | 2026-08-15 |
| 3. OAuth 2.1 | v1.0 | 9/9 | Complete | 2026-08-16 |
| 4. Per-User-Verwaltung und prepare_context | v1.0 | 4/4 | Complete | 2026-08-17 |
| 5. Hardening und Store-Einreichung | v1.0 | 16/16 | Complete | 2026-08-20 |
| 6. Härtung, Eigennachweise und Conference-Reife | v1.1 | 11/11 | Complete | 2026-08-20 |
| 7. Verwaltungs-Clients live verprobt | v1.1 | 0/0 | Deferred (extern getaktet) | - |
| 8. Erreichbarkeits-Spike und Tables | v1.2 | 5/5 | Complete | 2026-08-21 |
| 9. Talk | v1.2 | 5/5 | Complete | 2026-08-21 |
| 10. Mail strikt lesend und die Trifecta-Grenze | v1.2 | 8/8 | Complete | 2026-08-24 |
| 11. Bündelung, Budget und Release 0.1.8 | v1.2 | 10/10 | Complete | 2026-08-25 |
| 12. Konsistenz und Härtungs-Nachzieher | v1.3 | 1/4 | In Progress | - |
| 13. CIMD-Nachmessung und Release 0.1.9 | v1.3 | 0/? | Not started | - |

## Next

`/gsd:execute-phase 12` — Phase 12 "Konsistenz und Härtungs-Nachzieher" ausführen (4 Pläne in 2 Wellen; Gates bleiben auf der v1.2-Messung: BUDGET_BYTES 18000, MAX_TOOL_BYTES 1400)

---
*Roadmap created: 2026-08-14 (granularity: coarse, mode: mvp); v1.0 abgeschlossen: 2026-08-20; v1.1 abgeschlossen: 2026-08-20 (Phase 7 deferred); v1.2 abgeschlossen: 2026-08-25 (Release 0.1.8 live); v1.3 aufgesetzt: 2026-08-25 (2 Phasen, 6 Requirements)*
