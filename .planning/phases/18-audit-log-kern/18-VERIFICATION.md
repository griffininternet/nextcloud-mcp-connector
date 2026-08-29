---
phase: 18-audit-log-kern
verified: 2026-08-29T00:00:00Z
status: passed
score: 5/5 must-haves verified
overrides_applied: 0
---

# Phase 18: Audit-Log Kern Verification Report

**Phase Goal:** Jeder Werkzeugaufruf hinterlässt einen prüfbaren Eintrag, der weder Parameterwerte noch Ergebnisinhalte trägt und den OAuth-Speicher nicht schreibunfähig machen kann
**Verified:** 2026-08-29
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (Roadmap-Erfolgskriterien)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Nach einem Werkzeugaufruf steht ein Eintrag mit Nutzer, Werkzeugname, Zeitpunkt, aufrufendem Client und Ergebnisstatus; ein abgelehnter Aufruf mit seinem Grund; kein Werkzeug kommt an der Erfassung vorbei | ✓ VERIFIED | `graceful` in `src/mcp_connector/server/__init__.py:75-138` setzt `outcome`/`reason` in vier Zweigen und schreibt im `finally` über `record.note(...)`; Marker `__mcp_audited__` gesetzt (Zeile 138). `tests/contract/test_audit_surface.py::test_every_registered_tool_carries_the_recording_marker` und `::test_the_two_ways_to_the_tool_name_cannot_drift_apart` grün (32 Fälle in `test_audit_surface.py`+`test_tool_surface.py` zusammen, lokal ausgeführt). Recorder wird nur produktiv gebaut, wenn `config.audit_log_enabled(env)` wahr ist (`entry_exapp.py:109-158`) |
| 2 | Kein Parameterwert und kein Ergebnisinhalt in irgendeinem Eintrag; Erlaubnisliste je Werkzeug; Vertragstest nach dem Muster des Budget-Gates schlägt bei Überschreitung fehl | ✓ VERIFIED | `src/mcp_connector/audit/allowlist.py`: `PARAM_ALLOWLIST` hat genau 21 Einträge (per Skript geprüft, keine leere Menge), `FORBIDDEN_PARAMS` nennt 7 Nutzlastnamen (`content, description, location, message, summary, title, values`). Schema-Spalte `params` trägt nur eine sortierte JSON-Namensliste (`store.py:244`). `set_parameter_names` liest ausschliesslich `params["arguments"].keys()` (`record.py`), `grep -c ".values()"` in `record.py` = 0 (Falle 1 vermieden). Vier Gate-Fälle in `test_audit_surface.py` laufen grün |
| 3 | Prüfkommando bestätigt ungebrochene Hash-Kette oder benennt erste gebrochene Stelle; nachträglich veränderte Zeile wird gefunden | ✓ VERIFIED | `AuditStore.verify_chains` (`store.py:909`) trennt `FINDING_MODIFIED`/`FINDING_MISSING` je Kette. occ-Kommando `mcp_connector:audit:verify` registriert (`exapp/occ.py`, `OCC_AUDIT_COMMAND_NAME`), Handler in `exapp/audit_verify.py` antwortet immer mit 200 und benennt Kette+Nummer im Text sowie `broken` im JSON. Kein neuer `<url>`-Eintrag im Manifest (`grep -c "<url>" appinfo/info.xml` = 14 vor und nach der Phase; nur Kommentarzeilen erwähnen `/audit-verify`). Tests `test_exapp_audit_verify.py` (32 Fälle) grün, drei Manipulationsfälle je mit eigener sqlite3-Verbindung an der Ablage vorbei |
| 4 | Eigene Ablage neben OAuth-Speicher, Obergrenze, Aufbewahrungsfrist ≥180 Tage; bei vollem Volume bleiben Token-Rotation und neue Verbindungen funktionsfähig | ✓ VERIFIED | `AUDIT_FILENAME = "audit.sqlite3"` neben `STORE_FILENAME = "oauth.sqlite3"`, eigene Verbindung/eigenes WAL (`store.py:84`). `RETENTION_DAYS = 180`, `SIZE_LIMIT_BYTES = 100_000_000`, beide über `NC_MCP_AUDIT_RETENTION_DAYS`/`NC_MCP_AUDIT_MAX_BYTES` einstellbar (`config.py:52-54, 384-430`, per Python-Aufruf bestätigt: `False True 180 100000000`). Test `test_the_oauth_store_still_rotates_and_connects_after_the_bound_bit` (in `test_audit_store.py`) grün — belegt, dass ein volles Audit-Volume den OAuth-Speicher nicht schreibunfähig macht |
| 5 | `occ mcp_connector:purge`, Oberfläche, Trennen, Pausieren lassen das Log stehen (D-18: mit Ausnahme `--rm-data`); Löschung sonst nur durch Frist oder Nutzerlöschung (D-12) | ✓ VERIFIED (5a getestet, 5b hergeleitet gemäss D-18/T-18-25) | 5a: vier Fälle in `tests/unit/test_exapp_purge.py` (`test_the_purge_leaves_every_row_of_the_audit_log_where_it_is`, `::test_the_chains_of_the_audit_log_are_unbroken_after_the_purge`, `::test_the_purge_empties_every_oauth_table_and_keeps_the_audit_rows`, `::test_the_audit_log_is_still_readable_after_the_data_key_was_deleted`) grün; `git diff --stat 9d9be78 HEAD -- src/mcp_connector/exapp/purge.py` leer (Handler unverändert). 5b: `grep -rniE "audit|AUDIT_FILENAME|audit\.sqlite3" oauth/connections.py exapp/purge.py exapp/lifecycle.py` trifft nur eine harmlose Log-Textzeile, keine der drei Dateien importiert das Audit-Modul — das ist laut Aufgabenstellung ausdrücklich als "bewusst hergeleitet, nicht getestet" akzeptiert (D-18, T-18-25 `accept`) und keine neue Lücke dieser Verifikation. Nutzerlöschung nach D-12: `drop_user_chain` + Grabstein, `existing_users` fail-safe (gibt `None` bei jeder Unsicherheit zurück, löscht dann nichts) — Code verifiziert in `audit/accounts.py` und `audit/store.py` |

