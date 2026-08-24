---
phase: 10-mail-strikt-lesend-und-die-trifecta-grenze
plan: 05
subsystem: backend
tags: [mail, fetch, chatgpt, ids, html-zu-text, kappung, marker, vertrauens-signale, ssrf]

# Dependency graph
requires:
  - phase: 10-mail-strikt-lesend-und-die-trifecta-grenze
    provides: "Plan 10-01: die gemessene Byte-Kappe des Volltexts (32 KiB; Newsletter nach Wandlung 25582 Bytes)"
  - phase: 10-mail-strikt-lesend-und-die-trifecta-grenze
    provides: "Plan 10-02: clients/mail.py mit get_message -> (dict, body_missing) und capabilities.load_mail plus _MISSING[\"mail\"]"
  - phase: 10-mail-strikt-lesend-und-die-trifecta-grenze
    provides: "Plan 10-03: tools/html_text.to_text und marks.FINAL_TRUNCATION samt Muster in _PATTERNS"
  - phase: 10-mail-strikt-lesend-und-die-trifecta-grenze
    provides: "Plan 10-04: tools/mail.APP und die Id-Form mail:<databaseId>, die mail_browse ausgibt"
  - phase: 01-fundament
    provides: "ids.parse/encode als einzige Id-Stelle, chatgpt._fetch_file als Vorlage für Kappung plus Marker plus flache Metadaten"
provides:
  - "ids.encode_mail und der mail-Zweig von ids.parse mit Ziffernwächter"
  - "chatgpt._fetch_mail: Volltext einer Mail über das bestehende fetch mit mail:<databaseId>"
  - "chatgpt.MAX_MAIL_BYTES = 32768 als Byte-Kappe des Volltexts"
  - "chatgpt.FINAL_TRUNCATION als Re-Export des dritten Markers"
  - "chatgpt.MAIL_WEB_PREFIX = /index.php/apps/mail als url einer Mail"
  - "Die flache metadata-Projektion der Vertrauens-Signale (zehn mögliche Schlüssel)"
affects: [10-06, 10-07, 10-08, phase-11-prepare-context]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Eine zweite Byte-Kappe neben der Datei-Kappe, weil zwei Textarten zwei Preise haben; die Zahl ist die kleinere Hälfte, die wahre Markierung die grössere"
    - "Vertrauens-Signale als flache Stringfelder in metadata, nie als Prosa im text (Signal-Wäsche)"
    - "Ein fehlendes Prüfergebnis wird als unchecked projiziert und nie als invalid: eine Nichtaussage ist keine negative Aussage"
    - "Ein Erfolgsergebnis ohne Inhalt wird durch einen Satz mit nächstem Schritt ersetzt (Vorbild _fetch_event)"

key-files:
  created: []
  modified:
    - "src/mcp_connector/ids.py"
    - "src/mcp_connector/tools/chatgpt.py"
    - "tests/unit/test_ids.py"
    - "tests/unit/test_chatgpt_fetch.py"
    - "vulture_whitelist.py"

key-decisions:
  - "MAX_MAIL_BYTES = 32 * 1024 (32768 Bytes), eigene Konstante neben MAX_TEXT_BYTES (512 KiB) und weit über MAX_PREVIEW_BYTES (400): die Messung aus 10-01 steht als Begründung im Kommentar"
  - "Der angehängte Marker ist FINAL_TRUNCATION; TRUNCATION_NOTE und EXCERPT_TRUNCATION wären hier beide unwahr"
  - "Der Body läuft immer durch html_text.to_text, hasHtmlBody wird gar nicht gelesen (K2)"
  - "url einer Mail ist {base_url}/index.php/apps/mail: für eine einzelne Nachricht ist keine Web-Route von Mail 5.11.1 verifiziert, und ein geratener Link öffnet eine Fehlerseite statt einer Mail"
  - "dkim kennt drei Werte (valid, invalid, unchecked); hasDkimSignature bekommt keinen eigenen Schlüssel, weil eine fehlende Signatur und ein fehlendes Prüfergebnis denselben nächsten Schritt haben"
  - "signature kennt vier Werte: unsigned, valid, invalid und unchecked für signiert-aber-nicht-prüfbar (signatureIsValid ist nullable)"
  - "encrypted, phishing_warning und phishing_checks erscheinen nur, wenn sie wahr beziehungsweise nicht leer sind; sender_trusted, dkim und signature stehen immer da"
  - "206 und ein 200 mit leerem Body sind je ein ToolError mit nächstem Schritt, nie ein leerer Erfolg"
  - "Der Ziffernwächter steht in ids.parse und nicht nur im Client: mail:abc kostet null Requests"
  - "get_message und to_text verlassen die vulture-Whitelist mit diesem Plan, wie es die Regel der Datei verlangt"

