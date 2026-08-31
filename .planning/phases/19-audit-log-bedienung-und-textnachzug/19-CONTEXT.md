# Phase 19: Audit-Log Bedienung und Textnachzug - Context

**Gathered:** 2026-08-31
**Status:** Ready for planning
**Source:** Synthese aus Owner-Vorgaben (NEXT.md 31.08.), Milestone-Entscheiden D-v1.5-01..04 (REQUIREMENTS.md, dort abschließend entschieden, werden nicht wieder aufgemacht) und den Phase-18-Artefakten. Kein discuss-phase-Lauf: die Entscheide standen bereits fest, Modus yolo.

<domain>
## Phase Boundary

Ein Administrator schaltet das Audit-Log ein und liest es über `occ`, und jede bestehende Aussage über Speicherung, Purge und den Enterprise-Stand sagt danach die Wahrheit. Requirements: AUDIT-04 (occ-Lesekommando ohne neue Manifest-Route), AUDIT-05 (ab Werk aus, Admin-Beschriftung mit Leistungs-, Grenz- und Mitbestimmungshinweis), AUDIT-06 (Textnachzug docs/privacy.md, docs/uninstall.md, Enterprise-Absatz in drei Sprachen, Wörter-Gate).

NICHT in dieser Phase: kein Tag, kein Store-Upload, kein Release. Alle Textänderungen warten im `[Unreleased]`-Block (D-v1.5-03, Auslieferung ist EXAPP-12). Die Werkzeugoberfläche bleibt bei 21 Werkzeugen und 15712 Bytes, kein Gate-Grenzwert wird angehoben.
</domain>

<decisions>
## Implementation Decisions

### occ-Lesekommando (AUDIT-04)
- Lesen und Exportieren über ein `occ`-Kommando; KEINE neue Route im Manifest. Muster ist das in Phase 18 gebaute `occ mcp_connector:audit:verify`: AppAPI-PublicFunctions auf einen Pfad ohne `<url>`-Eintrag, Doppelprüfung x-origin-ip (404) dann require_appapi (401), immer Status 200 mit Urteil im Rumpf (AppAPI verwirft den Rumpf bei jedem anderen Status, T-18-20).
- Ausgabe klammert Nutzer- und Client-Namen vor der Ausgabe (Muster T-18-08); nie Parameterwerte, nie IPs, nie Fehlermeldungstexte.

### Admin-Schalter und Beschriftung (AUDIT-05)
- Ab Werk aus, einschaltbar in den Admin-Einstellungen (existiert seit Phase 18 als siebter Wert `audit_log`). Diese Phase zieht die BESCHRIFTUNG nach: was das Log leistet, was es nicht leistet (Grenzbeschreibung ist Pflichtbestandteil, D-v1.5-02), und dass ein nutzerbezogenes Protokoll mitbestimmungsrelevant sein kann (D-v1.5-04).
- Keine Stufe, die Parameterwerte oder Ergebnisinhalte protokolliert; `keys` ist der einzige einschaltbare Inhaltsumfang, `full` existiert nirgends in der Oberfläche.
- Befund aus dem Phase-18-Review (Info-Finding, hier einzulösen): die bisherige Formularbeschreibung verschweigt, dass auch Parameternamen, Ablehnungsgrund und Dauer gespeichert werden. Die neue Beschriftung nennt das ehrlich.

### Textnachzug (AUDIT-06)
- `docs/privacy.md` und `docs/uninstall.md` sagen im eigenen Text, dass das Audit-Log Purge und Deinstallation übersteht und die Aufbewahrungsfrist der einzige automatische Löscher ist (plus Nutzerlöschung in Nextcloud). Das v1.0-Erfolgskriterium "eine Deinstallation entfernt alle Daten" wird ausdrücklich umgeschrieben statt stillschweigend falsch (D-v1.5-01). Restpunkt R-18-04 aus 18-SECURITY.md: uninstall.md nennt das Audit-Log heute namentlich NICHT, die D-18-Grenze (`--rm-data` entfernt das Volume samt Log) steht bisher nur im Phasenartefakt und gehört in den Nutzertext.
- Enterprise-Absatz nennt das Audit-Log in allen drei Sprachen (EN/DE/FR) nicht länger als geplant; der Satz "heute in keiner Form vorhanden" ist mit Phase 18 falsch geworden.
- Wörter-Gate: ein Test hält die Wörter revisionssicher, AI-Act-konform, DSGVO-konform und SIEM-zertifiziert aus den Texten heraus (D-v1.5-02, Verbotsliste).
- Dreisprachigkeit ist Projektregel: README- und Store-Text-Änderungen immer EN/DE/FR nachziehen; echte Umlaute und Accents, keine Em-Dashes; in info.xml-Descriptions kein Backtick und keine Tabelle, die Version in info.xml wird NICHT angefasst.
- Alles wartet im `[Unreleased]`-Block des Changelogs; kein Tag (Milestone-Tags heißen milestone-v*, NIE v*, weil release.yml auf v* triggert).