**Score:** 5/5 Erfolgskriterien verifiziert (Kriterium 5 mit der im Auftrag selbst dokumentierten, bewusst nicht getesteten Teilaussage 5b)

### Requirements Coverage

| Requirement | Beschreibung | Status | Evidence |
|---|---|---|---|
| AUDIT-01 | Eintrag je Aufruf, Erlaubnisliste, Vertragstest | ✓ SATISFIED | `REQUIREMENTS.md:35` `[x]` + Tabelle `Complete`; Recorder produktiv verdrahtet in `entry_exapp.py` hinter Schalter |
| AUDIT-02 | Hash-Kette + Prüfkommando | ✓ SATISFIED | `REQUIREMENTS.md:36` `[x]` + `Complete`; `verify_chains` + `occ mcp_connector:audit:verify` |
| AUDIT-03 | Eigene Ablage, Obergrenze, Frist ≥180 Tage, OAuth-Speicher bleibt schreibfähig | ✓ SATISFIED | `REQUIREMENTS.md:37` `[x]` + `Complete`; siehe Kriterium 4 oben |
| AUDIT-04/05/06 | Phase 19 | korrekt als Pending/Phase 19 zugeordnet, keine verwaisten Requirements dieser Phase | `REQUIREMENTS.md:38-40, 89-91` |

Keine verwaisten Requirements: alle drei Plan-deklarierten IDs (AUDIT-01/02/03) sind mit den zehn Plänen dieser Phase erklärt und in `REQUIREMENTS.md` konsistent auf `Complete` gesetzt.

