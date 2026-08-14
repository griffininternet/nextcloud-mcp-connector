---
phase: 01-server-kern
plan: 13
subsystem: contribution
tags: [context_agent, fastmcp, stateless_http, dco, upstream, github]

requires:
  - phase: 01-server-kern (Plan 04)
    provides: tests/compat/legacy_client_check.py als automatisierter Beleg der #227-Fehlerklasse
  - phase: 01-server-kern (Plan 12)
    provides: App-ID-Freeze und oeffentliches Repo street1983nk/nextcloud-mcp-connector
provides:
  - Fork street1983nk/context_agent mit Branch fix/stateless-http-session-compat
  - DCO-signierter Commit def1425 mit genau einer funktionalen Aenderung in ex_app/lib/main.py
  - docs/contrib/227-pr-body.md als fertiger PR-Text mit Reproduktionsanleitung
affects: [CONTRIB-01, Oekosystem-Beziehung zum Nextcloud-Team, Phase 5 App-Store-Einreichung]

tech-stack:
  added: []
  patterns:
    - "Upstream-Beitraege laufen ueber einen Fork ausserhalb unseres Repos, nur editiert, nie ausgefuehrt"
    - "Fremdrepo-Commits mit git commit -s (DCO), lokale git-Identitaet street1983nk / k.cherif@outlook.de"
    - "Der PR-Body liegt versioniert bei uns und wird per --body-file eingereicht"

key-files:
  created:
    - docs/contrib/227-pr-body.md
  modified: []

key-decisions:
  - "stateless_http wird konfigurierbar statt hart False: behebt den Bug per Default und nimmt niemandem den stateless Transport weg (hoechste Merge-Wahrscheinlichkeit bei minimalem Diff)"
  - "Der Regressionstest bleibt in unserem Repo: ein Legacy-Client-Lauf im fremden CI braeuchte ein zweites Client-Environment gegen einen laufenden ExApp-Container und wuerde dort nur Rauschen erzeugen"
  - "Die PR-Metadaten (Branch, Commit, PR-URL-Platzhalter) stehen als HTML-Kommentar im Body-File, damit dieselbe Datei unveraendert als --body-file dienen kann"

patterns-established:
  - "Vorpruefung vor jedem Upstream-PR: Issue-Status und offene PRs auf Dopplung pruefen"
  - "Ausgehende Kommunikation unter street1983nk wird vom Owner ausgeloest, nie vom Agenten"

requirements-completed: []  # CONTRIB-01 und SRV-01 bleiben Pending bis der Owner den PR eingereicht hat

duration: 17 min
completed: 2026-08-14
---

# Phase 1 Plan 13: Contribution-PR an nextcloud/context_agent#227 Summary

**Einreichfertiger Ein-Zeilen-Fix im Fork street1983nk/context_agent: stateless_http wird per MCP_STATELESS_HTTP umschaltbar und ist per Default sessionfaehig, DCO-signiert, mit fertigem PR-Text und Reproduktionsanleitung.**

> **Status: vorbereitet, wartet auf Owner.** Der Human-Action-Checkpoint (Task 2) ist offen:
> die PR-Einreichung selbst macht der Owner. Task 3 des Plans (gh pr create, PR-URL
> dokumentieren) ist NICHT ausgefuehrt. ROADMAP 01-13 bleibt deshalb unmarkiert und
> CONTRIB-01 bleibt Pending.

## Performance

- **Duration:** 17 min (Task 1, ohne den offenen Checkpoint)
- **Started:** 2026-08-14T18:32:00Z
- **Completed:** 2026-08-14T18:49:30Z (Task 1)
- **Tasks:** 1 von 3 (Task 2 = Checkpoint offen, Task 3 = Owner-Schritt)
- **Files modified:** 1 in unserem Repo, 1 im Fork

## Accomplishments

