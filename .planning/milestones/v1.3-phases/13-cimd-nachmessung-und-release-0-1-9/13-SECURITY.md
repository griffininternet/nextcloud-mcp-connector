---
phase: 13
slug: 13-cimd-nachmessung-und-release-0-1-9
status: verified
threats_open: 0
asvs_level: 1
created: 2026-08-25
---

# Phase 13: Security

> Sicherheitsvertrag der Phase: Threat-Register, akzeptierte Risiken und Audit-Trail.
> Register verfasst zur Planzeit (register_authored_at_plan_time: true), verifiziert nach der Implementierung gegen die Artefakte, nicht gegen die SUMMARYs.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Arbeitsbaum zu Git-Tag | Der Tag ist irreversibel und startet den Release-Workflow | Quellstand, Version |
| Repo-Version/-Text zu veröffentlichtem Artefakt | Versionsstring und Store-Beschreibung reisen unveränderlich im signierten Tarball bzw. Katalog | Öffentliche Metadaten |
| Externer Client zu ExApp | CIMD-Client sendet eine https-Adresse, die der Server abruft (untrusted Input) | client_id-Dokumentadresse |
| ExApp zu ausgehendem Netz | CIMD-Abruf ist der einzige ausgehende Request des Pfades; Allowlist vor dem Fetch | HTTPS-Abruf des Metadatendokuments |
| Messlauf zu Owner-Zustand | Echter Client liest `C:\Users\Student\.claude.json`; zwei fremde Instanzen laufen daneben | Client-Konfiguration |
| Messprotokoll zu öffentlichem Repo | `docs/oauth-setup.md` und `.planning/**` sind öffentlich | Beweistexte, potentiell Credentials |
| Lokal gebautes Archiv zu veröffentlichtem Asset | Zwei verschiedene Bytefolgen; nur das heruntergeladene Asset darf signiert werden | Tarball-Bytes, Signatur |
| Privater Signierschlüssel / Store-Token zu Arbeitsbaum | Schlüssel und Token bleiben außerhalb des Repos | Geheimmaterial |
| Automat zu Mensch | Die Owner-Freigabe ist die eine Entscheidung, die kein Kommando ersetzt | Freigabe-Entscheid |
| GitHub Release Asset zu AppAPI-Installation | Administratoren installieren von der Asset-URL, nicht aus dem Store | Veröffentlichtes Artefakt |

---

## Threat Register

Status jeder Zeile per Grep/Kommando gegen die Artefakte verifiziert am 2026-08-25 (Audit nach Abschluss aller sechs Pläne inkl. Review-Fixes WR-01 bis WR-03).

### Plan 13-01 (Version und Changelog)

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-13-01 | Tampering | Sechs Versionsstellen | mitigate | Grep je Stelle: `pyproject.toml` 1, `__init__.py` 1, `<version>0.1.9` und `<image-tag>0.1.9` je genau einmal in `appinfo/info.xml`, drei `Version 0.1.9.`-Statuszeilen, `uv.lock:472`; Gate `tests/unit/test_exapp_env_setup.py:174-177` hält Manifest gegen `__version__` und image-tag; `release.yml` prüfte beim Tag (Lauf 32883904698 success) | closed |
| T-13-02 | Denial of Service | Git-Tag | mitigate | Tag entstand erst in 13-05 nach Owner-Freigabe; Proof-Zeile 18:21Z (`docs/store-submission.md:136`) belegt Tag-Abwesenheit nach dem Push, Freigabe 18:27Z dokumentiert, Tag-Zeile 18:30Z (Zeile 137) danach | closed |
| T-13-03 | Repudiation | CHANGELOG.md | mitigate | 0.1.9-Block (Zeile 12) nennt `message_truncated` (1 Treffer) und `talk-conversations` (1 Treffer); `_ID_KIND`/`one_room`/`test_module_boundaries` 0 Treffer; beide Link-Referenzen je 1 Treffer | closed |
| T-13-04 | Denial of Service | appinfo/info.xml | mitigate | Kein leeres Element im Manifest (Regex-Prüfung: keine), `<summary>` dreisprachig gefüllt, `<environment-variables>` mit 6 `<name>`-Einträgen; Store-Upload antwortete 201, nicht 500 | closed |
| T-13-SC-01 | Tampering | uv.lock, pyproject-Dependencies | mitigate | Bump-Commit `da3673d` numstat: `1 1 uv.lock`, `1 1 pyproject.toml`, kein Dependency-Block, kein Fremdpaketname im Diff | closed |

