---
phase: 10-mail-strikt-lesend-und-die-trifecta-grenze
reviewed: 2026-08-24T15:28:22Z
depth: standard
files_reviewed: 31
files_reviewed_list:
  - src/mcp_connector/nextcloud/clients/mail.py
  - src/mcp_connector/nextcloud/capabilities.py
  - src/mcp_connector/tools/mail.py
  - src/mcp_connector/tools/html_text.py
  - src/mcp_connector/tools/marks.py
  - src/mcp_connector/tools/chatgpt.py
  - src/mcp_connector/ids.py
  - src/mcp_connector/server/reg_mail.py
  - vulture_whitelist.py
  - scripts/check_tool_budget.py
  - scripts/acceptance_all_tools.py
  - scripts/bootstrap_exapp.sh
  - compose.exapp.yml
  - appinfo/info.xml
  - docs/privacy.md
  - docs/faq.md
  - docs/spike-mail.md
  - README.md
  - README.de.md
  - README.fr.md
  - CHANGELOG.md
  - tests/contract/test_no_destructive_calls.py
  - tests/contract/test_tool_surface.py
  - tests/integration/test_mail_read.py
  - tests/integration/test_srv06_degradation.py
  - tests/unit/test_mail_client.py
  - tests/unit/test_mail_tools.py
  - tests/unit/test_ocs_capabilities.py
  - tests/unit/test_html_text.py
  - tests/unit/test_truncation_marks.py
  - tests/unit/test_chatgpt_fetch.py
  - tests/unit/test_ids.py
  - tests/unit/test_exapp_env_setup.py
findings:
  critical: 1
  warning: 5
  info: 4
  total: 10
status: issues_found
---

# Phase 10: Code Review Report

**Reviewed:** 2026-08-24T15:28:22Z
**Depth:** standard
**Files Reviewed:** 31
**Status:** issues_found
**Fix pass:** 2026-08-24, Scope Critical+Warnings: CR-01 und WR-01 bis WR-05 fixed (Commits 6eb5d05, cd1f245, 3fda6ed, c149099, 4193856, 2c51cfc), IN-01 bis IN-04 deferred. Verifikation grün: ruff check, ruff format --check, pyright, pytest (voll und tests/contract).

## Summary

Geprüft wurde die strikt lesende Mail-Familie (mail_browse, fetch mit mail:&lt;id&gt;, HTML-zu-Text, Marker-Filter, App-Erkennung über die Navigation, Bootstrap/GreenMail, Store-Texte, Tests). Kein Structural-Findings-Block wurde übergeben, daher entfällt der Fallow-Abschnitt.

Das Read-only-Gate der Mail-Familie hält: die beiden Mail-Module enthalten keinen einzigen schreibenden Aufruf, die neun Mail-Nadeln in `test_no_destructive_calls.py` haben je einen Gegenbeweis, die vier erlaubten Routen sind positiv benannt, und der `WRITING_CALLS`-Rohquellen-Check deckt Routen ab, an die keine Nadel denkt. Die Marker-Kette (Filterung fremden Texts vor dem Anhängen eigener Marker) ist in beiden Pfaden in der richtigen Reihenfolge, inklusive des Entity-Umwegs (Filterung nach der HTML-Wandlung). Credential-Hygiene in Bootstrap und Tests ist konsequent (Secrets über stdin, T-08-01-Kappung, keine Header-Werte im Protokoll); die eine dokumentierte Abweichung (IMAP-Passwort der Wegwerf-Topologie auf argv) ist begründet und trägt keine Autorität. Die Vokabular-Falle "archiv" ist in allen drei Store-Beschreibungen sauber umgangen und per Gate plus Gegenprobe gehalten.

Der schwerste Befund liegt nicht im Code, sondern in der zentralen Sicherheitsaussage der Phase: "genau ein Ausgangskanal" ist in Gegenwart geteilter Ordner, Boards und Tabellen nicht wahr, und die Store- und Privacy-Texte versprechen einem Administrator mit `NC_MCP_TALK_SEND=off` eine vollständig gebrochene Kette, die so nicht gebrochen ist (CR-01). Daneben stehen fünf Warnungen: ein fehlender Mail-Server-Fehlerzweig auf der teuersten Route, ein Paginierungs-Cursor, der bei einem deformierten Datum stillschweigend verloren geht, eine Postfach-Ebene ohne Fortsetzung oberhalb von 50 Einträgen, Ziffern-Guards, die den projekteigenen Standard unterlaufen, und eine README-Drift bei `fetch`.