- Vorpruefung: Issue #227 ist offen (erstellt 2026-08-08), keiner der sechs offenen PRs
  (#229, #226, #218, #215, #177, #159) beruehrt `stateless_http`. Keine Dopplung, der PR ist frei.
- Fork `street1983nk/context_agent` angelegt und nach `C:\Users\Student\context_agent-fork\context_agent`
  geklont, ausserhalb unseres Repos (T-01-92: nur editieren, nicht installieren, nicht starten).
- Branch `fix/stateless-http-session-compat` mit genau einer funktionalen Aenderung in
  `ex_app/lib/main.py` (1 Datei, 4 Insertions, 1 Deletion), Commit `def1425` mit
  `Signed-off-by: street1983nk <k.cherif@outlook.de>` und ohne Co-Authored-By-Trailer.
- Branch in den Fork gepusht, per GitHub-API verifiziert
  (sha `def1425b89b375b090c452f6008511b198abb725`).
- `docs/contrib/227-pr-body.md` geschrieben: Problem, Ursache, Fix, Rueckwaertskompatibilitaet,
  Reproduktion als Kommandofolge mit gepinntem `mcp>=1.29,<2`-Client, Verweis auf
  `tests/compat/legacy_client_check.py` und `tests/compat/test_client_matrix.py` als Belegquelle.

## Der Diff im Fork

```diff
-http_mcp_app = mcp.http_app("/", transport="http", stateless_http=True)
+# Session-capable by default: SDK >= 1.28 clients keep the session after initialize
+# and fail with "Session terminated" when the transport is stateless. See #227.
+_stateless_http = os.getenv("MCP_STATELESS_HTTP", "0").lower() in ("1", "true", "yes")
+http_mcp_app = mcp.http_app("/", transport="http", stateless_http=_stateless_http)
```

`os` ist in dem Modul bereits importiert, deshalb bleibt es bei einer Datei. Die
`http_app`-Signatur von fastmcp 2.14.7 bleibt unangetastet, der Fix ist also unabhaengig
vom offenen fastmcp-3.x-Bump (#177). Keine neue Datei, damit greift das REUSE-Gate des
Zielrepos nicht.

## Task Commits

1. **Task 1 (unser Repo): PR-Body** - `f535859` (docs)
2. **Task 1 (Fork): Ein-Zeilen-Fix** - `def1425` (fix, DCO-signiert, nicht in unserem Repo)
3. **Task 2: Checkpoint human-verify/human-action** - offen, Owner
4. **Task 3: PR einreichen** - nicht ausgefuehrt, Owner

**Plan metadata:** siehe letzter docs(01-13)-Commit.

## Files Created/Modified

- `docs/contrib/227-pr-body.md` - fertiger PR-Text (englisch), dient per `--body-file` direkt als PR-Body
- `ex_app/lib/main.py` im Fork - die eine funktionale Aenderung (nicht in unserem Repo)

## Offener Owner-Schritt

Fertiges Kommando (aus dem Wurzelverzeichnis unseres Repos ausfuehren):

```bash
cd C:/Users/Student/nextcloud-mcp-connector && gh pr create \
  --repo nextcloud/context_agent \
  --head street1983nk:fix/stateless-http-session-compat \
  --title "fix(mcp): make stateless_http configurable and session-capable by default" \
  --body-file docs/contrib/227-pr-body.md
```

Vorher pruefen:

1. `cd C:/Users/Student/context_agent-fork/context_agent && git diff upstream/main...fix/stateless-http-session-compat`
   zeigt genau eine geaenderte Datei.
2. `docs/contrib/227-pr-body.md` lesen: Ton sachlich, keine Werbung ueber den fachlichen
   Verweis auf den Regressionstest hinaus.
3. Der PR-Body verlinkt `https://github.com/street1983nk/nextcloud-mcp-connector` und nennt
   `tests/compat/legacy_client_check.py`. Diese Datei ist lokal committet, aber noch **nicht**
   nach origin gepusht. Vor der Einreichung `git push origin main` im Connector-Repo, sonst
   findet ein Reviewer die Belegquelle nicht.
4. Bestaetigen, dass der PR unter dem Konto street1983nk rausgehen soll.

Nach der Einreichung: PR-URL und Datum in den HTML-Kommentarkopf von
`docs/contrib/227-pr-body.md` eintragen, ROADMAP-Zeile 01-13 abhaken, CONTRIB-01 auf
Complete setzen.

## Erwartungsmanagement zum fremden CI

`integration_test.yml` im Zielrepo faehrt eine schwere Matrix (server-versions master,
stable33, stable32, stable31, dazu die llm2-App mit Modell-Cache). Lange Laufzeiten und
flakige Jobs ohne Bezug zum Fix sind dort normal. Kein Nachfassen im Repo ohne Owner-Auftrag.

## Decisions Made

- **Konfigurierbar statt hart `False`:** Der Default behebt den Bug, `MCP_STATELESS_HTTP=1`
  erhaelt das alte Verhalten fuer Multi-Worker-Setups ohne Sticky Routing. Der PR-Body bietet
  ausdruecklich an, auf ein einfaches `stateless_http=False` zu wechseln, falls die Maintainer
  die kleinere Oberflaeche bevorzugen.
- **Kein Test im fremden CI:** Der Repro-Lauf braucht einen zweiten Client auf der 1.x-SDK-Linie
  gegen einen laufenden ExApp-Container. Der PR beschreibt die Reproduktion praezise und
  verweist auf unseren automatisierten Test (D-19).
- **PR-Metadaten als HTML-Kommentar:** So kann dieselbe Datei ohne Nachbearbeitung als
  `--body-file` dienen und der URL-Platzhalter taucht nicht im gerenderten PR auf.
- **git-Identitaet nur lokal im Fork-Clone gesetzt** (`k.cherif@outlook.de`), die globale
  Konfiguration bleibt unberuehrt.

## Deviations from Plan

### Abweichungen

**1. [Ausfuehrungsauftrag] Task 3 bewusst nicht ausgefuehrt**
- **Found during:** Task 2 (Checkpoint)
- **Issue:** Der Plan sieht die Einreichung durch den Agenten nach Freigabe vor. Der
  Ausfuehrungsauftrag dieses Laufs legt die Einreichung ausdruecklich in die Hand des Owners
  (ausgehende Kommunikation, Regel "Owner sendet Outreach selbst").
- **Fix:** Task 1 vollstaendig ausgefuehrt, am Checkpoint gestoppt, das fertige
  `gh pr create`-Kommando dokumentiert statt es auszufuehren.
- **Files modified:** keine zusaetzlichen
- **Verification:** Kein PR unter nextcloud/context_agent von street1983nk vorhanden.

**2. [Rule 2 - Missing Critical] Push-Vorbedingung fuer den Beleg-Link ergaenzt**
- **Found during:** Task 1 (PR-Body)
- **Issue:** `tests/compat/legacy_client_check.py` ist lokal committet, aber noch nicht nach
  `origin/main` gepusht. Ein Deep-Link in den PR-Body waere zum Zeitpunkt der Einreichung 404.
- **Fix:** Der PR-Body verlinkt das Repo und nennt die Pfade im Text statt eines Deep-Links;
  die Push-Vorbedingung steht als Owner-Pruefpunkt in dieser SUMMARY.
- **Files modified:** docs/contrib/227-pr-body.md
- **Verification:** `gh api repos/street1983nk/nextcloud-mcp-connector/contents/tests/compat`
  listet aktuell nur `test_stdio_startup.py`.

---

**Total deviations:** 2 (1 Auftragsvorrang, 1 Rule 2)
**Impact on plan:** Kein Scope-Kriechen. Der technische Inhalt des Plans ist vollstaendig
umgesetzt, nur der letzte, bewusst menschliche Schritt fehlt.

## Issues Encountered

- Der Fork-Clone erbte `user.email` aus der globalen Konfiguration
  (`khaled.cherif@akara-solutions.de`, Akara-Konto). Vor dem Commit lokal auf
  `k.cherif@outlook.de` gesetzt (Konto-Trennungsregel). Der Signed-off-by-Trailer traegt jetzt
  die richtige Adresse.
- `ruff check` auf `ex_app/lib/main.py` im Fork meldet 42 Befunde. Alle sind vorbestehend und
  liegen ausserhalb der geaenderten Zeilen 40 bis 45 (geprueft). Nicht angefasst, Scope-Grenze.
- Ein Tool-Artefakt `.claude-active` liegt untracked im Fork-Clone. Nicht committet, nicht
  geloescht (kein `git clean` in fremden Arbeitskopien).

## Quality Gates

Unser Repo (vor dem Commit):

- `uv run ruff check .` - All checks passed
- `uv run ruff format --check .` - 79 files already formatted
- `uv run pyright` - 0 errors, 0 warnings
- `uv run pytest` - 443 passed, 45 deselected
- `uv run vulture src tests` - nur vorbestehende Fixture-Befunde in `tests/unit/`, unveraendert

Fork:

- `uv run --isolated --no-project python -m py_compile ex_app/lib/main.py` - Syntax OK
- `ruff check ex_app/lib/main.py` - keine Befunde auf den geaenderten Zeilen

## User Setup Required

None - keine externe Service-Konfiguration. Der offene Punkt ist der Owner-Schritt oben.

## Self-Check

- `docs/contrib/227-pr-body.md` existiert: FOUND
- `grep -c legacy_client_check docs/contrib/227-pr-body.md` = 3: PASS
- Em-Dash-Pruefung (U+2014 / U+2013) auf dem PR-Body: PASS
- Commit `f535859` in unserem Repo: FOUND
- Commit `def1425` im Fork, Signed-off-by vorhanden, kein Co-Authored-By: FOUND
- Branch `fix/stateless-http-session-compat` auf `street1983nk/context_agent`
  (sha def1425b89b375b090c452f6008511b198abb725): FOUND
- `git diff --stat` im Fork: 1 Datei, 4 Insertions, 1 Deletion: PASS
- Acceptance-Kriterium "PR eingereicht und URL dokumentiert": OFFEN (Owner-Schritt, bewusst)

## Self-Check: PASSED (mit offenem Owner-Schritt)

## Next Phase Readiness

- Der PR ist einreichfertig. Nach der Einreichung: PR-URL nachtragen, ROADMAP 01-13 abhaken,
  CONTRIB-01 auf Complete.
- Offen in Phase 1: Plan 01-11 und Plan 01-14.

---
*Phase: 01-server-kern*
*Completed: 2026-08-14 (Task 1; Checkpoint offen)*