### Plan 13-02 (Enterprise-Fake-Door)

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-13-05 | Spoofing | Enterprise-Text in vier Fassungen | mitigate | `## Enterprise` je 1 in drei READMEs; Ehrlichkeitssatz ("None of the three exists / Keines der drei existiert / Aucun des trois") je 1; `planned`/`geplant`/`prévu` je 1; Währungs-/Preis-Grep `(EUR|€|$|USD|/month|pro Monat|par mois)` je 0 | closed |
| T-13-06 | Denial of Service | info.xml Store-Upload | mitigate | Nur `<description>`-Elementtext geändert (Commit `bb07df0`: 18 Hinzufügungen, 0 Entfernungen); `<summary>` und `<environment-variables>` gefüllt und unberührt; `variable_problems` Gate vorhanden (`test_exapp_env_setup.py:1794`); Upload 201 | closed |
| T-13-07 | Tampering | Rendering der Store-Beschreibung | mitigate | Gate `description_problems` vorhanden (`test_exapp_env_setup.py:1730`) und grün gelaufen (152 Tests Exit 0); kein `archiv` in info.xml (0 Treffer) | closed |
| T-13-08 | Repudiation | enterprise-signals-issue.md | mitigate | Zeile 6 der Datei: "Not published. Publishing this issue is an owner decision (D-07)."; kein `gh issue create` in der Phase; Issue nicht auf GitHub | closed |
| T-13-09 | Tampering | docs/contrib/227-pr-body.md | mitigate | Datei existiert unverändert am Originalpfad; Vokabular-Gate-Selbsttest hängt daran | closed |
| T-13-SC-02 | Tampering | Paketinstallation | accept | Siehe Accepted Risks R-13-01 | closed |