Hinweis zur Scope-Liste: `src/mcp_connector/vulture_whitelist.py` existiert nicht; die Datei liegt im Repo-Root (`vulture_whitelist.py`) und wurde dort geprüft (keine Beanstandung).

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: Die Trifecta-Behauptung "genau ein Ausgangskanal" ist falsch, und der Schalter bricht die Kette nicht vollständig

**Status:** fixed (Commit 6eb5d05). Formulierung überall ehrlich gemacht: `talk_send` ist der einzige DIREKTE Nachrichtenkanal, die geteilten Container (Datei, Karte, Zeile) sind als Restweg benannt, inkl. Handlungsempfehlung (Shares der verbundenen Konten prüfen). Geändert: info.xml (EN/DE/FR, Element-Reihenfolge und Version unberührt), privacy.md (Zutat 3, Gegenmaßnahmen-Bullet plus neues Bullet, ehrlicher Rest), faq.md, README.md/.de/.fr (Ketten-Abschnitt). Marker-Tripel-Test und Vokabular-Gate bleiben grün.

**File:** `appinfo/info.xml:64` (EN, analog DE:103, FR:144), `docs/privacy.md:100-102, 119-123`, `docs/faq.md:134`, `README.md:451-459`
**Issue:** Die Phase verkauft als zentrale Gegenmaßnahme: "An outgoing channel. `talk_send`, the one write tool of this server that puts something in front of other people" (privacy.md), "That switch is the one control that takes the third ingredient off the table completely" (privacy.md), "That one switch closes the only way out this app has" (faq.md) und im Store-Text "One way out only: sending a Talk message, and an administrator can switch it off". Diese Aussage ist gegenüber dem tatsächlichen Schreib-Surface zu stark:

1. `deck_create_card` legt Karten in Boards an, die mit anderen Konten geteilt sind. Board-Mitglieder sehen die Karte und erhalten Activity-Benachrichtigungen. Das legt Inhalt "vor andere Menschen".
2. `tables_create_row` schreibt Zeilen in Tabellen, die geteilt sein können (die eigene Testumgebung dieser Codebasis erzeugt genau solche geteilten Objekte).
3. `files_upload` schreibt in den Dateibaum des Nutzers, einschließlich Ordnern, die mit anderen Konten oder per öffentlichem Link geteilt sind (das Bootstrap-Skript legt selbst einen solchen geteilten Ordner an: `mcp-share-*`).

Konsequenz: Ein per Mail injizierter Assistent kann bei `NC_MCP_TALK_SEND=off` weiterhin gelesene Mail-Inhalte exfiltrieren, indem er sie als Karte, Zeile oder Datei in einen geteilten Container schreibt, den ein Dritter liest. Der Schalter schließt den einzigen direkten Nachrichtenkanal, nicht "den einzigen Weg nach außen". Ein Administrator oder Datenschutzbeauftragter, der auf Basis dieser Texte entscheidet ("chain broken rather than narrowed", privacy.md:143-144), trifft eine Entscheidung auf einer falschen Sicherheitsaussage, und zwar in genau dem Dokument, das die Phase als Trifecta-Grenze ausweist. Positiv geprüft: `calendar_create_event` nimmt keine Teilnehmer an (`server/reg_calendar.py`), es gibt also keinen iTIP-Mail-Kanal; die Aussage scheitert an den geteilten Containern, nicht am Kalender.
**Fix:** Die Formulierungen in info.xml (alle drei Sprachen), privacy.md, faq.md und den drei READMEs präzisieren, zum Beispiel:

```markdown
- **One direct messaging channel**: sending a Talk message, and an administrator can
  switch it off for the whole instance.
- The create-only writes (a file, a card, a row) can still land in a folder, board or
  table that is shared with other people. They cannot address anyone, but content
  written there is visible to everyone the container is shared with. An operator who
  needs every path closed also reviews which containers the account shares.
```

Alternativ (größerer Eingriff): die Restkanäle im Threat-Model der Phase benennen und die Sätze "takes the third ingredient off the table completely" / "closes the only way out" streichen. Die Aussage "Mail is read only" und der Contract-Test dahinter sind korrekt und bleiben unberührt.

## Warnings

### WR-01: `get_message` hat keinen Mail-Server-Fehlerzweig, obwohl gerade diese Route immer IMAP öffnet

**Status:** fixed (Commit cd1f245). `_check_mail_server` steht jetzt auch in `get_message`, vor dem 206-Zweig; Modul-Docstring auf "drei IMAP-gestützte Routen" nachgezogen; neuer Unit-Test gegen `MESSAGE_URL` analog zum Listen-Test.