patterns-established:
  - "Ein Signal, das ein Fremder in seinen Text schreiben könnte, gehört in ein Datenfeld und nicht neben den Text"
  - "Eine Kappungsmarkierung darf nur versprechen, was es gibt; wo es keine Fortsetzung gibt, sagt sie das"

requirements-completed: [MAIL-02]

# Metrics
duration: 20min
completed: 2026-08-24
---

# Phase 10 Plan 05: Der Volltext einer Mail über das bestehende fetch, Zusammenfassung

**`fetch("mail:<databaseId>")` liest eine einzelne Mail, wandelt ihren Body unbedingt zu Text, kappt ihn bei 32 KiB mit einer Markierung, die keine Fortsetzung verspricht, und legt Nextclouds Vertrauens-Signale als flache Stringfelder daneben statt als Sätze hinein.**

## Performance

- **Duration:** 20 min
- **Started:** 2026-08-24T14:08Z
- **Completed:** 2026-08-24T14:28Z
- **Tasks:** 3
- **Files created/modified:** 5

## Accomplishments

- `mail` ist das sechste Id-Kind, einteilig wie `file` und `note`, aber mit einem Ziffernwächter, den die zwei nicht haben: `mail:abc`, `mail:4711a`, `mail:-1`, `mail: 4711`, `mail:47:11` und `mail:` scheitern ohne einen einzigen Request (T-10-31).
- `_fetch_mail` ruft `capabilities.require_app` als erste Zeile und `get_message` **genau einmal**; ein Test zählt die Route und behauptet 1, ein zweiter behauptet 0 für eine fehlende Mail-App.
- Der Body läuft **immer** durch `html_text.to_text`, unabhängig von `hasHtmlBody`. Der Test dazu ist der wichtigste des Blocks: eine reine Textmail kommt aus der App als `Gr&uuml;&szlig;e` mit `<a href=...>`, und im Ergebnis stehen echte Umlaute ohne eine spitze Klammer.
- Die Reihenfolge steht wie im Datei-Zweig: fremde Marker weg, dann kappen, dann eigenen Marker anhängen. Eine Mail, die `FINAL_TRUNCATION` selbst mitbringt und zusätzlich gekappt wird, trägt am Ende genau einen Marker, und der ist unserer.
- Die Vertrauens-Signale sind flach und ausschliesslich Strings; das Ergebnis validiert durch `FetchResult`, also ist der ChatGPT-Kontrakt unverändert (Falle 7).
- `tests/unit/test_chatgpt_fetch.py` hat **16 neue Mail-Testfunktionen** (38 im ganzen File), `tests/unit/test_ids.py` **27 Fälle**; `ruff`, `ruff format`, `pyright`, `vulture` und `uv run pytest -q` sind grün, `tests/contract` ebenso, `scripts/check_tool_budget.py` meldet weiterhin 20 Werkzeuge bei 14358 von 15000 Bytes.
- Die zwei letzten geparkten Whitelist-Einträge der Phase (`get_message`, `to_text`) sind aufgelöst; die Mail-Familie parkt nichts mehr.

## Die Schnittstelle, gegen die 10-07 und 10-08 bauen

### Die Byte-Kappe des Volltexts

| Name | Wert | Ort |
|------|------|-----|
| `chatgpt.MAX_MAIL_BYTES` | `32 * 1024` = **32768 Bytes** | `src/mcp_connector/tools/chatgpt.py` |