### Plan 13-03 (CIMD-Nachmessung)

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-13-10 | Information Disclosure | 13-MEASUREMENTS.md, docs/oauth-setup.md | mitigate | Credential-Konvention im Protokollkopf, 6x Platzhalter `<gekürzt>`; Wert-Grep (code_verifier/code_challenge/Bearer/state=/password jeweils MIT Wert) ohne Treffer in beiden Dateien; Namens-Treffer nur als Parameternamen, im Protokoll selbst benannt (Abweichung 5 der 13-03-SUMMARY) | closed |
| T-13-11 | Repudiation | Behauptung "ohne Registrierung" | mitigate | Zwei Belege im Protokoll: `POST /register`-Zählung 0 über das Containerleben (dokumentiertes Kommando und Fenster) UND `clients`-Zeile mit `client_secret_hash` NULL plus gesetzten `cimd_fetched_at`/`cimd_expires_at`; zweiter Beleg `fetch_document_and_lifetime` (317 Bytes, 300 s) | closed |
| T-13-12 | Spoofing | Messweg B als Client-Beweis | mitigate | Messweg A gefahren (Protokoll Abschnitt 2, Zeile 127: echter Client Claude Code 2.1.233 wählte den CIMD-Weg selbst); der bedingte Serverseite-Satz war damit nicht erforderlich, Fallback B wurde nie gebaut | closed |
| T-13-13 | Tampering | Fremde Instanzen und Owner-MCP-Zustand | mitigate | `.claude.json` vor dem Lauf außerhalb des Repos gesichert (Protokoll Zeile 179); `claude mcp add -s local` aus Scratchpad-Projekt `scratchpad\cimd-run` (Zeile 173); `nc-mcp-test` und `findling-nextcloud` als "Up 10 days" belegt (Zeile 548) | closed |
| T-13-14 | Denial of Service | Volume und Autorisierungen | mitigate | `unregister` ohne `--rm-data` (Protokoll: `oauth_data_key`, `public_url` überlebten); Verbindung des Laufs über `/revoke` beendet, janes Zeilen unberührt (13-03-SUMMARY Decision) | closed |
| T-13-15 | Tampering | Instanz in Messkonfiguration | mitigate | Protokoll 4.4: `config:delete oauth_cimd`, disable+enable, `config:list` nennt nur die zwei Vorher-Schlüssel, AS-Dokument `client_id_metadata_document_supported` wieder `true`, Container healthy RestartCount 0 | closed |
| T-13-16 | Repudiation | Toter Verweis / unbelegbarer Beweis | mitigate | `grep '\.planning' docs/oauth-setup.md` 0 Treffer, `06-09-MEASUREMENTS` 0 Treffer; selbsttragende Proof-Zeile "Measured live on 2026-08-25" (Zeile 318) nennt 0.1.9, Client-Version und Gegenprobe | closed |
| T-13-SC-03 | Tampering | Messtreiber und Paketinstallation | mitigate | ConPTY per ctypes (Windows-Bordmittel), Treiber im Scratchpad; kein neuer Treiber unter `scripts/` (git log diff-filter=A leer); `uv.lock`/`pyproject.toml` in 13-03 unberührt | closed |

### Plan 13-04 (Gates und Proof-Zeilen 1-3)

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-13-17 | Tampering | dist/mcp_connector-0.1.9.tar.gz | mitigate | Proof-Zeile Schritt 3 (`docs/store-submission.md:135`) benennt den Lauf wörtlich als "structure check" und sagt "the locally built archive is not the artifact that gets signed"; signiert wurde in 13-06 nur der Download | closed |
| T-13-18 | Repudiation | docs/store-submission.md | mitigate | Drei Zeilen (133-135) im Format Datum UTC + Behauptung + Befehl, zwischen letzter 0.1.8-Zeile (132) und Abschnittsgrenze (145); zum Zeitpunkt von 13-04 keine Zeile zu Schritt 4-8 | closed |
| T-13-19 | Denial of Service | Git-Tag | mitigate | Kein Tag in 13-04; belegt durch die Push-Zeile 136 (18:21Z: "no tag exists", `git tag --list` und `ls-remote` leer), die zeitlich NACH 13-04 liegt | closed |
| T-13-20 | Tampering | Gate-Grenzwerte | mitigate | `scripts/check_tool_budget.py:83` `BUDGET_BYTES = 18_000`, Zeile 117 `MAX_TOOL_BYTES = 1400`, unverändert; Messung traf 15711 Bytes exakt, kein Anheben nötig | closed |
| T-13-21 | Information Disclosure | dist/ im Arbeitsbaum | accept | Siehe Accepted Risks R-13-02 | closed |
| T-13-SC-04 | Tampering | Paketinstallation | mitigate | Alle sechs Gates mit `uv run --no-sync` (Proof-Zeile 135 nennt das Präfix je Kommando); kein Install-Kommando in der Phase, Lockfile-Diff nur die Selbstangabe (T-13-SC-01) | closed |

