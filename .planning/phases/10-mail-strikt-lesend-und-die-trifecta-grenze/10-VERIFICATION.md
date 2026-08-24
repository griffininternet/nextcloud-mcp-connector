---
phase: 10-mail-strikt-lesend-und-die-trifecta-grenze
verified: 2026-08-24T18:00:00Z
status: passed
score: 6/6 must-haves verified
overrides_applied: 0
---

# Phase 10: Mail strikt lesend und die Trifecta-Grenze Verification Report

**Phase Goal:** Nutzer kann seine Mail lesen, und zwar nur lesen: Konten, Postfächer, Envelopes, Volltext, Filter. Gleichzeitig verschwinden alle drei neuen Familien (Mail/Talk/Tables) sauber, wenn ihre App auf der Instanz fehlt, und die Exfiltrationskette Mail-Lesen plus Talk-Senden ist benannt statt beschwiegen.
**Verified:** 2026-08-24T18:00:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Nutzer kann Mail-Konten, Postfächer (`specialRole`, Ungelesen-Zähler) und Envelopes lesen (Vorschautext statt Body, Default 20, Max 50) | ✓ VERIFIED | `mail_browse` (`src/mcp_connector/tools/mail.py`) mit drei Ebenen; `DEFAULT_LIMIT=20`/`MAX_LIMIT=50`; live gegen GreenMail gemessen: 1 Konto, 1 Postfach (`special_role="inbox"`, `unread=6`), 6 Envelopes mit Vorschau (`tests/integration/test_mail_read.py`, 24/24 grün, live ausgeführt) |
| 2 | Volltext über bestehendes `fetch` mit `mail:<databaseId>`: HTML als Text, Byte-Kappe markiert, Vertrauens-Signale als Datenfelder | ✓ VERIFIED | `chatgpt._fetch_mail`, `MAX_MAIL_BYTES=32768`, `marks.FINAL_TRUNCATION`; live gemessen: ungekappter Newsletter 26684 B ohne HTML-Reste, gekappter Newsletter bei 32768 B mit Marker, `metadata` trägt `dkim`/`signature`/`sender_trusted` als Strings (live in `test_mail_read.py`) |
| 3 | Filtergrammatik (`is:unread`, `from:`, `subject:`, `start:`, `tags:`) dokumentiert wie getestet | ✓ VERIFIED | `FILTER_TYPES`/`FLAG_VALUES` in `tools/mail.py`; README (EN/DE/FR) trägt Grammatik-Tabelle; live gemessen: `is:unread`→6, `from:buchhaltung`→2, `subject:Rechnung`→2, `tags:1`→1, `is:ungelesen` und `start:2026-08-01` korrekt abgelehnt |
| 4 | Kein Weg zum Senden/Entwurf/Verschieben/Markieren/Löschen einer Mail; Gate mit Gegenprobe | ✓ VERIFIED | `tests/contract/test_no_destructive_calls.py`: 9 Mail-Nadeln (`/message/send`, `/api/messages`, `/api/mailboxes`, `/api/accounts`, `/api/drafts`, `/api/outbox`, `/api/thread`, `/api/tags`, `/api/trustedsenders`) je mit Gegenprobe, `ALLOWED_MAIL_ROUTES` als Positivliste, Nur-GET-Grep über beide Mail-Module; manueller Grep bestätigt: keine `ocs_post`/`.post(`/`.put(`/`.patch(`/`.delete(` in `clients/mail.py` oder `tools/mail.py` |
| 5 | Werkzeug gegen fehlende App antwortet in allen drei Familien mit Fehlersatz samt nächstem Schritt (Talk/Tables über Capabilities, Mail über zweiten Kanal, gecacht) | ✓ VERIFIED | `capabilities.load_mail` über `GET /core/navigation/apps`, dieselbe Cache-Zeile (`ALLOWED_MODULE_STATE` bleibt bei 2 Einträgen); live gemessen über drei Disable/Restart-Zyklen: `mail`, `spreed`, `tables` liefern nach Neustart je einen benannten Fehlersatz ohne Stacktrace/Loginseite (`tests/integration/test_srv06_degradation.py`, 11/11 grün, live ausgeführt, Topologie danach wiederhergestellt: alle drei Apps wieder aktiv) |
| 6 | Doku/Store-Beschreibung (EN/DE/FR) benennt Exfiltrationskette, Admin-Schalter als Gegenmaßnahme, Satz "Mail ist strikt lesend" | ✓ VERIFIED | `docs/privacy.md` Abschnitt "The chain that mail closes" (3 Zutaten, 5 Gegenmaßnahmen, ehrlicher Rest); README-Trifecta-Abschnitt in 3 Sprachen; `appinfo/info.xml` in EN/DE/FR mit "Mail is read only" / "Mail nur lesen" / "lecture seule", geprüft per Manifest-Marker-Test (`test_exapp_env_setup.py`) |

