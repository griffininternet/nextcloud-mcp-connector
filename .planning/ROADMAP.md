# Roadmap: MCP Connector für Nextcloud

## Milestones

- **v1.0 MVP im Store**: Phasen 1-5 (shipped 2026-08-20, Release 0.1.2 live im Nextcloud App Store)
- **v1.1 Verwaltungs-Clients und Härtungs-Reste**: Phasen 6-7 (bewusst klein, Deadline Nextcloud Conference September 2026)

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

### v1.1 Verwaltungs-Clients und Härtungs-Reste (Phasen 6-7)

- [ ] **Phase 6: Härtung, Eigennachweise und Conference-Reife** - Alles, was ohne fremde Instanz beweisbar ist: CIMD mit SSRF-Grenze, Cursor und Loopback-Port gemessen, Ein-Klick-Story wörtlich wahr, Conference-Material steht
- [ ] **Phase 7: Verwaltungs-Clients live verprobt** - MUCGPT, F13 und BaerGPT verbinden sich gegen den Connector, jeder Nachweis mit Messdatei und Berechtigungs-Gegenprobe (extern getaktet)

## Phase Details

### Phase 6: Härtung, Eigennachweise und Conference-Reife
**Goal**: Jeder offene v1.1-Punkt, der ohne fremden Zugang beweisbar ist, ist erledigt: ein CIMD-Client kommt unter denselben Kontrollen wie ein DCR-Client herein, der Abruf des Metadatendokuments hat eine belegte SSRF-Grenze, die lokalen Clients (Cursor, Loopback-Port) sind gemessen statt vermutet, die Ein-Klick-Story sagt wörtlich das, was auf 34.0.3 wahr ist, und das Conference-Material ist vorführbar.
**Depends on**: Phase 5 (v1.0, abgeschlossen)
**Requirements**: AUTH-08, AUTH-09, CLIENT-04, CLIENT-05, EXAPP-06, CONF-01, CONF-02
**Success Criteria** (was wahr sein muss):
  1. Ein Client, der sich per Client ID Metadata Document ausweist (Kandidat: Claude Code), verbindet sich und ruft ein Werkzeug auf; dabei greifen die DCR-Kontrollen unverändert: die Redirect-URI-Prüfung, der Allowlist-Modus aus AUTH-07 und ein abgeschaltetes DCR, das über CIMD nachweislich nicht umgehbar ist.
  2. Der CIMD-Dokumentabruf ist fail-closed und belegt: nur https, keine privaten oder link-lokalen Ziele, Größen- und Zeitlimit greifen, das Caching ist kontrolliert, und für jede dieser Grenzen existiert ein roter Negativtest, der ohne die Grenze durchgeht.
  3. Die lokalen Clients sind gemessen statt vermutet: Cursor verbindet sich live nach der Teilregistrierung (DCR mit dem Drei-URI-Body wird 201, Autorisierung und Tool-Aufruf laufen durch), und die Loopback-Portfrage ist mit einem Client mit wechselndem 127.0.0.1-Port beantwortet, samt dokumentiertem Entscheid (RFC-8252-7.3-Ausnahme umgesetzt oder als benanntes Risiko akzeptiert).
  4. Auf einer auf 34.0.3 aktualisierten Instanz ist nachgewiesen, ob die Store-UI den Install- und Remove-Knopf für ExApps zeigt; docs/exapp-install.md und der Store-Text sagen danach genau das, was gemessen wurde, ohne Ein-Klick-Versprechen ohne Deckung.
  5. Ein Dritter kann die Demo nachfahren: eine reproduzierbare Strecke aus Verbindung, Tool-Aufrufen, Per-User-Verwaltung und Widerruf gegen eine laufende Instanz, mit Drehbuch, plus ein Lightning-Talk-Entwurf aus Folien und Sprechzettel (Einreichung bleibt Owner-Entscheid).
**Plans**: TBD

### Phase 7: Verwaltungs-Clients live verprobt
**Goal**: Die drei deutschen Verwaltungs-Assistenten sind vom Dossier-Zitat zum gelaufenen Fall geworden: MUCGPT, F13 und BaerGPT verbinden sich gegen den Connector, jeder Nachweis liegt als Messdatei neben den bestehenden Client-Belegen, und docs/client-setup.md enthält keine unverprobte Sektion mehr.
**Depends on**: Phase 6 (fachlich unabhängig; extern getaktet, startet je Client sobald Zugang besteht)
**Requirements**: CLIENT-01, CLIENT-02, CLIENT-03
**Success Criteria** (was wahr sein muss):
  1. MUCGPT verbindet sich live nach dem dokumentierten Protokoll (drei Checks in Ausfallreihenfolge: Header kommt an, Tool-Liste kommt zurück, Tool-Aufruf antwortet mit Inhalt des konfigurierten Kontos); die Messdatei ersetzt den Lücken-Absatz in docs/client-setup.md und BL-12 ist geschlossen.
  2. Die Identitätsfrage aus BL-12 ist beantwortet und festgehalten: Service-Konto genügt oder Per-User-Treue wird gefordert; im zweiten Fall steht Token Exchange als benannte v1.2-Kandidatin in den Requirements statt als Vermutung.
  3. F13 und BaerGPT verbinden sich live gegen den Connector; für jeden liegt eine Messdatei neben den anderen Client-Nachweisen und docs/client-setup.md hat eine belegte, datierte Sektion statt einer aus Quellcode abgeleiteten.
  4. Jeder der drei Nachweise trägt die Berechtigungs-Gegenprobe: ein Inhalt, den das konfigurierte Nextcloud-Konto nicht sehen darf, bleibt über den Assistenten unsichtbar.
**Plans**: TBD

**Hinweis zur Taktung:** CLIENT-01 hängt an der Antwort von it@M (Mail gesendet 2026-08-20), CLIENT-02 und CLIENT-03 an Owner-Kontakten. Phase 7 kann deshalb nach Phase 6 offen stehenbleiben, ohne einen Liefergegenstand von v1.1 zu blockieren; kein Punkt aus Phase 6 wartet auf einen dieser Zugänge.

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Server-Kern | v1.0 | 14/14 | Complete | 2026-08-14 |
| 2. ExApp-Shell | v1.0 | 7/7 | Complete | 2026-08-15 |
| 3. OAuth 2.1 | v1.0 | 9/9 | Complete | 2026-08-16 |
| 4. Per-User-Verwaltung und prepare_context | v1.0 | 4/4 | Complete | 2026-08-17 |
| 5. Hardening und Store-Einreichung | v1.0 | 16/16 | Complete | 2026-08-20 |
| 6. Härtung, Eigennachweise und Conference-Reife | v1.1 | 0/TBD | Not started | - |
| 7. Verwaltungs-Clients live verprobt | v1.1 | 0/TBD | Not started (extern getaktet) | - |

## Next

`/gsd:plan-phase 6`

---
*Roadmap created: 2026-08-14 (granularity: coarse, mode: mvp); v1.0 archived: 2026-08-20; v1.1 Phasen 6-7 ergänzt: 2026-08-20*