### Plan 13-05 (Push, Freigabe, Tag, Workflow)

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-13-22 | Denial of Service | Tag v0.1.9 | mitigate | Blockierender Checkpoint gehalten: wörtliche Antwort `freigeben` um 2026-08-25T18:27Z im 13-05-SUMMARY festgehalten; Tag-Zeile 137 (18:30Z) sagt "only after an explicit owner release at 18:27Z"; Tag `685295d` entstand nach der Freigabe | closed |
| T-13-23 | Tampering | Tag-Name | mitigate | `git tag --list` zeigt exakt `v0.1.9`, kein Tippfehler-Tag, kein Milestone-Tag neu; `release.yml`-Gleichheitsprüfung passiert (Lauf success) | closed |
| T-13-24 | Denial of Service | Release-Asset und Tag-Historie | mitigate | Live geprüft: `gh release list` nennt genau ein `v0.1.9` (Latest); Tag remote auf `685295d7d1...`, kein Force-Tag; Asset antwortet 302 dann 200 | closed |
| T-13-25 | Repudiation | Proof-Zeile Schritt 4/5 | mitigate | Zeile 137 entstand nach dem grünen Lauf und trägt Run-Id 32883904698, Job `publish`, 1m40s, Exit 0; Aufteilung in zwei Zeilen (Push separat, 18:21Z) stärkt die Beweisrichtung (dokumentierte Scope-Erweiterung in 13-05-SUMMARY) | closed |
| T-13-26 | Tampering | Nicht gepushter Stand unter Tag | mitigate | Zeile 136: `git log origin/main..HEAD` zählt 0 nach dem Push, vor der Tag-Entscheidung; `git merge-base --is-ancestor v0.1.9 origin/main` bestätigt: Tag liegt auf dem öffentlichen Branch. Review-Befund IN-02 (18:21Z-Zeile zertifiziert 22471c1, Tag zeigt auf den einen Commit späteren 685295d, der im selben Schritt vor dem Tag gepusht wurde) ändert am Ergebnis nichts | closed |
| T-13-27 | Repudiation | Changelog-Datum | mitigate | `## [0.1.9] - 2026-08-25` (CHANGELOG.md:12) trifft den Kalendertag des Tags (18:27Z UTC am 2026-08-25); Prüfung lief, kein Eingriff nötig | closed |
| T-13-SC-05 | Tampering | Build im Workflow | transfer | Transfer-Dokumentation vorhanden: Image und Archiv im GitHub-Workflow aus dem getaggten Quellstand gebaut (Run 32883904698, Zeile 137); Lieferketten-Nachweise (OCI-Index, Tagliste) in 13-06 erbracht (Zeilen 142/143) | closed |