Gemessen in Plan 10-01 gegen Mail 5.11.1: ein gewöhnlicher 45-KB-Newsletter kommt als 48811
Bytes HTML an und wird nach der Wandlung **25582 Bytes** Text, eine Kappe von 16 KiB hätte also
den Normalfall zerschnitten. Sie ist ausdrücklich **nicht** `MAX_TEXT_BYTES` (512 KiB ist die
Datei-Grenze und für eine Mail ein Kontext-Totalschaden) und ausdrücklich nicht die
Vorschau-Kappe `mail_browse.MAX_PREVIEW_BYTES` (400 Bytes sind ein halber Satz). Gemessen wird
auf der UTF-8-Kodierung, und der Schnitt wird tolerant dekodiert, damit ein Umlaut an der
Schnittstelle verschwindet statt kaputt anzukommen.

### Der Marker einer gekappten Mail

`chatgpt.FINAL_TRUNCATION = marks.FINAL_TRUNCATION`, wörtlich:

```
[truncated here; the rest was not returned and there is no way to continue]
```

Er nennt kein Werkzeug und keinen Offset, weil es für eine Mail beides nicht gibt:
`TRUNCATION_NOTE` schickte das Modell zu `files_read` mit einem Offset, den eine Nachricht nicht
hat, `EXCERPT_TRUNCATION` zu `fetch`, und `fetch` ist genau der Aufruf, der gerade gekappt hat.
Angehängt wird er mit `\n\n` an den gekappten Text, und `metadata["truncated"]` steht dann auf
`"true"`.

### Die vollständige Schlüsselliste von `metadata`

Alle Werte sind `str`, weil `FetchResult.metadata` `dict[str, str]` ist.

| Schlüssel | Wann | Mögliche Werte |
|-----------|------|----------------|
| `kind` | immer | `"mail"` |
| `sender_trusted` | immer | `"true"`, `"false"` |
| `dkim` | immer | `"valid"`, `"invalid"`, `"unchecked"` |
| `signature` | immer | `"unsigned"`, `"valid"`, `"invalid"`, `"unchecked"` |
| `encrypted` | nur wenn `smime.isEncrypted` wahr ist | `"true"` |
| `phishing_warning` | nur wenn `phishingDetails.warning` wahr ist | `"true"` |
| `phishing_checks` | nur wenn mindestens ein Check ausgelöst hat | die `type`-Werte, komma-getrennt, zum Beispiel `"spf, dmarc"` |
| `mailbox` | wenn `mailboxId` eine positive Zahl ist | die Zahl als String, zum Beispiel `"7"` |
| `date` | wenn `dateInt` in einen Moment umzurechnen ist | ISO 8601 in UTC, zum Beispiel `"2025-08-14T14:00:00+00:00"` |
| `truncated` | nur wenn gekappt wurde | `"true"` |

Drei Entscheidungen in dieser Tabelle, die Plan 10-07 mitschreiben muss:

1. **`unchecked` ist keine Fehlermeldung.** `dkimService->getCached` rechnet nichts nach, ein
   fehlendes `dkimValid` heisst "es gibt kein Urteil" und nicht "das Urteil ist schlecht"
   (T-10-36). Dasselbe Wort deckt die Mail ohne jede Signatur ab: beide führen zum selben
   nächsten Schritt, und keine von beiden ist ein geprüfter Absender. `hasDkimSignature`
   bekommt darum **keinen** eigenen Schlüssel.
2. **`signature` hat vier Werte, nicht drei.** `smime.signatureIsValid` ist nullable; eine
   signierte Mail ohne Prüfergebnis ist weder `unsigned` (das versteckte eine Signatur) noch
   `invalid` (das erfände eine fehlgeschlagene Prüfung), also `unchecked`, dasselbe Vokabular
   wie bei DKIM.
3. **Kein Signal steht im `text`.** Neben fremdem Text ist ein Satz dieses Servers von einem
   Satz des Absenders nicht zu unterscheiden, und eine Mail, die "DKIM: valid" in ihren Körper
   schreibt, wäre sonst nicht von der Wahrheit zu trennen (T-10-28). Ein Test behauptet, dass
   `dkim`, `phishing` und `trusted` im `text` nicht vorkommen, obwohl alle drei Felder gesetzt
   sind.

