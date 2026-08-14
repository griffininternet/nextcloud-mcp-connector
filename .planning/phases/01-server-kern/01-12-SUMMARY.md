---
phase: 01-server-kern
plan: 12
subsystem: infra
tags: [documentation, github, app-store, naming, agpl, permissions]

# Dependency graph
requires:
  - phase: 01-server-kern (Plan 01-01)
    provides: Repo-Skelett, pyproject mit Paket- und CLI-Namen, LICENSE (AGPL-3.0-or-later)
provides:
  - Eingefrorene App-ID mcp_connector mit dokumentierten Verfuegbarkeitsbelegen (2026-08-14)
  - README mit Sicherheitsversprechen, Env-Variablen und Permission-Tabelle fuer alle 15 v1-Tools
  - Oeffentliches GitHub-Repo street1983nk/nextcloud-mcp-connector mit origin-Remote und gepushtem main
affects: [01-13 (Fork und PR an context_agent), 01-14 (Verifikation der Tool-Tabelle gegen die Registry), Phase 5 (CSR und Store-Einreichung)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Namens-Freeze als eigenes Dokument mit reproduzierbaren Pruefkommandos statt als Fussnote"
    - "Permission-Level (read / create-only) als oeffentliche Doku-Tabelle, die Plan 14 automatisiert gegen die Tool-Registry prueft"

key-files:
  created:
    - README.md
    - docs/app-id-freeze.md
  modified: []

key-decisions:
  - "Repo-Sichtbarkeit: option-a, alles oeffentlich inklusive .planning (Owner-Entscheidung, T-01-84 disposition accept)"
  - "PyPI-Verfuegbarkeit wird ueber /pypi/<name>/json und /simple/<name>/ geprueft, nicht ueber die HTML-Projektseite: diese antwortet wegen einer Bot-Challenge auch fuer unbekannte Namen mit 200"
  - "TOOL-09 bleibt Pending: dieser Plan liefert nur die Dokumentationshaelfte, der Nachweis 'kein Tool kann loeschen oder ueberschreiben' gehoert zu Plan 14"

patterns-established:
  - "Freeze-Dokumente nennen die Kosten einer spaeteren Aenderung explizit (hier: Zertifikatsbindung nach dem CSR-Merge)"
  - "Vor jedem Push in ein oeffentliches Repo laeuft eine Secret-Gegenprobe per git grep (T-01-83)"

requirements-completed: [EXAPP-03]

# Metrics
duration: 14 min
completed: 2026-08-14
---

# Phase 1 Plan 12: App-ID-Freeze, README und oeffentliches Repo Summary

**App-ID mcp_connector mit vier frisch geprueften Verfuegbarkeitsbelegen eingefroren, englisches README mit Permission-Tabelle fuer alle 15 v1-Tools, und das oeffentliche AGPL-Repo street1983nk/nextcloud-mcp-connector steht mit gepushtem main.**

## Performance

- **Duration:** 14 min
- **Started:** 2026-08-14T15:36:00Z
- **Completed:** 2026-08-14T15:50:00Z
- **Tasks:** 3 (davon 1 Decision-Checkpoint)
- **Files modified:** 2 erstellt (README.md, docs/app-id-freeze.md), 0 geaendert

## Accomplishments

- **App-ID eingefroren und belegt.** `docs/app-id-freeze.md` haelt alle sieben Identifier fest (App-ID `mcp_connector`, Anzeigename "MCP Connector", Python-Package `mcp_connector`, PyPI `nextcloud-mcp-connector`, CLI `nc-mcp`, Repo `nextcloud-mcp-connector`, Lizenz AGPL-3.0-or-later), begruendet sie (Store-Regel gegen "nextcloud" in der ID, belegter PyPI-Name `nextcloud-mcp-server`) und beziffert die Kosten einer Umbenennung nach dem CSR-Merge.
- **Vier Verfuegbarkeitsbelege, alle am 2026-08-14 frisch erhoben** (nicht aus der Research uebernommen): PyPI JSON-API und Simple-Index 404 fuer `nextcloud-mcp-connector` (Kontrolle: `nextcloud-mcp-server` 200), Store-API fuer Plattform 34.0.0 (378 Apps) und 30.0.0 (423 Apps) ohne eine einzige ID mit "mcp", Store-Seite `/apps/mcp_connector` 404 gegen Kontrolle `/apps/notes` 200, sowie `nextcloud/app-certificate-requests` mit 838 Verzeichnissen, keinem "mcp"-Treffer und Code-Suche `total_count: 0`.
- **Permission-Modell oeffentlich.** Das README listet alle 15 Tools mit Spalte "Permission" (11 mal read, 4 mal create-only), enthaelt das woertliche Sicherheitsversprechen "This server can never delete, overwrite or re-share anything." und den Abschnitt "What this server cannot do" (kein Loeschen, kein Ueberschreiben, kein Move/Rename, keine Share-Aenderung, kein Admin-Zugriff, keine Inhaltssuche ohne Full-text-search-App).
- **Oeffentliches Repo live.** `https://github.com/street1983nk/nextcloud-mcp-connector` ist PUBLIC, GitHub erkennt die Lizenz als `agpl-3.0`, Default-Branch `main`, `origin` verdrahtet, HEAD und `origin/main` identisch.
- **Autoren-Gate bestanden.** `git log --format="%an <%ae>" | sort -u` liefert vor dem Push ausschliesslich `street1983nk <k.cherif@outlook.de>`, kein Committer-Fremdeintrag, kein einziger `Co-Authored-By`-Trailer in der gesamten Historie.

## Task Commits

1. **Task 1: README und Freeze-Dokumentation mit frisch geprueften Belegen** - `025112b` (docs)
2. **Task 2: Entscheidung zur Veroeffentlichung des Repos** - kein Commit (Checkpoint, siehe Decisions)
3. **Task 3: GitHub-Repo anlegen und Remote verdrahten** - kein Commit (Infrastruktur-Aktion; option-a laesst `.gitignore` unveraendert, es gab nichts zu committen). Ergebnis: Repo angelegt, `main` gepusht (`025112b`).

**Plan metadata:** siehe docs-Commit dieses Plans.

## Files Created/Modified

- `README.md` - Projektvorstellung, woertliches Sicherheitsversprechen, stdio-Quickstart mit Client-Config-Beispiel, HTTP-Modus, Env-Variablen-Tabelle (`NC_MCP_URL`, `NC_MCP_USER`, `NC_MCP_APP_PASSWORD`, `NC_MCP_ALLOWED_HOSTS`, `NC_MCP_STATIC_BEARER`), Tool-Tabelle mit Permission-Level, "What this server cannot do", Dev-Kommandos, Lizenz, Link auf den Freeze
- `docs/app-id-freeze.md` - Freeze-Entscheidung, Begruendung, vier Verfuegbarkeitsbelege mit Datum und Kommando, Kostenanalyse einer Umbenennung nach dem CSR

## Decisions Made

- **Checkpoint Task 2 (Repo-Sichtbarkeit): option-a, alles oeffentlich inklusive `.planning`.** Im Auto-Modus auto-approved, gedeckt durch die bereits vorliegende Owner-Entscheidung in `.planning/PROJECT.md` ("Repo: public auf GitHub street1983nk") und der Session-Notiz vom 2026-08-14. Konsequenz bewusst akzeptiert (T-01-84): Strategie, Wettbewerbsvergleich und Terminplanung sind oeffentlich lesbar, dafuer keine Historie-Akrobatik und maximale Glaubwuerdigkeit im Open-Source-Umfeld. `.gitignore` bleibt unveraendert.
- **PyPI-Pruefmethode korrigiert.** Die HTML-Projektseite ist als Verfuegbarkeitsbeleg unbrauchbar (siehe Deviations), maschinelle Pruefungen laufen ueber `pypi.org/pypi/<name>/json` und `pypi.org/simple/<name>/`. Diese Methodennotiz steht im Freeze-Dokument, damit spaetere Pruefungen nicht in dieselbe Falle laufen.
- **Store-Gegenprobe ueber zwei Plattform-Generationen.** `apps.json` ist plattformgefiltert, eine nur fuer aeltere Nextcloud-Versionen veroeffentlichte App waere in der 34.0.0-Abfrage unsichtbar geblieben. Deshalb zusaetzlich 30.0.0 plus die direkte Store-Seite.
- **TOOL-09 wird nicht abgehakt.** Nur EXAPP-03 ist erfuellt; die zweite Haelfte von TOOL-09 (kein Tool kann loeschen, ueberschreiben oder Freigaben aendern) ist erst mit dem Grep- und Registry-Nachweis aus Plan 14 belegt. Ein Haken auf Basis eines README-Versprechens waere genau der Tampering-Fall T-01-86.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Verfuegbarkeitsbeleg fuer PyPI lieferte ein falsches Ergebnis**
- **Found during:** Task 1 (Belege frisch nachpruefen)
- **Issue:** Das im Plan vorgegebene Kommando `curl -s -o /dev/null -w "%{http_code}" https://pypi.org/project/nextcloud-mcp-connector/` antwortete mit **200**, obwohl die Research 404 dokumentiert hatte. Ohne Gegenpruefung waere daraus der falsche Schluss "Name belegt" gezogen und der Freeze auf einer Fehlinformation aufgebaut worden. Ursache: PyPI schaltet vor die HTML-Seite eine Anti-Bot-Challenge, die fuer jeden Pfad 200 liefert.
- **Fix:** Umstieg auf die maschinenlesbaren Endpunkte `https://pypi.org/pypi/<name>/json` (404) und `https://pypi.org/simple/<name>/` (404), jeweils mit Kontrollmessung gegen den belegten Namen `nextcloud-mcp-server` (200 / 200). Beide Kommandos, beide Ergebnisse und die Methodenwarnung stehen im Freeze-Dokument.
- **Files modified:** `docs/app-id-freeze.md`
- **Verification:** Vier Messungen, zwei davon Kontrollen mit bekanntem Erwartungswert
- **Committed in:** `025112b`

**2. [Rule 2 - Missing Critical] Store-Beleg gegen nur eine Plattformversion war luechenhaft**
- **Found during:** Task 1
- **Issue:** Der Plan sah nur `platform/34.0.0/apps.json` vor. Diese Liste ist versionsgefiltert (378 Apps), eine App mit der ID `mcp_connector`, die nur fuer aeltere Nextcloud-Releases veroeffentlicht ist, waere unentdeckt geblieben. Beim Store-Zertifikat haengt genau daran der Freeze (T-01-85).
- **Fix:** Zusaetzliche Abfrage `platform/30.0.0/apps.json` (423 Apps, ebenfalls kein Treffer) und die direkte Store-Seite `https://apps.nextcloud.com/apps/mcp_connector` (404) mit Kontrolle `/apps/notes` (200).
- **Files modified:** `docs/app-id-freeze.md`
- **Verification:** Drei unabhaengige Store-Messungen, eine davon Kontrolle
- **Committed in:** `025112b`

**3. [Rule 2 - Missing Critical] Secret-Gegenprobe vor dem Push ausgeweitet**
- **Found during:** Task 3 (vor der Repo-Erstellung)
- **Issue:** Das Threat-Modell (T-01-83) nennt nur `git grep` auf `NC_MCP_APP_PASSWORD=`. Beim erstmaligen Oeffentlichmachen eines Repos ist das zu eng: Tokens, Fremd-Secrets und private Pfade waeren durchgerutscht.
- **Fix:** Vor dem Push zusaetzlich geprueft: generische Secret-Muster (`password|secret|token|api_key` mit einem Literalwert ab 12 Zeichen), GitHub- und Slack-Token-Praefixe (`gh[pousr]_`, `xox[baprs]-`), getrackte `.env`-Dateien, sowie lokale Windows-Pfade ausserhalb von `.planning`. Ergebnis: nur der Platzhalter `NC_MCP_APP_PASSWORD=xxxxx-...` im README-Quickstart, keine getrackte `.env`, keine Tokens. Die einzigen E-Mail-Adressen in `.planning` sind oeffentliche PyPI-Maintainer-Angaben aus einem zitierten Audit.
- **Files modified:** keine (reine Pruefung)
- **Verification:** 5 Grep-Laeufe ueber alle getrackten Dateien, alle ohne Fund
- **Committed in:** kein Commit noetig

**4. [Rule 1 - Bug] Verifikationskommandos scheiterten am Windows-Pfadbruch**
- **Found during:** Task 1
- **Issue:** `curl -o /tmp/...` unter Git Bash schreibt in den MSYS-Baum, das anschliessende (native Windows-)`uv run python` fand die Datei nicht (`FileNotFoundError`).
- **Fix:** Downloads in einen absoluten Windows-Pfad geschrieben und von dort gelesen.
- **Files modified:** keine (nur Ausfuehrungsweg)
- **Verification:** Store-Abfragen liefen anschliessend durch
- **Committed in:** kein Commit noetig

### Bewusste Abweichung ohne Auto-Fix

**5. Requirement TOOL-09 nicht abgehakt.** Die Plan-Frontmatter nennt `requirements: [EXAPP-03, TOOL-09]`. Abgehakt wurde nur EXAPP-03. Begruendung siehe "Decisions Made": TOOL-09 verlangt neben der Dokumentation auch den technischen Nachweis der Schreibgrenzen, der in Plan 14 (Grep-Test gegen destruktive Aufrufe, Registry-Abgleich der Tabelle) erbracht wird. Diese Trennung folgt dem Vorgehen aus 01-02, wo ebenfalls nur das tatsaechlich bewiesene Requirement abgehakt wurde.

---

**Total deviations:** 4 auto-fixed (2 Bugs, 2 fehlende kritische Absicherungen) plus 1 bewusste Requirement-Zurueckhaltung
**Impact on plan:** Kein Scope-Creep. Zwei der vier Auto-Fixes betreffen die Beweisfuehrung des Freezes selbst: ohne sie waere die App-ID auf einem falschen (PyPI) beziehungsweise unvollstaendigen (Store) Beleg eingefroren worden, und genau daran haengt spaeter das Store-Zertifikat.

## Issues Encountered

- Der Endpunkt `https://apps.nextcloud.com/api/v1/apps/mcp_connector` antwortet mit HTTP 500 (existiert in dieser Form nicht). Er wurde verworfen und durch die Plattform-Abfragen plus die Store-Seite ersetzt. Kein offener Punkt.
- `gsd-sdk query state.record-metric` mit positionalen Argumenten wird von v1.42.3 nicht akzeptiert ("phase, plan, and duration required"), der Aufruf braucht benannte Flags. Der Metrik-Eintrag wurde entsprechend gesetzt.

## Threat Flags

Keine neue Sicherheitsflaeche. Dieser Plan enthaelt keinen Produktionscode; alle Kontrollen bleiben bei den Plaenen 02, 03, 05, 07 und 08 (T-01-87, disposition transfer).

Erledigte Dispositionen aus dem Threat-Modell des Plans:

| Threat ID | Disposition | Status |
|-----------|-------------|--------|
| T-01-83 | mitigate | Erfuellt: erweiterte Secret-Gegenprobe vor dem Push, kein Fund, keine getrackte `.env` |
| T-01-84 | accept | Erfuellt: Owner-Entscheidung option-a dokumentiert, Konsequenz benannt |
| T-01-85 | mitigate | Erfuellt: vier Verfuegbarkeitsbelege inklusive Kontrollmessungen, Freeze mit Kostenanalyse |
| T-01-86 | mitigate | Offen bis Plan 14: die Tabelle ist geschrieben, der automatisierte Registry-Abgleich steht aus |
| T-01-87 | transfer | Unveraendert an die Code-Plaene uebergeben |

## Known Stubs

Keine. Der Plan liefert Dokumentation und Repo-Infrastruktur, keinen Code mit Datenanbindung. Die Tool-Tabelle im README beschreibt bewusst das vollstaendige v1-Tool-Set, obwohl aktuell nur `files_read` registriert ist; das README weist im Abschnitt "Status" ausdruecklich darauf hin und Plan 14 gleicht die Tabelle gegen die Registry ab.

## User Setup Required

None - no external service configuration required. Das GitHub-Repo wurde mit dem bereits authentifizierten `gh`-CLI (Konto `street1983nk`, Scope `repo`) angelegt.

## Next Phase Readiness

- **Der CSR-Prozess kann jetzt angestossen werden.** Beide Voraussetzungen stehen: die App-ID `mcp_connector` ist eingefroren und belegt, und das oeffentliche Repo existiert. Der CSR-PR an `nextcloud/app-certificate-requests` ist damit von den restlichen Phase-1-Plaenen entkoppelt und sollte wegen der Lead-Time sofort starten, nicht erst in Phase 5.
- **Plan 01-13 (Contribution-PR an context_agent#227) ist entblockt**, das GitHub-Konto und die oeffentliche Referenz auf das eigene Projekt stehen.
- **Plan 01-14 uebernimmt die offene Pflicht:** Abgleich der README-Tool-Tabelle gegen die tatsaechliche Registry und der Grep-Nachweis gegen destruktive Aufrufe; erst danach wird TOOL-09 abgehakt.
- **Push-Pfad ist ab jetzt vorhanden.** Die globale Regel "nach jedem Edit committen und pushen" ist erst ab diesem Plan technisch erfuellbar; folgende Plaene sollten pushen.

## Self-Check: PASSED

- `README.md` vorhanden, `docs/app-id-freeze.md` vorhanden, `01-12-SUMMARY.md` vorhanden
- Commit `025112b` in `git log --all` gefunden
- Plan-Verifikation 1: `grep -c "create-only" README.md` = 7, alle 15 Tool-Namen vorhanden, kein Em- oder En-Dash in README, Freeze-Dokument und SUMMARY, Sicherheitssatz woertlich enthalten
- Plan-Verifikation 2: `gh repo view` liefert `nextcloud-mcp-connector PUBLIC`, `git remote -v | grep -c origin` = 2, `HEAD` = `origin/main` = `025112b`
- Plan-Verifikation 3: Secret-Gegenprobe ohne Fund (der einzige Treffer auf `NC_MCP_APP_PASSWORD=` ausserhalb des README-Platzhalters ist eine Shell-Variablenreferenz `${ALICE_PW}` in der Research)
- Autoren-Gegenprobe: `git log --format="%an <%ae>" | sort -u` = `street1983nk <k.cherif@outlook.de>`, keine `Co-Authored-By`-Trailer

---
*Phase: 01-server-kern*
*Completed: 2026-08-14*