### Claude's Discretion
- Ob das Lesekommando ein eigenes `mcp_connector:audit:read`/`:export` wird oder das bestehende verify-Kommando eine Leseausgabe bekommt; Exportformat (JSONL/CSV) und Filteroptionen.
- Ob die drei Env-Variablen (`NC_MCP_AUDIT_LOG`, `NC_MCP_AUDIT_RETENTION_DAYS`, `NC_MCP_AUDIT_MAX_BYTES`) jetzt einen `<environment-variables>`-Eintrag in appinfo/info.xml bekommen (deferred item aus 18-07; reine Bequemlichkeit für Hand-Installationen, Admin-Formular bleibt der Hauptweg BL-06).
- Ob die Restrisiken R-18-06/07/08 aus 18-SECURITY.md hier miterledigt werden (drei divergente Namensreiniger/Bidi, note() vs CancelledError, isdigit ohne isascii in audit_verify._payload); sie sind klein, code-nah und berühren die Bedienoberfläche dieser Phase.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase-18-Ergebnisstand (Satzschema, Speicher, Muster)
- `.planning/phases/18-audit-log-kern/18-CONTEXT.md` — die 15 Entscheide D-01..D-15 des Kerns
- `.planning/phases/18-audit-log-kern/18-SECURITY.md` — Threat-Register, akzeptierte Risiken, Restrisiken R-18-04/06/07/08
- `.planning/phases/18-audit-log-kern/18-REVIEW.md` — Review-Befunde, Info-Findings (Admin-Text, tote Pfade, Sanitizer)
- `.planning/phases/18-audit-log-kern/deferred-items.md` — Env-Variablen ohne info.xml-Eintrag, flakiger 429-Test
- `src/mcp_connector/exapp/audit_verify.py` — Muster für occ-Kommando über PublicFunctions ohne Manifest-Route
- `src/mcp_connector/exapp/occ.py` — occ-Registrierung
- `src/mcp_connector/exapp/admin_settings.py` — Admin-Formular, Feld `audit_log`
- `src/mcp_connector/audit/store.py` — Ablage, verify_chains, sweep, StoreOverview (used_bytes, sweepable_entries, over_bound_unevictable)

### Texte
- `docs/privacy.md`, `docs/uninstall.md` — umzuschreibende Aussagen
- `appinfo/info.xml` — Enterprise-Absatz in den Descriptions EN/DE/FR (Version nicht anfassen)
- `CHANGELOG.md` — `[Unreleased]`-Block (durch Phase 16 geleert)
- `src/mcp_connector/exapp/ui/strings.py` — Beschriftungstexte
</canonical_refs>

<specifics>
## Specific Ideas

- Owner-Formulierung (NEXT.md): "occ-Lesekommando, Admin-Beschriftung mit Mitbestimmungshinweis, docs/privacy.md + docs/uninstall.md umschreiben, Enterprise-Absatz und Wörter-Gate; alles wartet im [Unreleased]-Block, KEIN Tag, KEIN Store-Upload".
- Regel aus D-v1.5-01, abgeleitet in REQUIREMENTS.md: Verbindung trennen und Pausieren lassen die Einträge stehen; abgelaufene Frist und Nutzerlöschung löschen sie; Purge und Deinstallation löschen alles AUSSER dem Audit-Log; `--rm-data` ist die benannte Ausnahme.
- Gate-Muster für die Verbotswörter existiert im Repo bereits als Wortlisten-Test (Vokabular-Gates); gleiches Muster verwenden.
</specifics>

<deferred>
## Deferred Ideas

- EXAPP-12: Release 0.1.12 mit dem Audit-Log; ausdrücklich nicht Teil dieses Meilensteins.
- Flakiger Test `test_a_flood_of_accepted_authorization_requests_ends_in_429` (zeitabhängig, ohne Bezug zur Phase).
</deferred>

---

*Phase: 19-audit-log-bedienung-und-textnachzug*
*Context gathered: 2026-08-31 via Synthese aus Owner-Vorgaben und Milestone-Entscheiden*