### Required Artifacts

| Artifact | Erwartet | Status | Details |
|---|---|---|---|
| `src/mcp_connector/audit/store.py` | Schema, Pragmas, Kette, Prüfung, Sweep | ✓ VERIFIED | 19 Spalten bestätigt, `BEGIN IMMEDIATE` in `append`/`sweep`/`drop_user_chain`, `verify_chains`, `overview`, `size` vorhanden und getestet |
| `src/mcp_connector/audit/__init__.py` | `audit_opener`, `AUDIT_STATE_ATTR` | ✓ VERIFIED | Closure ohne Modulzustand, importierbar |
| `src/mcp_connector/audit/allowlist.py` | `PARAM_ALLOWLIST` (21), `FORBIDDEN_PARAMS` (7) | ✓ VERIFIED | Per Skript nachgezählt: 21 Einträge, keine leere Menge, 7 Sperrnamen |
| `src/mcp_connector/audit/record.py` | `Recorder`, `note`, `note_switch`, `set_parameter_names` | ✓ VERIFIED | Nur `.keys()` gelesen, kein `.values()`; fail-open mit `except Exception` |
| `src/mcp_connector/audit/accounts.py` | `existing_users`, fail-safe | ✓ VERIFIED | Fünf Antwortformen, vier davon `None` |
| `src/mcp_connector/errors.py` | `ToolError.reason`, `REASONS` | ✓ VERIFIED | Sechs `REASON_*`-Konstanten, `REASONS`-Frozenset bestätigt |
| `src/mcp_connector/server/__init__.py` | `graceful` mit Marker + finally | ✓ VERIFIED | `__mcp_audited__` gesetzt, `finally: await record.note(...)` |
| `src/mcp_connector/exapp/audit_verify.py` | occ-Handler, kein Manifest-Route | ✓ VERIFIED | `AUDIT_VERIFY_PATH`, keine `<url>` im Manifest |
| `src/mcp_connector/config.py` | drei Audit-Env-Werte | ✓ VERIFIED | `audit_log_enabled/-retention_days/-size_limit`, Vorgaben `False/180/100000000` |
| `appinfo/info.xml` | keine neue Route | ✓ VERIFIED | `<url>`-Zählung unverändert bei 14 (13 echte Routen + 1 Kommentarerwähnung) |

### Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| `server/__init__.py::graceful` | `audit/record.py::note` | `await record.note(ctx, ...)` im `finally` | WIRED | Bestätigt im Quelltext, Contract-Test grün |
| `entry_exapp.py::build_exapp_app` | `audit/record.py::Recorder` | nur hinter `config.audit_log_enabled(env)` gebaut | WIRED | Recorder-Konstruktion an Zeile ~128, `audit_recorder=recorder` an `RequireAppApi` |
| `exapp/middleware.py::RequireAppApi` | `AUDIT_STATE_ATTR` | Ablage in `request.state` nach dritter Prüfung, auch AppAPI-Weg | WIRED | Bestätigt in `middleware.py`, `deps.resolve_caller` liest denselben Namen |
| `exapp/occ.py` | `exapp/audit_verify.py` | `OCC_AUDIT_COMMAND_NAME`, Registrierungsschleife | WIRED | Zwei Kommandos, ein `try` je Kommando |
| `audit/record.py` | `audit/accounts.py` | `_drop_chains_without_an_account` hinter `should_check_accounts` | WIRED | Aufruf im Aufräumzweig von `note` bestätigt |
| `exapp/purge.py` | `audit/store.py` | keine Verbindung (gewollt) | UNCHANGED (by design) | `git diff --stat` über die Phase leer; vier Tests belegen Überleben |

### Behavioral Spot-Checks / Gate-Läufe (lokal ausgeführt, nicht nur aus SUMMARY übernommen)