Verworfen und darum nicht in der Antwort: die Empfänger, `flags`, `attachments`,
`inlineAttachments`, `itineraries`, `scheduling`, `signature` (der Textblock), die
Adressfelder der Nachricht und die drei weiteren Id-Felder (`uid`, `messageId` und das `id`
der Volltextantwort), von denen keines in diesem Connector etwas adressiert.

### Die gewählte `url` einer Mail

```python
MAIL_WEB_PREFIX = "/index.php/apps/mail"          # url = f"{creds.base_url}{MAIL_WEB_PREFIX}"
```

**Begründung.** Für **eine einzelne Nachricht** ist in Mail 5.11.1 keine Web-Route verifiziert,
und ein auf einer Vermutung gebauter Link ist schlechter als ein Link auf die App: er öffnet im
Browser eine Fehlerseite statt einer Mail. Die Mail-App-Route ist die ehrliche Antwort, und sie
ist eine Seite, die ein Mensch tatsächlich öffnen kann. Sie wird wie jeder andere Link dieses
Moduls aus `clients.creds.base_url` gebaut und **nie** aus der Antwort übernommen: die
Abmelde-, Rohquellen- und Anhang-Adressen einer Nachricht hat ihr Absender ausgesucht, dieser
Server ruft keine davon auf und gibt keine als `url` weiter (T-10-30). Ein Test setzt zwei
dieser Felder auf eine fremde Domain und behauptet, dass sie im ganzen Ergebnis nirgends
vorkommt; ein zweiter greppt die Quelldatei danach, dass die drei Feldnamen dort gar nicht
stehen.

### Die zwei Ablehnungen, wörtlich

**HTTP 206, die Nachricht konnte nicht entschlüsselt werden** (`body_missing` aus
`clients/mail.get_message`):

```
message: The mail {message_id} was found, but its body could not be decrypted, so there is
         no text to read.
hint:    Open that message in the Mail app of Nextcloud: an encrypted mail can be read where
         its key is, and this connector holds no key.
```

**HTTP 200 mit leerem oder fehlendem Body, oder nach der Wandlung leerer Text:**

```
message: The mail {message_id} carries no text that can be read.
hint:    Open it in the Mail app: the usual reason is a message that consists of attachments
         alone, and this connector reads no attachment.
```

Beide sind ein `ToolError` und nie ein leerer Erfolg: ein Erfolgsergebnis ohne Inhalt ist die
Form, die zum Erfinden einlädt (T-10-34, T-01-75). Das Vorbild ist `_fetch_event`, das ein
Kalenderobjekt ohne Termin ablehnt statt leer zu antworten.

### Die Id-Form und der Hinweistext

`ids.encode_mail(4711)` und `ids.encode_mail("4711")` ergeben beide `mail:4711`, also genau die
Form, die `mail_browse` auf der Nachrichtenebene ausgibt. `ids.parse("mail:0")` ist gültig: die
Ablehnung einer Null wäre eine Aussage über die Datenbank der App und nicht über die Form einer
Id. Der Hinweistext, den jedes Werkzeug bei einer abgelehnten Id ausgibt, nennt jetzt alle sechs
Formen:

```
Use an id exactly as returned by a search tool: file:<fileid>, note:<id>,
card:<board>:<stack>:<card>, event:<calendar>:<object>, mail:<databaseId> or url:<absolute-url>.
```

## Deviations from Plan

Keine inhaltliche Abweichung; drei Präzisierungen, die der Plan offengelassen hat:

1. **`signature` bekommt einen vierten Wert `unchecked`.** Der Plan liess die Wahl offen
   ("`unsigned` oder den gewählten Wert für nicht prüfbar") und verlangte, dass ein Test sie
   festschreibt. `unchecked` ist gewählt, weil `unsigned` eine vorhandene Signatur verstecken
   würde; `test_an_encrypted_mail_with_an_unverifiable_signature_says_exactly_that` nagelt es
   fest.