**File:** `src/mcp_connector/nextcloud/clients/mail.py:182-203` (fehlender Aufruf), `:222-237` (`_check_mail_server`)
**Issue:** `_check_mail_server` existiert genau deshalb, weil ein HTTP 500 dieser Familie im Regelfall "der Mailserver des Nutzers ist nicht erreichbar" bedeutet und der geteilte Transport-Check sonst "Problem auf der Nextcloud-Seite, prüfe das Log" antwortet. Der Zweig ist aber nur an `get_mailboxes` und `get_messages` angebaut. `get_message` (Volltext) öffnet laut eigener Doku bei jedem Aufruf eine IMAP-Sitzung in der App und ist damit die Route, die einen toten IMAP-Server am sichersten trifft; die eigene Messung belegt exakt dieses Verhalten (spike-mail.md, GreenMail-Befund: Volltextroute antwortet 500 "Could not connect to IMAP server."). Heute läuft dieser 500 in `ocs.parse_ocs` und erzeugt den irreführenden Nextcloud-Hinweis, den `_check_mail_server` für die zwei anderen Routen ausdrücklich verhindert. Der Nutzer wird auf ein Log geschickt, das er nicht lesen kann, statt auf sein Mail-Konto.
**Fix:**

```python
async def get_message(...):
    message = _path_id(message_id, "message id")
    response = await ocs.ocs_get(client, creds, MESSAGE_PATH.format(message=message))
    _check_mail_server(response, f"the message {message}")  # 500er zuerst, wie bei den Listenrouten
    if response.status_code == PARTIAL:
        return _partial_message(response), True
    ...
```

Plus ein Unit-Test analog `test_a_server_error_on_the_message_list_says_the_same_thing`, nur gegen `MESSAGE_URL`.

### WR-02: Abgeschnittene Nachrichtenseite ohne `next`-Cursor, sobald ein Envelope kein brauchbares `dateInt` trägt

**Status:** fixed (Commit 3fda6ed). Deformierte (=0) Zeitstempel sind aus der Minimum-Bildung ausgenommen (Walrus-Filter wie im Review-Vorschlag); zwei neue Tests: ein deformiertes Datum unterdrückt den Cursor nicht mehr, und eine Seite ganz ohne gültiges Datum bleibt ehrlich ohne `next`.

**File:** `src/mcp_connector/tools/mail.py:435-439`
**Issue:** `oldest = min((_number(item.get("dateInt")) for item in raw), default=0)` nimmt das Minimum über alle Envelopes, und `_number` liefert 0 für fehlende, boolesche oder nicht-ganzzahlige Werte. Ein einziger deformierter Envelope in einer vollen Seite drückt `oldest` auf 0, der `if oldest > 0`-Guard unterdrückt den Cursor, und die Antwort trägt `truncated: true` ohne `next`. Für das Modell liest sich das als "abgeschnitten, aber es gibt keine Fortsetzung", die restlichen Nachrichten des Postfachs sind dann still unerreichbar. Kein Test deckt diesen Fall ab (die Tests prüfen nur volle Seiten mit gültigen Daten und nicht-volle Seiten).
**Fix:**

```python
oldest = min((stamp for item in raw if (stamp := _number(item.get("dateInt"))) > 0), default=0)
```

Damit entscheidet der älteste *gültige* Zeitstempel; ein Envelope ohne Datum fällt sowieso aus der strikten Cursor-Logik der App.

### WR-03: Die Postfach-Ebene kennt keine Fortsetzung; ein Konto mit mehr als 50 Postfächern hat unerreichbare Postfächer

**Status:** fixed (Commit c149099), per Owner-Vorgabe als honest limit statt Variante (a)/(b): bei Kappung trägt die Antwort jetzt eine `note`, die unter dem Maximum das größere `limit` als Ausweg nennt und am Maximum ehrlich sagt, dass die restlichen Einträge über dieses Tool nicht erreichbar sind. Cursor auf Ebenen ohne Fortsetzung wird weiterhin abgelehnt (Regel aus Phase 9). Drei neue Tests (unter dem Maximum, am Maximum, ohne Kappung).