### Plan 13-06 (Signatur, Store-Upload, Nachweise)

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-13-28 | Tampering | Signatur über das falsche Artefakt | mitigate | Proof-Zeile Schritt 6 (`docs/store-submission.md:138`): signiert wurde die per `curl -sSLO` geholte Datei (47264 Bytes, sha256 `a2b9bc33…`), `openssl dgst -sha512 -verify` gab wörtlich `Verified OK`; Differenz zum lokalen Archiv (47546 Bytes, `4f2a05fe…`) als Beweis in der Zeile | closed |
| T-13-29 | Information Disclosure | Privater Schlüssel und Store-Token | mitigate | Greps über `docs` und `.planning`: kein `BEGIN [RSA ]PRIVATE KEY`, kein `NC_STORE_TOKEN=<wert>`, kein `Authorization: Token <wert>` außer den wörtlichen Muster-Selbstzitaten in 13-06-PLAN.md/-SUMMARY.md (Namensnennungen ohne Wert); Token blieb im Browser-Seitenkontext | closed |
| T-13-30 | Information Disclosure | Base64-Signatur in einem Commit | mitigate | Alle drei 13-06-Commits (`4b7668e`, `f714573`, `bba1df7`) geprüft: keine Base64-Kette über 100 Zeichen; Signatur steht in keinem Dokument, sie wird per Runbook-Schritt 6 neu berechnet | closed |
| T-13-31 | Denial of Service | Store-Upload 500 | mitigate | Keine leeren XML-Elemente im Manifest (Regex-Prüfung); Beschreibungs- und Variablen-Gates liefen in 13-02/13-04; Upload antwortete 201 (Zeile 139), kein nachträglicher Manifest-Eingriff | closed |
| T-13-32 | Denial of Service | Zweites Release wegen Cache | mitigate | Katalog-Zeile 140 dokumentiert beide Zeitpunkte (18:41Z alte Liste, 18:46Z Fund, 6 Minuten Cache); live geprüft: genau ein `v0.1.9` in `gh release list` | closed |
| T-13-33 | Denial of Service | Gelöschtes Asset, umgeschriebener Tag | mitigate | Pflicht-Nachweiszeile 141 (`curl -I` 302 dann 200 mit 47264 Bytes); im Audit live nachgemessen: 302 dann 200; Tag unverändert auf `685295d` | closed |
| T-13-34 | Repudiation | Proof-Zeilen Schritte 6-8 | mitigate | Sieben Zeilen (138-143), jede nach ihrem Ereignis mit Datum, Zahl/Statuscode und Befehl; Reihenfolge folgt den Runbook-Schritten (Review-Info IN-01: innerhalb Schritt 8 nicht streng chronologisch, Beweisrichtung unberührt) | closed |
| T-13-SC-06 | Tampering | Herkunft des veröffentlichten Images | transfer | Transfer-Dokumentation vorhanden: OCI-Index-Zeile 142 (`linux/amd64` + `linux/arm64` + Attestation-Einträge) und Tagliste-Zeile 143 (zehn Tags, keiner umgeschrieben) belegen den Workflow-Build bei GitHub Actions/ghcr.io; kein lokaler Upload | closed |

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| R-13-01 | T-13-SC-02 | Plan 13-02 ändert ausschließlich Markdown und XML-Elementtext; kein Paketmanager wird aufgerufen, es existiert kein Installationskandidat. Verifiziert: die drei 13-02-Commits enthalten nur Text-Hinzufügungen (167 Zeilen, 0 Entfernungen), Lockfile unberührt. | Plan-Autor (13-02 threat_model), bestätigt im Audit | 2026-08-25 |
| R-13-02 | T-13-21 | `dist/` ist gitignored (`.gitignore:17`) und hält nur Archive aus öffentlichem Quellcode; nichts daraus wird committet. Verifiziert: `git ls-files dist` leer, `git check-ignore` greift. | Plan-Autor (13-04 threat_model), bestätigt im Audit | 2026-08-25 |

---

## Unregistered Flags

Keine. Nur 13-05-SUMMARY führt einen Abschnitt `## Threat Flags` ("Keine neue Sicherheitsoberfläche", mit Mapping auf T-13-22/23/24). Die übrigen fünf SUMMARYs melden keine Flags; ihre Abweichungen wurden geprüft und mappen auf bestehende Threats:

- 13-03 Abweichung 5 (Credential-Grep strenger als seine Absicht) → T-13-10, im Protokoll selbst benannt, keine Werte offengelegt.
- Review-Fix WR-03 (`f3faefd`): das interne Go-Kriterium des Fake-Door-Tests stand im öffentlichen Issue-Entwurf (Information Disclosure, nicht im Register). Behoben vor dem Audit: verschoben nach `.planning/phases/13-cimd-nachmessung-und-release-0-1-9/enterprise-issue-go-kriterium.md`; der öffentliche Entwurf trägt nur noch Ziel-Repo, Titel und die Owner-Entscheidungs-Zeile. Kein offener Rest.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-08-25 | 40 | 40 | 0 | gsd-security-auditor (Claude) |

Verifikationsmethode: jede `mitigate`-Zeile per Grep/Kommando gegen die zitierten Artefakte (nicht gegen SUMMARY-Behauptungen); `accept` gegen diesen Accepted-Risks-Log; `transfer` gegen die dokumentierten Workflow-/Registry-Nachweise. Zusätzlich drei Live-Messungen: Asset-Erreichbarkeit (302→200), Release-Einzigkeit (`gh release list`), Tag-Ancestry (`git merge-base --is-ancestor`).

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-08-25