2. **Die `url` ist die Mail-App-Route**, nicht die Instanz-Wurzel. Der Plan liess beides zu und
   verlangte die Begründung in der Zusammenfassung; sie steht oben.
3. **`vulture_whitelist.py` wurde mitgeändert** (nicht in `files_modified` des Plans, aber von
   der Regel dieser Datei und von der Wellen-Übergabe verlangt): `get_message` und `to_text`
   verlassen die Liste mit dem Plan, der ihre Aufrufer schreibt. `uv run vulture src/mcp_connector
   vulture_whitelist.py` ist ohne beide Einträge grün.

## Task Commits

1. **Task 1: mail als Id-Kind, mit Ziffernwächter** - `ca2c735` (feat)
2. **Task 2: `_fetch_mail`, mit Wandlung, Markierung und flachen Signalen** - `f0bea0b` (feat)
3. **Task 3: Unit-Abdeckung des mail-Zweigs von fetch** - `6b2e156` (test)

## Files Created/Modified

- `src/mcp_connector/ids.py` - Formatliste um `mail:<databaseId>` samt der Warnung vor `uid`, `remoteId` und `messageId` ergänzt, `_HINT` ergänzt (nicht ersetzt), `encode_mail`, `mail`-Zweig in `parse` mit Ziffernwächter und dem Grund als Kommentar
- `src/mcp_connector/tools/chatgpt.py` - `FINAL_TRUNCATION`, `MAX_MAIL_BYTES`, `MAIL_WEB_PREFIX`, `_NO_SUBJECT`, `case "mail"` im Dispatch, `_fetch_mail`, `_mail_signals`, `_dkim`, `_signature`, `_phishing_checks`, `_mail_date`; Modul-Docstring auf fünf Leser nachgezogen
- `tests/unit/test_ids.py` - Roundtrip über sechs Kinds, sieben Ablehnungsfälle für `mail:`, `mail:0` als gültig, Hinweistext-Test über alle sechs Formen
- `tests/unit/test_chatgpt_fetch.py` - 16 Mail-Tests plus die Fixtures `full_message`, `mock_mail_app`, `mock_mail`, `HTML_BODY`, `TEXT_BODY`
- `vulture_whitelist.py` - `get_message` und `to_text` aufgelöst, mit dem Vermerk, welcher Plan sie gelöst hat

## Verification

| Prüfung | Ergebnis |
|---------|----------|
| `uv run ruff check .` | grün |
| `uv run ruff format --check .` | grün, 193 Dateien |
| `uv run pyright` | 0 errors, 0 warnings |
| `uv run vulture src/mcp_connector vulture_whitelist.py` | grün, ohne neuen Eintrag |
| `uv run pytest -q` (Default-Auswahl) | grün |
| `uv run pytest tests/contract -q` | grün, 51 Fälle: Output-Schema von `fetch` und `search` unverändert |
| `uv run python scripts/check_tool_budget.py` | Exit 0, 20 Werkzeuge, 14358 von 15000 Bytes |
| `git diff --stat` gegen `pyproject.toml`, `uv.lock`, `models.py`, `provider_map.py`, `tools/context.py`, `server/` | leer |
| Quelltext-Gate: `unsubscribeUrl`, `rawUrl`, `downloadUrl` in `chatgpt.py` | kommen nicht vor |

## Was offen bleibt

- **MAIL-02 ist erfüllt, aber noch nicht live nachgewiesen.** Plan 10-08 führt den Volltext-Lauf
  gegen die GreenMail-Topologie, inklusive der Gegenprobe, dass ein Volltextabruf `flags.seen`
  nicht setzt (die App liest mit `peek`, das ist eine Eigenschaft der Fassung und kein
  Protokollversprechen).
- **Die Doku kennt den Weg noch nicht.** Plan 10-07 schreibt `mail:<databaseId>`, die Byte-Kappe,
  die `metadata`-Schlüssel und die zwei Ablehnungssätze in README, Doku und Store-Text.
- **`fetch` bleibt bei zwei Parametern.** Dieser Plan registriert kein Werkzeug und ändert kein
  Schema; die Werkzeugoberfläche der Mail-Familie entsteht in Plan 10-06.

## Self-Check: PASSED
