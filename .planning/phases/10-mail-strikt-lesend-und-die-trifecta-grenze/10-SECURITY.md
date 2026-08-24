---
phase: 10-mail-strikt-lesend-und-die-trifecta-grenze
slug: mail-strikt-lesend-und-die-trifecta-grenze
status: verified
threats_open: 0
asvs_level: 1
created: 2026-08-24
updated: 2026-08-24
---

# Phase 10 , Security

> Sicherheitsvertrag dieser Phase: Bedrohungsregister, akzeptierte Risiken, Prüfprotokoll.
> Geprüfter Stand: HEAD nach `6f3b25e` (also nach dem Review-Fix-Pass `6eb5d05..3093d9a`),
> plus der T-10-01-Schlusstest aus diesem Audit-Lauf.
> Grundhaltung dieser Prüfung: jede Minderung gilt als abwesend, bis eine Fundstelle im
> Implementierungsstand sie belegt. Doku und Absicht allein sind kein Beweis.
> Register aufgebaut aus den acht `<threat_model>`-Blöcken von `10-01-PLAN.md` bis
> `10-08-PLAN.md` (register_authored_at_plan_time: true).
> Gate-Lauf des Audits: `uv run pytest tests/contract tests/unit/test_mail_{client,tools}.py
> tests/unit/test_{html_text,truncation_marks,chatgpt_fetch,ids,exapp_env_setup,ocs_capabilities}.py`
> = 457 passed (vor dem T-10-01-Schlusstest; danach 148/148 in test_exapp_env_setup.py).

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Modelleingabe zu URL-Pfad | Konto-, Postfach- und Nachrichten-Ids aus Modellantworten werden Pfadsegmente der vier Mail-Leserouten | Pfadsegmente, Query-Parameter (Ziffernwächter `[0-9]+`) |
| Fremder Mail-Inhalt zu Modellkontext | Jeder Absender der Welt kann Text schreiben, den `mail_browse`/`fetch mail:` in den Modellkontext legt | Betreff, Vorschau, Body (HTML zu Text), Absendername |
| Mail-App zu Vertrauensurteil | Nextclouds Signale (DKIM, Phishing, Absender vertraut) werden als Daten durchgereicht, nie als eigenes Urteil | dkim/signature/phishing/sender_trusted in metadata |
| Mail lesen zu Ausgangskanälen | Die Trifecta: gelesener Fremdinhalt plus talk_send (direkter Kanal) bzw. geteilte Container (Restweg) | Nachrichtentexte, Datei-/Karten-/Zeileninhalte |
| GreenMail zu Compose-Netz | Der Mess-Mailserver läuft ohne Authentifizierung; seine Reichweite endet am Compose-Netz | IMAP/SMTP der Testtopologie (kein ports-Block, per Test behauptet) |
| Manifest/Doku zu Store-Leser | Die Sicherheitsaussagen (strikt lesend, Kanal-Formulierung) in EN/DE/FR, per Marker-Test gehalten | Store-Beschreibung, READMEs, privacy/faq |

---

## Threat Register

Alle 56 Threats CLOSED. Belege (Datei:Zeile bzw. Test) aus dem Audit-Lauf 2026-08-24:

