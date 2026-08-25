---
phase: 11-b-ndelung-budget-und-release-0-1-6
verified: 2026-08-25T03:49:18Z
status: passed
score: 7/7 must-haves verified
overrides_applied: 0
---

# Phase 11: Bündelung, Budget und Release 0.1.8 Verification Report

**Phase Goal:** Die neuen Familien kommen dort an, wo ein Assistent sie im Alltag trifft: im Ein-Aufruf-Bündel `prepare_context` und als auflösbarer Suchtreffer. Das Budget-Gate wird auf die neue Messung verankert statt einmalig angehoben, und die Fassung, die all das trägt, liegt im Store.
**Verified:** 2026-08-25T03:49:18Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `prepare_context` liefert einen Talk-Digest aus einem Request mit eigenem Budget und `degraded`-Eintrag (CTX-01) | ✓ VERIFIED | `src/mcp_connector/tools/context.py`: `TALK_BUDGET`, `MAX_DIGEST=3`, `DIGEST_PREVIEW_BYTES=200`, `asyncio.timeout(TALK_BUDGET)` (Zeile 305), degraded-Append Zeile 615. Integrationsmessung in `11-06-MEASUREMENTS.md` bestätigt 1 Request, Kappe 3, Vorschau-Byte-Kappe |
| 2 | `prepare_context` liefert Mail-Ungelesen-Zähler als reine Zahlen, nie aus dem Navigations-`unread` (CTX-02) | ✓ VERIFIED | `context.py`: `MAIL_BUDGET`, `MAX_MAIL_ACCOUNTS=3`, `asyncio.timeout(MAIL_BUDGET)` (Zeile 351), Zähler aus `mail_tools.browse` (Postfachliste), nicht aus Navigation. `11-06-MEASUREMENTS.md`: `inbox_unread` 6 gegen `mail_browse(level="mailboxes")` 6 gegengeprüft, 1+N-Requestkosten gemessen (1 Kontenliste + 1 Postfachliste) |
| 3 | Ein Talk- und ein Tables-Treffer aus Unified Search sind über `fetch` auflösbar statt `kind=url` (TOOL-16) | ✓ VERIFIED | `ids.py`: `encode_message`, `encode_table`, Token-/Ziffernwächter; `provider_map.py`: `talk-message`→`message`, `tables-search-tables`→`table`, `_tables_node` (View fällt bewusst auf `url` zurück), `_message_target`; `chatgpt.py`: `case "message"`/`case "table"` rufen `_fetch_message`/`_fetch_table`. Integrationsbeweis mit echten Suchtreffern `message:6c3pifti:17` und `table:2` in `11-06-MEASUREMENTS.md` |
| 4 | Das Budget-Gate ist auf die neue Messung verankert (17.500–18.000 Bytes), nicht einmalig angehoben (TOOL-15) | ✓ VERIFIED | `scripts/check_tool_budget.py`: `BUDGET_BYTES = 18_000`, Messzeile "2026-08-24 after the diet of plan 11-07". Live-Lauf bestätigt: `tools/list: 15657 bytes, 21 tools, budget 18000` (unter Gate, Diät wirksam) |
| 5 | Alle fünf neuen Werkzeuge sind schema-diätet, Annotationen ehrlich, Werkzeugzahl 21 in Registry und Contract-Tests | ✓ VERIFIED | `MAX_TOOL_BYTES = 1400`, größtes Werkzeug `mail_browse` 1376 Bytes; `tests/contract/test_tool_surface.py`: `EXPECTED_TOOLS` mit `len(tools) == 21`; `uv run pytest -q` grün (volle Suite) |
| 6 | Release 0.1.8 ist im Store, Version an allen vier Stellen, Tag nach Owner-Freigabe (EXAPP-07) | ✓ VERIFIED | `pyproject.toml`, `src/mcp_connector/__init__.py`, `appinfo/info.xml`, drei READMEs alle auf `0.1.8`; `CHANGELOG.md` mit `[0.1.8]`-Block und nachgetragener `[0.1.5]`-Sektion; Git-Tag `v0.1.8` existiert lokal; `docs/store-submission.md` dokumentiert Proof-Zeilen mit HTTP-201-Store-Annahme (2026-08-25 02:58Z) und grünem Release-Workflow (Run `32803041518`) |
| 7 | Review-Findings sind behandelt: 0 Critical/0 offene Warnings, Fix-Pass verifiziert | ✓ VERIFIED | `11-REVIEW.md`: WR-01 bis WR-04 als "fixed" mit Commits `e0150af`, `5ab83e6`, `33cae32`, `5501b0a` markiert; Fixes stichprobenartig im Code bestätigt (`context.py` `_mail`/`_counters` mit eigenen degraded-Sätzen für Postfach-/Kontenlisten-Kappung, Statuszeilen aller drei READMEs auf 0.1.8). IN-01 bis IN-07 sind als Info bewusst deferred (dokumentiert in `deferred-items.md` und Review-Frontmatter) |