**File:** `src/mcp_connector/tools/mail.py:50-51` (`DEFAULT_LIMIT`/`MAX_LIMIT`), `:565-571` (`_envelope`), `:89-92` (`_CURSOR_HINT`)
**Issue:** `_envelope` schneidet die Postfachliste hart bei `limit` (Standard 20, Maximum 50) und setzt `truncated: true`, aber nur `level=messages` gibt einen Cursor aus; ein Cursor auf `level=mailboxes` wird ausdrücklich abgelehnt. In IMAP ist jedes Ordnerverzeichnis ein Mailbox-Eintrag, und Konten mit mehr als 50 Ordnern sind bei gewachsenen Postfächern normal. Für ein solches Konto sind die Postfächer 51ff. durch dieses Tool prinzipiell nicht adressierbar, und damit auch keine Nachricht darin, obwohl die App die vollständige Liste bereits geliefert hat (die Kappung passiert erst in der Projektion). Das ist keine ehrliche Grenze der App, sondern eine selbstgemachte ohne Ausweg.
**Fix:** Entweder (a) auf der Mailbox-Ebene das Limit nicht anwenden (die App liefert die Liste ohnehin komplett, die Antwort ist klein: ~5 Felder pro Eintrag) oder (b) einen Offset-Cursor für `level=mailboxes` ausgeben, analog zum bestehenden `paging`-Muster. Variante (a) ist eine Ein-Zeilen-Änderung im `mailboxes`-Zweig von `browse` und hält die Aussage "truncated ohne next gibt es nicht auf Ebenen mit vollständiger Antwort".

### WR-04: `str.isdigit`-Guards akzeptieren Nicht-ASCII-Ziffern und unterlaufen den im selben Diff dokumentierten Standard

**Status:** fixed (Commit 4193856). Beide Guards (`ids.parse` und `_path_id` im Mail-Client) messen "numerisch" jetzt mit `re.fullmatch(r"[0-9]+", ...)` wie die Zeitfilter; Testfälle mit `"٤٢"` und `"²"` in test_ids.py und in allen drei Guard-Parametrisierungen von test_mail_client.py (Anfrage-Zähler 0).

**File:** `src/mcp_connector/ids.py:84`, `src/mcp_connector/nextcloud/clients/mail.py:206-219`
**Issue:** `tools/mail.py:130-134` stellt selbst fest: "``str.isdigit`` would accept a superscript two and an Arabic-Indic digit as well" und benutzt deshalb `re.fullmatch(r"[0-9]+", ...)` für Zeitstempel. Die beiden Id-Guards derselben Phase benutzen aber genau `isdigit()`: `ids.parse` für `mail:<id>` und `_path_id` im Mail-Client. `"٤٢".isdigit()` und `"²".isdigit()` sind wahr, also passieren `mail:٤٢` und `mail:²` beide Guards, die URL wird gebaut und die Anfrage geht raus (PHP castet auf 0, 404). Der Docstring des Guards verspricht das Gegenteil: "keeps the most expensive call of this family away from a value that is certainly wrong" (Threat T-10-06/T-10-31). Kein Sicherheitsloch, aber der Guard erfüllt seinen dokumentierten Zweck für diese Eingaben nicht, und zwei Module derselben Familie messen "numerisch" verschieden.
**Fix:** In beiden Stellen dieselbe Prüfung wie bei den Zeitfiltern verwenden:

```python
_DIGITS = re.compile(r"[0-9]+")
...
if not _DIGITS.fullmatch(text):  # statt text.isdigit()
```

Plus je einen Testfall mit `"٤٢"` und `"²"` in `test_ids.py` und `test_mail_client.py` (Anfrage-Zähler 0).

### WR-05: README-Drift: `fetch` wird in allen drei Sprachen als Auflöser von nur vier Id-Arten beschrieben, Mail fehlt

**Status:** fixed (Commit 2c51cfc). Tool-Tabelle und ChatGPT-Abschnitt in allen drei READMEs nachgezogen: fünf Id-Arten inklusive `mail:<databaseId>` (Volltext einer Nachricht, geschnitten bei 32 KiB, Schnitt markiert).

**File:** `README.md:216, 402-404`, `README.de.md:224, 414-416`, `README.fr.md:228, 424-426`
**Issue:** Die Tool-Tabelle ("resolves an id to a file, note, card or event") und der Abschnitt "ChatGPT connector profile" ("`fetch` resolves the four id kinds ... `file:`, `note:`, `card:`, `event:`") sind nach Phase 10 falsch: `fetch` löst sechs Id-Arten auf, darunter `mail:<databaseId>`, was der Mail-Abschnitt derselben READMEs drei Bildschirmseiten weiter oben ausdrücklich sagt. Ein Leser, der die Exfiltrationsfläche über den ChatGPT-Abschnitt auditiert, lernt nicht, dass `fetch` Mail-Volltexte liest, obwohl genau das der sicherheitsrelevante Zugang dieser Phase ist. Widerspricht außerdem der eigenen Regel, Doku bei Verhaltensänderungen mitzuziehen. Der Contract-Test der README-Tabelle prüft nur Name und Berechtigungsstufe, nicht die Beschreibung, deshalb hat kein Gate das gefangen.
**Fix:** In allen drei READMEs beide Stellen aktualisieren, z. B. EN-Tabelle: "resolves an id to a file, note, card, event or mail", und im ChatGPT-Abschnitt: "`fetch` resolves the five id kinds the read tools understand: `file:<fileid>` ..., `event:<calendar>:<object>` and `mail:<databaseId>` (the full text of one message, cut at 32 KiB)."