| Threat ID | Category | Component | Disposition | Mitigation / Evidence | Status |
|-----------|----------|-----------|-------------|-----------------------|--------|
| T-10-01 | Information Disclosure | GreenMail ohne Auth | mitigate | Kein ports-Block (`compose.exapp.yml:124-152`); dienstspezifischer Test `test_the_mail_server_publishes_no_port` (tests/unit/test_exapp_env_setup.py, in diesem Audit ergänzt) | closed |
| T-10-02 | Information Disclosure | Messprotokoll spike-mail.md | mitigate | Nur Variablennamen, keine Werte (`docs/spike-mail.md:94-95`, `:206`); alle Adressen example.test | closed |
| T-10-03 | Spoofing | Existenzprüfung Mail-Konto | mitigate | `scripts/bootstrap_exapp.sh:344-368` vergleicht Adresse UND host:port | closed |
| T-10-04 | Tampering | Wegwerf-Container SMTP | accept | `docker run --rm -i --network`, gepinnt `python:3.13-alpine`, kein Volume/Port (`bootstrap_exapp.sh:435-438`) | closed |
| T-10-05 | Denial of Service | 400-KB-Testmail | accept | Topologie ohne veröffentlichten Port (`bootstrap_exapp.sh:588`) | closed |
| T-10-06 | Spoofing | `_path_id` | mitigate | `clients/mail.py:221-234` `_DIGITS.fullmatch`, alle drei Eintritte; Tests mit 0 Requests inkl. `"٤٢"`/`"²"` | closed |
| T-10-07 | Elevation of Privilege | Pfadformen des Clients | mitigate | Vier GET-Konstanten `clients/mail.py:71-86`, nur `ocs.ocs_get`; 16-Nadeln-Quelltext-Test | closed |
| T-10-08 | Information Disclosure | 404 fremder Nachrichten-Id | mitigate | `clients/ocs.py:177-178` liest meta.message, nie ocs.data | closed |
| T-10-09 | Denial of Service | Fenster ohne Grenze | mitigate | `clients/mail.py:174` min/max-Kappe, MAX_MESSAGES=50 | closed |
| T-10-10 | Tampering | Deformierte Navigationsantwort | mitigate | `capabilities.py:234-241` ToolError mit Ausweg, nie "Mail fehlt" | closed |
| T-10-11 | Information Disclosure | Cache-Inhalt Erkennungsweg | mitigate | `capabilities.py:128/150-151/191-194`, Original-Zeitstempel bleibt | closed |
| T-10-12 | Tampering | `_OK_STATUS`-Erweiterung um 206 | accept | 206 lokal in `clients/mail.py:103/215/255`, globales frozenset unverändert | closed |
| T-10-13 | Tampering | XXE über DOCTYPE | mitigate | `html_text.py:100` `no_network=True`; Test gegen Datei-Exfiltration | closed |
| T-10-14 | Denial of Service | Entity-Expansion | mitigate | Test gegen Entity-Bombe (`len(text) < 200`) | closed |
| T-10-15 | Denial of Service | Parserfehler Volltextpfad | mitigate | `html_text.py:88-103` except -> "" | closed |
| T-10-16 | Spoofing | Gefälschte Kappungsmarkierung | mitigate | Dritter Marker in `_PATTERNS` (`marks.py:64`); Tests inkl. mehrfaches Vorkommen | closed |
| T-10-17 | Spoofing | Skript-/Stilinhalt als Prosa | mitigate | `_DROPPED_TAGS` + drop_tree (`html_text.py:42/109-110`) | closed |
| T-10-18 | Information Disclosure | Marker schickt ins Leere | mitigate | FINAL_TRUNCATION nennt kein Werkzeug (`marks.py:52`) | closed |
| T-10-19 | Tampering | Filter mit unbekanntem Typ | mitigate | Positivliste + `_checked_filter` VOR require_app (`tools/mail.py:119/202/222-278`); Tests mit 0 Requests | closed |
| T-10-20 | Information Disclosure | `body:` als Filter | mitigate | body fehlt in FILTER_TYPES, Begründung `tools/mail.py:104-107` | closed |
| T-10-21 | Spoofing | Marker in Betreff/Vorschau/Absender | mitigate | `_text -> marks.without_marks` auf allen Textfeldern (`tools/mail.py:551-559`) | closed |
| T-10-22 | Elevation of Privilege | Cursor-Handle fremdes Postfach | mitigate | `paging.check_scope` vor dem ersten Request (`tools/mail.py:416`); Test 0 Requests | closed |
| T-10-23 | Denial of Service | Kontextflut | mitigate | Limit-Kappe, MAX_PREVIEW_BYTES=400, kein Body auf Listenebene | closed |
| T-10-24 | Information Disclosure | Geratenes Konto | mitigate | Kein account_id-Default, Ablehnung mit `_ACCOUNT_HINT` (`tools/mail.py:163/211-213`) | closed |
| T-10-25 | Information Disclosure | `id` vs `databaseId` | mitigate | Nur databaseId projiziert (`tools/mail.py:346`) | closed |
| T-10-26 | Repudiation | Nachricht an Seitengrenze | accept | Docstring + README "Known limitations" | closed |
| T-10-27 | Spoofing | `summary` der App | mitigate | summary nie projiziert; Test | closed |
| T-10-28 | Spoofing | Signal-Wäsche "DKIM: valid" | mitigate | Signale nur in metadata, text = Body (`chatgpt.py:409-418`); Test | closed |
| T-10-29 | Spoofing | Gefälschte Marke im Mailinhalt | mitigate | without_marks VOR der Kappe (`chatgpt.py:387/399-407`); count==1-Test | closed |
| T-10-30 | Tampering | SSRF über unsubscribe/raw/downloadUrl | mitigate | Feldnamen kommen in src/ nicht vor; url aus creds.base_url; Test | closed |
| T-10-31 | Spoofing | Nicht numerische Nachrichten-Id | mitigate | `_DIGITS.fullmatch` in ids.parse + Client-Wächter | closed |
| T-10-32 | Denial of Service | Sehr grosse Mail | mitigate | MAX_MAIL_BYTES=32 KiB mit Messbegründung, markierte Kappung | closed |
| T-10-33 | Denial of Service | Loop über Volltextroute | mitigate | Genau ein get_message; call_count==1-Test | closed |
| T-10-34 | Information Disclosure | Leerer Erfolg bei 206/leerem Body | mitigate | Je ToolError mit nächstem Schritt (`chatgpt.py:370-395`) | closed |
| T-10-35 | Tampering | Verschachteltes metadata | mitigate | Flache dict[str,str]-Projektion + `_phishing_checks` (`chatgpt.py:422-518`) | closed |
| T-10-36 | Information Disclosure | Fehlendes dkimValid als "ungültig" | mitigate | `_dkim`/`_signature` -> "unchecked" bei fehlendem Wert | closed |
| T-10-37 | Elevation of Privilege | POST /message/send künftig | mitigate | Nadel + Gegenprobe in test_no_destructive_calls.py | closed |
| T-10-38 | Elevation of Privilege | Rückfall auf /api/-Resource-Routen | mitigate | 8 Nadeln + 8 Gegenproben + Vollständigkeitstest + ALLOWED_MAIL_ROUTES | closed |
| T-10-39 | Tampering | Schreibaufruf ohne Nadel | mitigate | MAIL_MODULES + WRITING_CALLS über den Rohquelltext beider Mail-Module | closed |
| T-10-40 | Denial of Service | Kontextkosten Werkzeugoberfläche | mitigate | Datierte Messzeile 15736 B, BUDGET_BYTES=18500 als Zwischenstand, MAX_TOOL_BYTES=1400 gehalten | closed |
| T-10-41 | Repudiation | Zahlen an mehreren Orten | mitigate | 21 konsistent in Budget-Skript, Contract-Test, Abnahmeskript, drei READMEs | closed |
| T-10-42 | Spoofing | Credential-abhängige tools/list | accept | Bedingungslose Listung begründet (`reg_mail.py:7-10`) | closed |
| T-10-43 | Information Disclosure | Lethal Trifecta (Mail lesen + Senden) | mitigate | Nach CR-01-Fix ehrlich: talk_send = einziger DIREKTER Nachrichtenkanal, Restweg geteilte Container benannt; privacy/faq/3 READMEs/Store EN/DE/FR | closed |
| T-10-44 | Repudiation | Sicherheitsaussage ohne Halter | mitigate | privacy.md trennt Fähigkeitsaussage vom prüfbaren Versprechen (Contract-Test als Halter) | closed |
| T-10-45 | Tampering | Store-Text verliert die Sätze | mitigate | Marker-Tripel read only/nur lesen/lecture seule + Postfachnamen-Test | closed |
| T-10-46 | Repudiation | Verbotenes Vokabular | mitigate | FORBIDDEN_VOCABULARY-Gate case-insensitiv über den Manifest-Text + Gegenprobe | closed |
| T-10-47 | Tampering | Versehentliche Versionsanhebung | mitigate | `<version>0.1.7` unangetastet (git show über beide Manifest-Commits) | closed |
| T-10-48 | Information Disclosure | Grenze als Fehler erlebt | mitigate | Vier Mail-Zeilen in den Known limitations mit What you see / What to do | closed |
| T-10-49 | Elevation of Privilege | Zugriff auf fremdes Postfach | mitigate | Zwei-Konten-Beweis live (bob an alices Ids abgewiesen, Hint-Negativproben) | closed |
| T-10-50 | Information Disclosure | Fehlermeldung bestätigt fremde Nachricht | mitigate | subject/preview nicht in der Ablehnung; zurückgegebene Id ist die des Aufrufers | closed |
| T-10-51 | Information Disclosure | Stacktrace/Loginseite als Antwort | mitigate | Integrationstests gegen Traceback/HTML/Login in beiden Suiten | closed |
| T-10-52 | Repudiation | Grüner Degradationstest ohne Beleg | mitigate | disable -> restart -> clear_cache je Familie, restarted-Assertion | closed |
| T-10-53 | Denial of Service | Halb abgeschaltete Instanz | mitigate | finally: enable + restart + Abschlusstest über occ app:list | closed |
| T-10-54 | Information Disclosure | APP_SECRET in einer Ausgabe | mitigate | secret/AUTHORIZATION-Header/greenmail/imap/password-Negativproben | closed |
| T-10-55 | Tampering | Seen-Zustand durch Lesen verändert | mitigate | seen_state vor/nach fetch gemessen (false/false, unread 6/6) | closed |
| T-10-SC (8x) | Tampering | Paketinstallation | mitigate | Kein Commit der Phase an pyproject/uv.lock; Images gepinnt; lxml_html_clean nicht installiert | closed |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-10-1 | T-10-04 | SMTP-Einlieferung läuft im Wegwerf-Container (--rm, kein Volume, kein Port, gepinntes Image) innerhalb der Messtopologie | Audit-Lauf (Plan-Disposition) | 2026-08-24 |
| AR-10-2 | T-10-05 | Die 400-KB-Testmail lebt nur in der Topologie ohne veröffentlichten Port; sie ist das Messobjekt der Kappe | Audit-Lauf (Plan-Disposition) | 2026-08-24 |
| AR-10-3 | T-10-12 | HTTP 206 wird lokal im Mail-Client behandelt statt global in `_OK_STATUS`; die globale Liste bleibt eng | Audit-Lauf (Plan-Disposition) | 2026-08-24 |
| AR-10-4 | T-10-26 | Zwei Mails in derselben Sekunde können an der Seitengrenze eine Nachricht auslassen; dokumentiert in Docstring und README Known limitations | Audit-Lauf (Plan-Disposition) | 2026-08-24 |
| AR-10-5 | T-10-42 | tools/list listet bedingungslos (auch ohne Mail-Konto); der Aufruf selbst degradiert ehrlich | Audit-Lauf (Plan-Disposition) | 2026-08-24 |

*Accepted risks do not resurface in future audit runs.*

---

## Unregistered Flags (WARNING, geprüft, kein Befund)

1. Sechs von acht SUMMARYs tragen keinen `## Threat Flags`-Abschnitt (nur 10-04 und
   10-07). Die fünf betroffenen Pläne wurden einzeln gegen das Register geprüft:
   keine ungemappte Fläche gefunden. Prozesshinweis für kommende Phasen.
2. Neue Fläche aus dem Review-Fix-Pass (nicht im Plan-Register, geprüft, vereinbar
   mit T-10-23/T-10-48): `_check_mail_server` auf der Volltextroute (WR-01) und die
   `note` der cursorlosen Ebenen (WR-03).
3. `capabilities.load_mail` fügt einen zweiten HTTP-Request pro Cache-Fenster hinzu;
   durch T-10-10/T-10-11 abgedeckt, als eigener DoS-Posten nicht geführt.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-08-24 | 56 | 55 | 1 (T-10-01, Testhälfte fehlte) | gsd-security-auditor (opus) |
| 2026-08-24 | 56 | 56 | 0 (T-10-01 per dienstspezifischem ports-Test geschlossen) | Orchestrator-Nachtrag |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-08-24