**Score:** 7/7 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/mcp_connector/ids.py` | `encode_message`, `encode_table`, Token-/Ziffernwächter, `_HINT` mit acht Formen | ✓ VERIFIED | Vorhanden, `_TOKEN = re.compile(r"[a-z0-9]{4,30}")`, Wächter Zeile 139 |
| `src/mcp_connector/provider_map.py` | `PROVIDER_KINDS` erweitert, Fragment-Leser, zwei `extract_id`-Zweige | ✓ VERIFIED | `talk-message`, `talk-message-current`, `tables-search-tables` in `PROVIDER_KINDS`; `_message_target`, `_tables_node` vorhanden |
| `src/mcp_connector/nextcloud/clients/talk.py` | `get_message_context` auf v1-Chat-Route | ✓ VERIFIED | Zeile 196ff, hängt an `CHAT_PREFIX`, nutzt `ocs.ocs_get`/`ocs.parse_ocs` |
| `src/mcp_connector/tools/chatgpt.py` | `case message`/`case table`, `_fetch_message`, `_fetch_table` | ✓ VERIFIED | Zeilen 220–223, 587, 668 |
| `src/mcp_connector/tools/context.py` | Talk-Bein, Mail-Bein, `EXCERPT_KINDS`, reduzierte `resolvable`-Zeile | ✓ VERIFIED | Alle Konstanten und Funktionen vorhanden, Messzeilen verweisen auf existierende `11-06-MEASUREMENTS.md` |
| `.planning/phases/.../11-06-MEASUREMENTS.md` | Nachweistabelle mit Datum, Behauptung, Befehl | ✓ VERIFIED | Datei existiert (14500 Bytes), 19 Messzeilen mit Reproduktionsbefehlen gegen echte Container |
| `scripts/check_tool_budget.py` | Neue Messzeile, `BUDGET_BYTES` verankert | ✓ VERIFIED | `BUDGET_BYTES = 18_000`, Messzeile "2026-08-24 after the diet of plan 11-07" |
| `scripts/acceptance_all_tools.py` | Werkzeugliste aus `list_tools`, fetch für `message:`/`table:` | ✓ VERIFIED | `client.list_tools()` Zeile 140, `_message_to_fetch`/`_table_to_fetch` bauen Ids aus echten Suchtreffern |
| `src/mcp_connector/tools/mail.py` | `preview_truncated` eindeutig | ✓ VERIFIED | Zeile 509 `entry["preview_truncated"] = True`, getrennt von Antwort-Ebene `answer["truncated"]` |
| `pyproject.toml`, `__init__.py`, `appinfo/info.xml`, `CHANGELOG.md` | Version 0.1.8 überall | ✓ VERIFIED | Alle vier Stellen bestätigt identisch `0.1.8` |
| `docs/store-submission.md` | Proof-Zeilen Schritte 4–8 | ✓ VERIFIED | Proof-Tabelle mit Datum/Behauptung/Befehl bis 2026-08-25 03:01Z, inkl. HTTP 201 |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `provider_map.py` | `ids.py` | `extract_id` baut Ids über `encode_message`/`encode_table` | ✓ WIRED | Zeilen 144, 148 rufen `_message_target`/`_tables_node`, Rückgabe über `ids.encode_*` |
| `context.py` | `tools/talk.py`, `tools/mail.py` | Beine rufen `talk_tools.browse`/`mail_tools.browse` | ✓ WIRED | Bestätigt durch grep und bestandene Tests in `test_tools_context.py` |
| `context.py` | `asyncio.timeout` | Jedes Bein unter eigener Decke | ✓ WIRED | `asyncio.timeout(CALENDAR_BUDGET)`, `(TALK_BUDGET)`, `(MAIL_BUDGET)` je eigene Zeile |
| `chatgpt.py` | `nextcloud/clients/talk.py` | `get_message_context` liefert Fenster | ✓ WIRED | `_fetch_message` referenziert Route über Talk-Client |
| `appinfo/info.xml` | `src/mcp_connector/__init__.py` | Versionsabgleich | ✓ WIRED | Beide `0.1.8`, Contract-Test `test_exapp_env_setup.py` prüft laut Docstring die Übereinstimmung |
| `CHANGELOG.md` | Store-Beschreibung | Vokabular-Gate | ✓ WIRED | Keine verbotenen Begriffe in öffentlichen Artefakten (grep negativ) |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Budget-Gate hält 21 Werkzeuge unter 18000 Bytes | `uv run python scripts/check_tool_budget.py` | `tools/list: 15657 bytes, 21 tools, budget 18000` | ✓ PASS |
| Volle Testsuite grün | `uv run pytest -q` | alle Tests grün, keine Fehler | ✓ PASS |
| Lint/Format/Typen sauber | `uv run ruff check .`, `uv run ruff format --check .`, `uv run pyright` | "All checks passed!", "197 files already formatted", "0 errors, 0 warnings" | ✓ PASS |
| Toter Code | `uv run vulture src scripts vulture_whitelist.py` | keine Ausgabe (grün) | ✓ PASS |
| Debt-Marker (TBD/FIXME/XXX) in phasenrelevanten Dateien | grep über alle 19 in Plänen genannten Dateien | keine Treffer | ✓ PASS |
| Git-Tag v0.1.8 existiert lokal | `git tag \| grep 0.1.8` | `v0.1.8` | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| CTX-01 | 11-04, 11-06 | Talk-Digest aus einem Request im Bündel | ✓ SATISFIED | Talk-Bein in `context.py`, gemessen in `11-06-MEASUREMENTS.md` |
| CTX-02 | 11-05, 11-06 | Mail-Ungelesen-Zähler, nur Zahlen, 1+N gemessen | ✓ SATISFIED | Mail-Bein in `context.py`, Requestkosten gemessen und dokumentiert |
| TOOL-15 | 11-07, 11-08 | Budget-Gate auf neue Messung verankert, Werkzeuge diätet | ✓ SATISFIED | `BUDGET_BYTES=18000`, gemessen 15657 Bytes/21 Tools |
| TOOL-16 | 11-01, 11-02, 11-03, 11-08 | Talk/Tables-Suchtreffer auflösbar, Mail bleibt `url` | ✓ SATISFIED | `ids.py`/`provider_map.py`/`chatgpt.py` Ketten verifiziert |
| EXAPP-07 | 11-09, 11-10 | Release 0.1.8 im Store, Tag nach Freigabe | ✓ SATISFIED | Versionsabgleich, Tag, Store-HTTP-201-Proof |

Keine verwaisten (orphaned) Requirement-IDs: alle fünf Phase-11-IDs aus `REQUIREMENTS.md` (CTX-01, CTX-02, TOOL-15, TOOL-16, EXAPP-07) sind in den `requirements:`-Feldern der zehn Pläne vertreten.

### Anti-Patterns Found

Keine Blocker. Keine unreferenzierten `TBD`/`FIXME`/`XXX`-Marker in den phasenrelevanten Dateien gefunden.

Vier Warnungen aus dem Review (`11-REVIEW.md`, WR-01 bis WR-04) sind laut Review-Frontmatter und Commit-Historie (`e0150af`, `5ab83e6`, `33cae32`, `5501b0a`) gefixt; stichprobenartig im Code bestätigt (siehe Truth 7). Sieben Info-Befunde (IN-01 bis IN-07) sind bewusst als Tech-Debt zurückgestellt, dokumentiert in `11-REVIEW.md` und `deferred-items.md` (DF-11-01) — das ist eine explizite Scope-Entscheidung des Nutzers/Teams, kein unentdeckter Gap.

### Human Verification Required

Keine. Alle Wahrheiten sind über Code, Tests, gemessene Integrationsläufe (dokumentiert in `11-06-MEASUREMENTS.md`) und Store-Proof-Zeilen (HTTP-201, Release-Workflow-Run-Id, Tag-Existenz) programmatisch nachvollziehbar. Der irreversible Schritt (Tag, Push, Store-Submission) ist bereits mit Owner-Freigabe erfolgt und dokumentiert.

### Gaps Summary

Keine Gaps gefunden. Alle 7 abgeleiteten Wahrheiten sind verifiziert, alle 11 erwarteten Artefakte existieren, sind substantiell und verdrahtet, alle 5 Requirement-IDs sind abgedeckt, die volle Testsuite (2766+ Tests) sowie Ruff/Pyright/Vulture sind grün, und Release 0.1.8 ist nachweislich im Store mit HTTP 201 angenommen.

---

_Verified: 2026-08-25T03:49:18Z_
_Verifier: Claude (gsd-verifier)_