## Info

### IN-01: Der Schlüssel `truncated` trägt in einer Nachrichten-Antwort zwei Bedeutungen

**Status:** deferred. Info-Befund außerhalb des Fix-Scopes (Critical+Warnings); eine Umbenennung von `truncated` auf Eintragsebene ist eine Antwortformat-Änderung, die bewusst nicht im Fix-Lauf nebenbei passiert.

**File:** `src/mcp_connector/tools/mail.py:477-481` (Eintrag: Vorschau gekappt) und `:434-436` (Antwort: Seite gekappt)
**Issue:** In `level=messages` heißt `truncated: true` auf Antwortebene "die Seite wurde geschnitten, es gibt ggf. `next`", auf Eintragsebene "die Vorschau wurde bei 400 Bytes geschnitten". Ein Modell, das den Hinweis "the answer says with truncated that it was cut" (`_CURSOR_HINT`) liest, kann die beiden verwechseln.
**Fix:** Eintragsfeld umbenennen, z. B. `preview_truncated: true`, oder die Doppelnutzung im Tool-Docstring benennen.

### IN-02: CHANGELOG hat keine [0.1.5]-Sektion, aber Link-Definitionen, die v0.1.5 referenzieren

**Status:** deferred. Info-Befund außerhalb des Fix-Scopes; ob 0.1.5 eine Sektion bekommt oder die Links korrigiert werden, hängt davon ab, ob v0.1.5 getaggt wurde, und gehört in die Release-Pflege.

**File:** `CHANGELOG.md:86` (Sprung 0.1.6 auf 0.1.4), `:382-383` (Link-Definitionen)
**Issue:** Zwischen `## [0.1.6]` und `## [0.1.4]` fehlt die Release-Sektion 0.1.5, während die Compare-Links `[0.1.6]: .../v0.1.5...v0.1.6` und `[0.1.5]: .../v0.1.4...v0.1.5` existieren. Keep-a-Changelog-Anspruch der Datei ("All notable changes ... are documented here") wird damit für ein Release nicht eingelöst; info.xml verweist zudem auf "The shape since 0.1.5".
**Fix:** Eine kurze `## [0.1.5]`-Sektion nachtragen (Store-Text-Release), oder falls 0.1.5 nie getaggt wurde, die Link-Definitionen korrigieren.

### IN-03: Veralteter Kommentar "Our four variables carry none today" bei sechs deklarierten Variablen

**Status:** deferred. Info-Befund außerhalb des Fix-Scopes; die Docstring-Zahl fiel mit keinem der sechs Fixes trivial mit ab (test_exapp_env_setup.py wurde in diesem Lauf nicht angefasst).

**File:** `tests/unit/test_exapp_env_setup.py:1796-1797`
**Issue:** Der Docstring von `variable_problems` spricht von vier Variablen; das Set-Equality-Gate derselben Datei (`:1960-1967`) pinnt sechs (`NC_MCP_PUBLIC_URL`, DCR, CIMD, Allowlist x2, `NC_MCP_TALK_SEND`).
**Fix:** "Our six variables carry none today" oder die Zahl ganz weglassen.

### IN-04: Abnahmeskript meldet einen fehlgeschlagenen Mailbox-Aufruf als SKIP "lists no mailbox"

**Status:** deferred. Info-Befund außerhalb des Fix-Scopes; betrifft nur die Matrix-Begründung des Abnahmeskripts, der Lauf schlägt über die FAIL-Zeile weiterhin korrekt fehl.

**File:** `scripts/acceptance_all_tools.py:292-303`
**Issue:** Schlägt `mail_browse level=mailboxes` fehl, gibt `call` einen leeren String zurück, `loads("")` wird `{}`, `_preferred_mailbox({})` wird `""`, und das Skript schreibt zusätzlich zur FAIL-Zeile eine SKIP-Zeile mit dem Grund "that mail account lists no mailbox", der nicht stimmt. Der Lauf schlägt über die FAIL-Zeile trotzdem fehl, aber die Matrix trägt eine irreführende Begründung.
**Fix:** Den Rückgabewert von `call` prüfen (leer = bereits als FAIL verbucht, keine SKIP-Zeile schreiben), analog für den Messages-Schritt.

---

_Reviewed: 2026-08-24T15:28:22Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