**Score:** 6/6 truths verified

### Code-Review-Fixes (10-REVIEW.md) — Nachprüfung im Code

| Finding | Review-Status | Nachprüfung |
|---------|---------------|-------------|
| CR-01 (kritisch): "genau ein Ausgangskanal" war falsch gegenüber geteilten Containern | fixed (6eb5d05) | ✓ Bestätigt: `docs/privacy.md`, `README.md`, `appinfo/info.xml` (EN/DE/FR) benutzen jetzt "one direct messaging channel" / "ein direkter Nachrichtenkanal" statt "the only way out"; Rest-Weg (geteilte Ordner/Boards/Tabellen) explizit benannt mit Handlungsempfehlung |
| WR-01: `get_message` ohne Mail-Server-Fehlerzweig | fixed (cd1f245) | ✓ Bestätigt: `_check_mail_server` wird jetzt in `get_mailboxes`, `get_messages` UND `get_message` aufgerufen (`clients/mail.py:144,186,214`) |
| WR-02: Cursor verloren bei deformiertem `dateInt` | fixed (3fda6ed) | ✓ Bestätigt: `oldest = min((stamp for item in raw if (stamp := _number(...)) > 0), default=0)` in `tools/mail.py:443-445` |
| WR-03: Postfach-Ebene ohne Fortsetzung bei >50 Einträgen | fixed (c149099) | ✓ Bestätigt: `_envelope` liefert jetzt ein `note`-Feld mit ehrlicher Grenzangabe (`tools/mail.py:565-580`) |
| WR-04: `isdigit()` akzeptiert Nicht-ASCII-Ziffern | fixed (4193856) | ✓ Bestätigt: `_DIGITS = re.compile(r"[0-9]+")` in `ids.py` und `clients/mail.py`; Testfälle mit `٤٢` und `²` vorhanden und grün |
| WR-05: README-Drift bei `fetch`-Id-Kinds | fixed (2c51cfc) | ✓ Bestätigt: alle drei READMEs nennen jetzt "the five id kinds" inkl. `mail:<databaseId>` |
| IN-01 bis IN-04 | deferred | Info-Level, nicht must-have-relevant (Feldnamen-Doppelbedeutung, Changelog-Lückenhygiene, veralteter Docstring-Kommentar, kosmetische SKIP-Meldung im Abnahmeskript) |

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/mcp_connector/nextcloud/clients/mail.py` | Vier lesende OCS-Pfadformen, kein Schreibpfad | ✓ VERIFIED | Existiert, 4 Leser, `_check_mail_server` in allen 3 relevanten Routen, kein `ocs_post`/`.post(`/etc. |
| `src/mcp_connector/tools/mail.py` | `mail_browse` mit 3 Ebenen, Filter-Positivliste | ✓ VERIFIED | Existiert, 571 Zeilen, Filter-Grammatik, honest limits, WR-02/WR-03 Fixes bestätigt |
| `src/mcp_connector/tools/html_text.py` | `to_text(html) -> str` | ✓ VERIFIED | Existiert, genutzt in `chatgpt._fetch_mail`, live Umlaut-Erhalt bestätigt |
| `src/mcp_connector/server/reg_mail.py` | Registrierung `mail_browse` | ✓ VERIFIED | Existiert, 21 Tools gesamt (`scripts/check_tool_budget.py`: 15736/18500 Bytes) |
| `docs/privacy.md`, `docs/faq.md`, drei READMEs, `appinfo/info.xml` | Exfiltrationskette benannt | ✓ VERIFIED | Alle vorhanden, Vokabular-Gate + Marker-Test grün |
| `tests/integration/test_mail_read.py` | Live-Nachweis Mail lesen ohne Nebenwirkung | ✓ VERIFIED | Live ausgeführt gegen laufende GreenMail-Topologie: 24/24 grün |
| `tests/integration/test_srv06_degradation.py` | Degradation aller drei Familien | ✓ VERIFIED | Live ausgeführt inkl. 3 Neustart-Zyklen: 11/11 grün, Topologie danach wiederhergestellt |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `tools/mail.py` (`mail_browse`) | `nextcloud/clients/mail.py` | `get_accounts`/`get_mailboxes`/`get_messages` | ✓ WIRED | Live bestätigt (echte Daten von GreenMail) |
| `tools/chatgpt.py` (`fetch`) | `nextcloud/clients/mail.py` (`get_message`) | `ids.parse("mail:...")` → `_fetch_mail` | ✓ WIRED | Live bestätigt, inkl. 206/500-Sonderfälle |
| `nextcloud/capabilities.py` (`require_app("mail")`) | `GET /core/navigation/apps` | `load_mail` in derselben Cache-Zeile | ✓ WIRED | Live bestätigt über Degradationslauf (Navigation liefert `False` nach Neustart ohne Mail-App) |
| `tests/contract/test_no_destructive_calls.py` | `clients/mail.py` + `tools/mail.py` | Nur-GET-Grep + 9 Nadeln mit Gegenprobe | ✓ WIRED | Grün, unabhängig gegengeprüft per manuellem Grep |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| MAIL-01 | 10-06, 10-07 | Konten/Postfächer/Envelopes lesen, kein Schreibpfad | ✓ SATISFIED | `mail_browse`, live bestätigt, Gate grün |
| MAIL-02 | 10-05 | Volltext über `fetch` mit `mail:<databaseId>` | ✓ SATISFIED | `_fetch_mail`, live bestätigt |
| MAIL-03 | 10-06, 10-07 | Filtergrammatik dokumentiert wie getestet | ✓ SATISFIED | `FILTER_TYPES`, README-Tabelle, live gemessen |
| SRV-06 | 10-08 | Alle drei Familien degradieren sauber | ✓ SATISFIED | Live 11/11 grün inkl. Neustarts |
| SEC-01 | 10-07 | Exfiltrationskette benannt, Admin-Schalter als Gegenmaßnahme | ✓ SATISFIED | `docs/privacy.md`, README, info.xml (EN/DE/FR), CR-01-Fix verifiziert |

Keine verwaisten Requirements: REQUIREMENTS.md listet für Phase 10 exakt MAIL-01, MAIL-02, MAIL-03, SRV-06, SEC-01, und alle fünf sind über die acht Pläne abgedeckt (MAIL-04 gehört zu Phase 8 und ist dort bereits erledigt).

### Anti-Patterns Found

Keine Debt-Marker (`TBD`/`FIXME`/`XXX`/`TODO`/`HACK`/`PLACEHOLDER`) in den von dieser Phase geänderten Produktionsdateien (`clients/mail.py`, `tools/mail.py`, `tools/html_text.py`, `tools/marks.py`, `tools/chatgpt.py`, `ids.py`, `server/reg_mail.py`, `capabilities.py`). Kein Schreibaufruf in den beiden Mail-Modulen (unabhängig gegengeprüft per Grep). Vulture sauber ohne neue Whitelist-Einträge.

### Behavioral Spot-Checks / Probe Execution

Kein separates Probe-Skript im Repo (`scripts/*/tests/probe-*.sh` existiert nicht für dieses Projekt). Stattdessen wurden die dokumentierten Integrationstests der Phase live gegen die laufende Docker-Topologie (GreenMail + Nextcloud 34.0.3 + Mail 5.11.1) ausgeführt, nicht nur die SUMMARY-Behauptungen übernommen:

| Prüfung | Kommando | Ergebnis | Status |
|---------|----------|----------|--------|
| Mail lesen ohne Nebenwirkung | `pytest tests/integration/test_mail_read.py -m integration` | 24 passed | ✓ PASS |
| Degradation aller drei Familien | `pytest tests/integration/test_srv06_degradation.py -m integration` | 11 passed | ✓ PASS |
| Volle Unit/Contract-Suite | `pytest -q` | grün (kein Fail) | ✓ PASS |
| `ruff check .` / `ruff format --check .` | — | grün | ✓ PASS |
| `pyright` | — | 0 errors, 0 warnings | ✓ PASS |
| `vulture src/mcp_connector vulture_whitelist.py` | — | grün, ohne neue Einträge | ✓ PASS |
| `scripts/check_tool_budget.py` | — | 21 Tools, 15736/18500 Bytes | ✓ PASS |
| Topologie-Zustand nach Live-Läufen | `occ app:list` | `mail`, `spreed`, `tables` aktiviert | ✓ PASS |

### Human Verification Required

Keine. UI-Hint der Phase ist "nein" (kein eigenes Frontend), es gibt keine `<human-check>`-Blöcke in den Plänen, und alle Aussagen sind entweder per Unit-/Contract-Test oder per live ausgeführtem Integrationstest gegen die echte Topologie belegt.

### Gaps Summary

Keine Gaps. Alle sechs Roadmap-Erfolgskriterien sind mit Codebeleg und, wo sinnvoll, mit live ausgeführten Integrationstests verifiziert. Die Review-Fixes aus 10-REVIEW.md (CR-01 kritisch, WR-01 bis WR-05) sind im Code nachgeprüft und nicht nur laut SUMMARY behauptet. Die vier deferred Info-Findings (IN-01 bis IN-04) sind kosmetisch/dokumentarisch und nicht must-have-relevant für den Phasenzweck.

---

_Verified: 2026-08-24T18:00:00Z_
_Verifier: Claude (gsd-verifier)_