| Prüfung | Kommando | Ergebnis | Status |
|---|---|---|---|
| Lint | `uv run --no-sync ruff check .` | `All checks passed!` | ✓ PASS |
| Format | `uv run --no-sync ruff format --check .` | `216 files already formatted` | ✓ PASS |
| Typen | `uv run --no-sync pyright` | `0 errors, 0 warnings, 0 informations` | ✓ PASS |
| Dead Code | `uv run --no-sync vulture src scripts vulture_whitelist.py` | kein Befund, Exit 0 | ✓ PASS |
| Unit+Contract | `uv run --no-sync pytest tests/unit tests/contract -q` | Exit 0, alle Punkte grün (~2900 Fälle) | ✓ PASS |
| Matrix | `uv run --no-sync pytest -m matrix -q` | 8 passed | ✓ PASS |
| Budget | `uv run --no-sync python scripts/check_tool_budget.py` | `tools/list: 15712 bytes, 21 tools, budget 18000` — unverändert | ✓ PASS |
| Audit-spezifische Suiten | `pytest tests/unit/test_audit_store.py tests/unit/test_audit_record.py tests/unit/test_audit_caller.py tests/unit/test_audit_accounts.py tests/unit/test_errors_reason.py tests/unit/test_exapp_audit_verify.py tests/unit/test_exapp_purge.py -q` | alle grün | ✓ PASS |
| Kein Debt-Marker | `grep -nE "TBD\|FIXME\|XXX\|TODO\|HACK\|PLACEHOLDER"` über alle in dieser Phase geänderten Dateien | nur zwei False Positives (`_PLACEHOLDER`/`_PLACEHOLDERS` als Bezeichnernamen, kein Debt-Marker) | ✓ PASS |
| Verbotene Wörter | `grep -rniE "revisionssicher\|AI-Act\|DSGVO-konform\|SIEM-zertifiziert"` über alle geänderten Dateien | kein Treffer | ✓ PASS |
| Unveränderte Randbereiche | `git diff --stat 9d9be78 HEAD -- purge.py, check_tool_budget.py, test_tool_surface.py, privacy.md, uninstall.md, pyproject.toml, uv.lock` | leer | ✓ PASS |

### Anti-Patterns Found

Keine Blocker. Keine unreferenzierten TBD/FIXME/XXX. Keine verbotenen Begriffe. Keine leeren Stub-Implementierungen gefunden; alle als "geparkt" markierten Namen in `vulture_whitelist.py` sind mit nachvollziehbarem Ausstiegsplan versehen und wurden planmäßig über die zehn Pläne hinweg abgebaut (bestätigt per Diff der Datei).

### Human Verification Required

Keine. Diese Phase liefert reinen Server-/Backend-Code (SQLite-Ablage, Dekorator, occ-Kommando, Konfigurationsschalter) ohne visuelle Oberfläche; die einzige UI-Änderung ist ein kurzes Checkbox-Label, dessen Text und Reihenfolge bereits durch `test_exapp_admin_settings.py` (Feldreihenfolge, Typ, `default: False`, kein `sensitive`) programmatisch gehalten werden. Die ausführliche Beschriftung mit Mitbestimmungshinweis ist AUDIT-05 und explizit Phase 19.

### Gaps Summary

Keine Lücken gefunden, die den Phasenzielen entgegenstehen. Der einzige nicht getestete Teil (5b: Verhalten bei Oberflächen-Entfernen/Trennen/Pausieren) ist im Auftrag selbst als bewusst hergeleitet statt getestet deklariert (D-18, T-18-25 `accept`) und wird hier entsprechend nicht als Gap gewertet, sondern als dokumentierte, akzeptierte Einschränkung bestätigt: Die Herleitung (grep über die drei relevanten Dateien, keine trifft das Audit-Modul) wurde in dieser Verifikation unabhängig nachvollzogen und bestätigt.

---

_Verified: 2026-08-29_
_Verifier: Claude (gsd-verifier)_
