# Phase 12: Konsistenz und Härtungs-Nachzieher - Research

**Researched:** 2026-08-25
**Domain:** Interne Konsistenz eines bestehenden Python-MCP-Servers (Antwortschlüssel, Id-Codec, Modulgrenzen, Quelltext-Gates). Kein neues Framework, keine neue Abhängigkeit.
**Confidence:** HIGH (alle Fundstellen im Arbeitsbaum gelesen und die Gates lokal ausgeführt; die zwei externen Verifikationen für SEC-02(a) gegen Release-Tags nachgelesen)

## Summary

Diese Phase ist reine Innenarbeit an vier Stellen, die Phase 11 bewusst offen gelassen hat. Alle vier sind exakt lokalisierbar, und keine von ihnen braucht neue Bibliotheken, neue Routen oder eine Anhebung eines Gates. Die Recherche hat für jeden der vier Arbeitspakete die Fundstellen, die Vorbild-Implementierung im Repo, die betroffenen Tests und die Byte-Kosten bestimmt.

Zwei Befunde sind für die Planung wichtiger als der Rest. Erstens: die Dateiangabe in `REQUIREMENTS.md` für TOOL-18 ist falsch. Der `_ID_KIND`-Workaround steht in `src/mcp_connector/tools/mail.py:70` und wird in `:490` benutzt, nicht in `tools/chatgpt.py`; `chatgpt.py` enthält überhaupt kein `_ID_KIND`. Die IN-Nummern in den Requirements sind gegen `11-REVIEW.md` um vier Positionen verschoben (Requirement sagt IN-05/IN-06, gemeint sind IN-01 und IN-04; TOOL-19 meint IN-05 und IN-06). Die Prosa der Requirements ist normativ, die Datei- und IN-Angaben sind es nicht. Zweitens: die Byte-Sorge der Leitplanke ist gemessen und entschärft. `talk_browse` steht heute bei 858 Bytes gegen `MAX_TOOL_BYTES` 1400, die ganze Oberfläche bei 15657 gegen 18000. Der analoge Satz aus dem Mail-Vorbild kostet rund 53 Bytes; eine Gegenkompression wie bei `mail_browse` ist nicht nötig, weil `talk_browse` 542 Bytes eigene Luft hat und die Oberfläche 2343.

Der dritte Befund betrifft die Gate-Bauweise für TOOL-19. Ein naiver Grep auf `_`-Durchgriffe wird rot, weil `tools/context.py` in drei Kommentaren und einem Docstring `mail_tools._mailboxes`, `mail_tools._messages`, `mail_tools._special_role` und `talk._conversation` nennt. Das Repo hat für genau dieses Problem schon eine Lösung: `tests/contract/test_no_destructive_calls.py::_code_lines` blendet Kommentare und Docstrings per `ast` plus `tokenize` aus, bevor gesucht wird. Zusätzlich gemessen: `ruff --select SLF` findet in `src/` genau drei Verstöße, und einer davon ist der zu behebende `talk_tools._room`. Die Lint-Regel wäre also fast frei zu haben, kostet aber zwei `noqa`-Ausnahmen in `oauth/provider.py` und ein `per-file-ignores` für `tests/**` (53 Treffer, alle legitime Quelltext-Gates).

**Primary recommendation:** Alle vier Pakete streng nach dem Vorbild-Commit `53ba602` arbeiten (eine Bedeutung je Schlüssel, Kommentar mit Begründung an der Änderungsstelle, ein Test für den gemeinsamen Fall, Gegenprobe für jedes neue Gate). Neue Gates gehören nach `tests/contract/` oder `tests/unit/`, weil CI dort ohne neuen Workflow-Schritt läuft (`.github/workflows/ci.yml:36`: `uv run pytest tests/unit tests/contract`).

## User Constraints

Keine `12-CONTEXT.md` vorhanden (das Phasenverzeichnis war bis auf diese Datei leer, `/gsd:discuss-phase` ist für Phase 12 nicht gelaufen). Die verbindlichen Vorgaben stammen daher aus `ROADMAP.md` (Success Criteria) und dem Auftrag des Orchestrators.

### Locked Decisions (aus ROADMAP.md, Phase 12, SC 1-5)

- `talk_browse(level="messages")`: Nachrichtenebene heißt `message_truncated`, Antwortebene behält `truncated`. Tool-Docstring nennt je Ebene genau eine Bedeutung. Tests decken beide Ebenen getrennt ab. Die Umbenennung steht als Formatänderung im Changelog-Block für 0.1.9.
- Kein Produktionsmodul baut einen Id-String außerhalb des Codecs. `ids.encode_mail` statt `_ID_KIND`. `ids.parse` lehnt die `url:`-Id mit Whitespace-Rest ab. Je ein Negativtest.
- Kein Tool-Modul ruft eine `_`-präfixte Funktion eines fremden Tool-Moduls. `talk_tools._room` läuft über eine öffentliche Schnittstelle. Ein Gate oder Test wird rot, wenn der Durchgriff zurückkehrt. Das README-Beispiel für den unbekannten Suchprovider nennt eine echte, nie registrierte Provider-Id statt `spreed`.
- SEC-02: (a) jeder `PROVIDER_KINDS`-Eintrag trägt den Verifikationskommentar mit Repository, Datei und Klasse, auch `files` und `notes`; (b) das Quelltext-Gate aus T-11-29 läuft als Regressionstest in der Suite; (c) das Vokabular-Gate prüft über `appinfo/info.xml` hinaus mindestens die drei READMEs und `CHANGELOG.md`, `docs/store-submission.md` ist bereinigt oder als interne Ausnahme begründet.
- `BUDGET_BYTES` bleibt 18000, `MAX_TOOL_BYTES` bleibt 1400, die Zahl der Werkzeuge bleibt 21, keine neuen Familien. Die einzige nutzersichtbare Änderung ist der umbenannte Nachrichten-Schlüssel.

### Claude's Discretion

- Der öffentliche Name für `_room` (Vorschlag des Reviews: `room_of`; Konvention des Moduls: `one_message`, also `one_room`).
- Die Bauweise des Privat-Durchgriff-Gates (AST-Test versus `ruff --select SLF`), siehe Abschnitt "Architecture Patterns".
- Ort und Zuschnitt des erweiterten Vokabular-Gates, solange die Wortliste nicht dupliziert wird.
- Ob der Changelog-Block 0.1.9 in dieser Phase angelegt oder nur der Text vorbereitet wird (Phase 13 SC2 verlangt den vollständigen Block).

### Deferred Ideas (OUT OF SCOPE)

- Ein Contract-Test, der die README-Statuszeile gegen `mcp_connector.__version__` hält (Vorschlag aus WR-03; existiert heute nicht, ist kein Requirement dieser Phase, Runbook-Schritt 1 trägt die Stelle stattdessen).
- Auflösung eines Mail-Suchtreffers zu `mail:<databaseId>` (AR-11-1, Future Requirement).
- Die `title`-Keys der Schemas als Byte-Sparmaßnahme (`scripts/check_tool_budget.py:56-63` nennt sie als bewusst ungenutzten Schnitt).
- IN-02 (stale Ampersand-Kommentar in `info.xml`) und IN-03 (`never called` im Abnahmeskript) aus `11-REVIEW.md`: nicht in TOOL-17..19 oder SEC-02 abgebildet.

## Project Constraints (from CLAUDE.md)

- **Sprache:** Code und README Englisch, Projektkommunikation Deutsch. Keine Em-Dashes, echte Umlaute in deutschen Texten. Gilt auch für Kommentare und Changelog-Text.
- **Security:** Der MCP darf nie mehr sehen als der angemeldete Nutzer. Keine destruktiven Writes.
- **Solo-Betrieb:** Wartungsaufwand pro Feature zählt, kuratiert schlank schlägt breit. Übersetzt auf diese Phase: ein Gate mehr ist billiger als eine Regel ohne Gate, aber zwei Wahrheiten über dieselbe Regel sind teurer als beides.
- **Timeline:** Conference September 2026 ist die harte Deadline. Phase 12 ist Vorarbeit für das Release 0.1.9 in Phase 13.
- **Toolchain:** `uv` ist Pflicht, das globale Python ist defekt. Jeder Verifikationsbefehl beginnt mit `uv run --no-sync`.
- **GSD-Workflow:** Keine direkten Repo-Edits außerhalb eines GSD-Kommandos.
- **Projekt-Skills:** `.claude/skills/` existiert nicht in diesem Repo (leer). Keine zusätzlichen Regeldateien zu laden.

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| TOOL-17 | `truncated` der Nachrichtenebene von `talk_browse(level="messages")` heißt `message_truncated`, Antwortebene behält `truncated`, Docstring sagt je Ebene eine Bedeutung, Changelog-Formatänderung, Tests für beide Ebenen getrennt | Fundstellen exakt: `tools/talk.py:525` (Eintrag), `:495` und `:702` (Antwort). Kopplung: `tools/chatgpt.py:653` liest den Eintrags-Schlüssel und muss mitziehen. Vorbild 1:1 in Commit `53ba602`. Byte-Kosten gemessen: unkritisch. Betroffene Tests benannt. |
| TOOL-18 | Id-Codec als einzige Quelle: `ids.encode_mail` statt `_ID_KIND`, `ids.parse` lehnt Whitespace-`url:` ab, Negativtests | `_ID_KIND` liegt in `tools/mail.py:70`+`:490` (nicht chatgpt.py, siehe Diskrepanz-Abschnitt). Verhaltensgleichheit belegt (`_number(databaseId) > 0`-Filter in `mail.py:441`). `ids.parse:115-116` ist der Frühausstieg vor dem Leersegment-Check in `:161`. |
| TOOL-19 | Öffentliche Schnittstellen statt Privat-Durchgriffen, `_room` öffentlich, Gate hält es fest, README-Beispiel mit echter nie registrierter Provider-Id | Genau ein echter Durchgriff im Repo: `tools/chatgpt.py:616`. Drei Aufrufer von `_room` (`talk.py:291`, `talk.py:481`, `chatgpt.py:616`). Gate-Bauweise mit Vorbild und Messung geklärt. README-Ersatz-Id ist `talk-conversations`, bereits durch einen Test als "echt und nie registriert" belegt. |
| SEC-02 | Drei Nachzieher aus 11-SECURITY.md: PROVIDER_KINDS-Kommentare, T-11-29-Quelltext-Gate als Regressionstest, Vokabular-Gate über info.xml hinaus | (a) Repository, Datei, Klasse und Verhalten für `files` und `notes` in dieser Recherche verifiziert (Zitate unten). (b) Der einmalige Prüfschritt ist rekonstruiert (`level="messages"` kommt in `context.py` nirgends als Code vor) und als Test formulierbar. (c) Trefferlage vollständig ausgezählt: nur `docs/store-submission.md` trägt das Wort, zehn Zeilen, davon zwei datierte Proof-Zeilen und ein Nextcloud-Klassenname. |

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Antwortschlüssel einer Tool-Antwort | Tool-Schicht (`src/mcp_connector/tools/talk.py`) | Registrierung (`server/reg_talk.py`, Docstring) | Die Projektion baut den Schlüssel, die Registrierung erklärt ihn dem Modell. Beide Seiten müssen zusammen geändert werden, sonst hat der Schlüssel zwei Erklärungen. |
| Verbraucher desselben Schlüssels | Tool-Schicht (`tools/chatgpt.py::_fetch_message`) | - | `fetch` liest die Projektion von `talk._message` und übersetzt das Flag in `metadata["truncated"]`. Ohne Mitzug verliert `fetch` die Kappungsangabe still. |
| Id-Erzeugung und Id-Prüfung | Codec (`src/mcp_connector/ids.py`) | - | Der Modul-Docstring verspricht "encoded and parsed in exactly one place". Jeder zweite Bauer ist eine Verletzung, unabhängig davon ob er heute korrekt ist. |
| Modulgrenze zwischen Tool-Familien | Tool-Schicht (öffentliche Funktion in `tools/talk.py`) | Gate in `tests/contract/` | Der Stabilitätsvertrag ist ein Name, nicht ein Kommentar. Das Gate ist die Durchsetzung. |
| Provider-Verifikation | Datenkarte (`src/mcp_connector/provider_map.py`, Kommentare) | Eingefrorener Halter (`tests/unit/test_provider_map.py:287`) | Der Kommentar ist der Beweis, der Test die Grenze der Menge. Beide existieren schon, nur zwei Kommentare fehlen. |
| Vokabular- und Quelltext-Regeln | Test-Schicht (`tests/unit/`, `tests/contract/`) | CI (`pytest tests/unit tests/contract`) | CI führt beide Verzeichnisse ohne neuen Schritt aus. Ein Skript-Gate bräuchte eine Workflow-Änderung. |

## Standard Stack

Keine neuen Bibliotheken. Diese Phase nutzt ausschließlich die installierte Toolchain.

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytest | >=9.1.1 (installiert) | Alle Gates und Regressionstests | Projekt-Standard, CI führt `tests/unit tests/contract` aus [VERIFIED: pyproject.toml, ci.yml gelesen] |
| ruff | >=0.16.3 (installiert) | Lint und Format, optional `SLF` für Privat-Durchgriffe | Pflicht laut globaler Regel; `select` steht in `pyproject.toml` [VERIFIED] |
| pyright | >=1.1.411 (installiert) | Typprüfung, `typeCheckingMode = "standard"` | Meldet den Privat-Durchgriff NICHT (`reportPrivateUsage` ist im Standard-Modus aus), was das Gate begründet [VERIFIED: pyproject.toml gelesen, heutiger Lauf ist grün trotz `chatgpt.py:616`] |
| vulture | >=2.16 (installiert) | Toter Code; relevant beim Umbenennen von `_room` | `vulture src scripts vulture_whitelist.py` läuft in CI; `_room` steht heute nicht in der Whitelist [VERIFIED: grep] |
| stdlib `ast` + `tokenize` | 3.13 | Quelltext-Gates ohne Fremdpaket | Genau so gebaut in `tests/contract/test_no_destructive_calls.py::_code_lines` [VERIFIED] |
| stdlib `inspect.getsource` | 3.13 | Quelltext-Gate auf eine einzelne Funktion | Bereits benutzt in `tests/unit/test_tools_context.py:970/978` [VERIFIED] |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| AST-Gate für Privat-Durchgriffe | `ruff --select SLF` in `pyproject.toml` | Billiger im Code, teurer in Ausnahmen: zwei `# noqa: SLF001` in `oauth/provider.py` (`:554`, `:1544`, beide Zugriffe auf eigene Klassen-Interna im selben Modul) plus `"tests/**" = ["SLF001"]` in `per-file-ignores` wegen 53 legitimer Quelltext-Gates. Die Regel prüft außerdem mehr als das Requirement will (jeden Privatzugriff, nicht nur den zwischen Tool-Modulen). |
| Test-Gate für das Vokabular | Skript unter `scripts/` | Braucht einen neuen CI-Schritt in `.github/workflows/ci.yml`; ein Test in `tests/unit` oder `tests/contract` läuft automatisch mit. |
| `message_truncated` | `preview_truncated`-Analogon wie `text_truncated` | Der Name ist in ROADMAP SC1 und REQUIREMENTS wörtlich festgelegt. Keine Freiheit. |

**Installation:** Keine. Kein `uv add`, kein `pip install`, kein `npm install` in dieser Phase.

## Package Legitimacy Audit

Nicht anwendbar: diese Phase installiert kein externes Paket. `pyproject.toml` und `uv.lock` bleiben unangetastet (das ist zugleich die übliche `T-*-SC`-Registerzeile des Projekts). Sollte ein Plan wider Erwarten eine Abhängigkeit brauchen, ist das ein Scope-Bruch und gehört als eigener Checkpoint vor die Installation.

## Fundstellen-Katalog

### TOOL-17: die zwei Ebenen von `truncated` in Talk

| Ort | Zeile | Ebene | Was zu tun ist |
|-----|-------|-------|----------------|
| `src/mcp_connector/tools/talk.py` | 525 | Eintrag (`_message`) | `entry["truncated"] = True` wird `entry["message_truncated"] = True`, mit Begründungskommentar wie in `mail.py:502-508` |
| `src/mcp_connector/tools/talk.py` | 513-515 | Docstring `_message` | "The truncation is a field beside the text" nennt den Namen des Feldes noch nicht; ergänzen |
| `src/mcp_connector/tools/talk.py` | 495 | Antwort (`_messages`) | Bleibt `truncated`, unverändert. Docstring `:460-466` erklärt es schon |
| `src/mcp_connector/tools/talk.py` | 702 | Antwort (`_envelope`, Konversationsebene) | Bleibt `truncated`, unverändert |
| `src/mcp_connector/tools/talk.py` | 12-13 | Modul-Docstring | "Every cut is named in the answer, never silent" darf die zwei Namen nennen (kostet keine `tools/list`-Bytes) |
| `src/mcp_connector/tools/talk.py` | 107-110 | `_CURSOR_HINT` | Bezieht sich auf die **Konversationsliste**, also die Antwortebene. Anders als in Mail keine Pflichtänderung; falls präzisiert, den Talk-Sinn beachten (die Konversationsliste hat kein `next`) |
| `src/mcp_connector/server/reg_talk.py` | 46-48 | Tool-Docstring | Satz nach dem Mail-Muster: `truncated: page cut; message_truncated: message cut.` |
| `src/mcp_connector/server/reg_talk.py` | 42 | `cursor`-Field-Description | "Next page handle from a truncated answer" bleibt richtig (Antwortebene) |
| `src/mcp_connector/tools/chatgpt.py` | 653-654 | Verbraucher | `if entry.get("truncated")` muss `message_truncated` lesen, sonst verliert `fetch` das Flag still. `metadata["truncated"]` in `:654` bleibt so (eine Ebene, eine Bedeutung) |

**Nicht betroffen, geprüft:** `tools/tables.py` (nur Antwortebene, `:406` und `:550`), `tools/mail.py` (schon gefixt), `tools/files.py`, `tools/calendar.py`, `tools/contacts.py`, `tools/deck.py` (je nur Antwortebene). Nach dieser Phase existiert im Repo kein Modul mehr, das dasselbe Wort auf zwei Ebenen benutzt. Belegt per `grep -rn '\["truncated"\]\|"truncated":' src/mcp_connector/`.

**Doku:** Die drei READMEs zeigen `truncated` nur im `files_list`-Beispiel (`README.md:248`, `README.de.md:256`, `README.fr.md:261`). Kein Talk-Antwortbeispiel. Es gibt also keine README-Änderung für TOOL-17, nur den Changelog.

### TOOL-18: Id-Codec

| Ort | Zeile | Ist-Zustand | Soll |
|-----|-------|-------------|------|
| `src/mcp_connector/tools/mail.py` | 67-70 | `_ID_KIND = "mail"` mit dem Kommentar "Plan 10-05 is the one that adds `ids.encode_mail` ... until then" | Konstante samt Kommentar entfernen |
| `src/mcp_connector/tools/mail.py` | 490 | `"id": f"{_ID_KIND}{ids.SEPARATOR}{_number(raw.get('databaseId'))}"` | `"id": ids.encode_mail(_number(raw.get("databaseId")))` |
| `src/mcp_connector/ids.py` | 115-116 | `if kind == "url": return "url", (rest,)` vor dem gemeinsamen Leersegment-Check in `:161` | `rest.strip()` prüfen und mit dem bestehenden "not a valid resource id"-Satz ablehnen |

**Verhaltensgleichheit des Mail-Fixes ist belegt.** `tools/mail.py:441` filtert `_number(item.get("databaseId")) > 0`, bevor `_message` läuft, also erreicht nie eine 0 oder ein Nicht-Integer die Id-Bildung. `ids.encode_mail` ruft `_join`, das nur leere Segmente und Separatoren im Segment ablehnt; für jeden Wert, der den Filter passiert, ist die Ausgabe byte-identisch mit heute. Es bricht also kein bestehender Test. Der Gewinn ist der Vertrag, nicht eine Korrektur.

**Semantik-Fallstrick bei `ids.parse`.** ROADMAP und Requirements formulieren "Whitespace im Rest". Die konsistente Auslegung ist "der Rest besteht **nur** aus Whitespace", nicht "der Rest enthält irgendwo Whitespace":

- `encode_url` (`ids.py:100-105`) lehnt heute genau das ab: `(url or "").strip()` leer, also whitespace-only. Eine URL mit einem inneren Leerzeichen akzeptiert es.
- Der Review-Befund IN-04 nennt wörtlich `url:   ` als Fall und schlägt `rest.strip()` vor.
- Ein `parse`, das inneres Whitespace ablehnt, wäre strenger als `encode_url` und würde die Asymmetrie nur in die andere Richtung drehen. Der bestehende Test `test_url_keeps_colons_and_slashes` (`tests/unit/test_ids.py:176`) zeigt, dass die `url`-Art bewusst tolerant ist.

Empfehlung: whitespace-only ablehnen, und den Kommentar an der Stelle sagen lassen, warum inneres Whitespace erlaubt bleibt. Falls der Planner die strengere Lesart wählt, muss `encode_url` mitgezogen werden, sonst gibt es einen Wert, den der Codec baut und selbst nicht parst.

**Bestehende Tests, die die `url`-Art berühren:** `tests/unit/test_ids.py:30-31` (Roundtrip), `:46` (`encode_url`), `:167` (`url:` ohne Rest in der Liste der Präfix-Formen), `:176-178` (Doppelpunkte und Slashes bleiben), `:195` (`"url:"` in einer Ablehnungsliste), `:214` (`encode_url("")` lehnt ab). Der neue Negativtest gehört in dieselbe Datei, nach dem Muster der bestehenden Ablehnungsliste.

### TOOL-19: Modulgrenzen und das README-Beispiel

**Der eine echte Durchgriff:** `src/mcp_connector/tools/chatgpt.py:616`, `room = await talk_tools._room(clients, token, include_last_message=False)`. Bestätigt durch `ruff check --select SLF src/`: drei Treffer im ganzen Produktionsbaum, nämlich `oauth/provider.py:554` (`view._also` nach `copy.copy(self)`), `oauth/provider.py:1544` (`self._provider._now()`) und `tools/chatgpt.py:616`. Nur der letzte überschreitet eine Modulgrenze zwischen Tool-Familien.

**Aufrufer von `_room`, die beim Umbenennen mitziehen:** `tools/talk.py:291` (in `send`), `tools/talk.py:481` (in `_messages`), `tools/chatgpt.py:616`. Weitere Nennungen sind Prosa: `tools/talk.py:234` (Docstring), `11-SECURITY.md` T-11-12/T-11-14 (Belegzeilen, Dokument einer abgeschlossenen Phase).

**Namenswahl.** Das Modul hat für genau diesen Zweck schon einen Präzedenzfall: `one_message` (`tools/talk.py:531`) wurde in Phase 11 öffentlich gemacht, damit `chatgpt.py` sie aufrufen darf; ihr Docstring nennt den Aufrufer. Zwei konsistente Kandidaten:

- `one_room(clients, token, *, include_last_message)` folgt der Modul-Konvention `one_message`.
- `room_of(clients, token, *, include_last_message)` ist der wörtliche Vorschlag aus `11-REVIEW.md` IN-06.

Beide sind vertretbar. Wichtig ist in beiden Fällen: der Docstring von `_room` trägt heute die Sicherheitsbegründung (T-09-21: nie `GET /room/{token}` mit einem Token aus einer Modellantwort). Dieser Text muss mitwandern, denn er ist die halbe Mitigation von T-11-12 und T-11-14, und `11-SECURITY.md` zitiert die Zeile.

**Vulture:** `_room` steht nicht in `vulture_whitelist.py`. Eine öffentliche Funktion mit drei Aufrufern erzeugt keinen neuen Whitelist-Eintrag. Gegenprüfen mit `uv run --no-sync vulture src scripts vulture_whitelist.py`.

**Das README-Beispiel.** Drei identische Zeilen, `README.md:372`, `README.de.md:381`, `README.fr.md:389`. Zu ändern ist genau `"provider":"spreed"` zu `"provider":"talk-conversations"`. Warum das die richtige Id ist:

- `talk-conversations` ist eine echte Provider-Id (Talk meldet sie zur Laufzeit) und ist absichtlich **nicht** in `PROVIDER_KINDS` (Modul-Docstring `provider_map.py:42-43`: "a conversation is not a document, and `talk_browse` is the way to it").
- Der Test `test_a_talk_conversation_hit_stays_a_url_because_a_conversation_is_no_document` (`tests/unit/test_provider_map.py:288`) belegt für exakt diese Id `kind == "url"`, `canonical is False`. Die Beispielzeile behauptet `"kind":"url","resolvable":false` und wird damit wahr statt erfunden.
- `test_the_provider_table_is_not_a_list_of_installed_apps` (`:287-299`) friert die Menge ein und behauptet ausdrücklich `"talk-conversations" not in PROVIDER_KINDS`.
- `spreed` war nie eine Provider-Id; `tests/unit/test_provider_map.py:78-80` hält das schriftlich fest und hat die Zeile schon aus dem eigenen Testbeispiel entfernt. Das README ist die letzte Stelle, an der sie noch steht.

Der URL-Teil der Beispielzeile (`/index.php/call/abc123`) passt weiterhin, der Token `abc123` erfüllt das Token-Alphabet.

**Kein Test hält die README-Beispiele.** `tests/contract/test_tool_surface.py` liest `README.md` nur für die Tool-Tabelle (`:736-749`) und für Tool-Zahlen in `docs/*.md` (`:766`). Ein Beispiel mit falscher Provider-Id fällt heute keinem Gate auf. Wenn das Requirement das festnageln soll, wäre die billigste Form ein Test, der die drei READMEs nach `"provider":"<id>"` durchsucht und jede gefundene Id gegen `PROVIDER_KINDS` plus eine benannte Liste echter unregistrierter Ids prüft. Das ist nicht wörtlich gefordert (SC3 verlangt das Gate nur für den Privat-Durchgriff), aber es ist die Stelle, an der genau dieser Fehler zurückkehren kann.

### SEC-02(a): die zwei fehlenden Verifikationskommentare

Kommentarformat der vier vorhandenen Einträge (`provider_map.py:58-72`): eine oder mehrere `#`-Zeilen direkt über dem Eintrag, Form "Verified against nextcloud/<repo> <pfad>, class <Klasse>: <was der Code tut, das wir ausnutzen>". `search-deck-card-board` nennt Repo und Datei ohne Version, `talk-message` und `talk-message-current` nennen die Klasse und das Verhalten, `tables-search-tables` nennt zusätzlich die Link-Bauweise. Versionen stehen in benachbarten Kommentaren des Projekts (`tools/talk.py:126-129` nennt `nextcloud/server v34.0.0` und `spreed v24.0.4`), sind hier aber nicht durchgehend Konvention.

Für die zwei fehlenden Einträge liegen die Belege jetzt vor:

**`files`** [VERIFIED: raw.githubusercontent.com/nextcloud/server/v34.0.0/apps/files/lib/Search/FilesSearchProvider.php, gelesen 2026-08-25]
- Repo und Datei: `nextcloud/server`, `apps/files/lib/Search/FilesSearchProvider.php`, Tag `v34.0.0`.
- Klasse: `FilesSearchProvider implements IFilteringProvider`.
- `getId(): string { return 'files'; }` (Zeile 49-51 der Datei).
- `search()` setzt `addAttribute('fileId', (string)$result->getId())` und `addAttribute('path', $path)`, und der Link kommt aus `linkToRoute('files.View.showFile', ['fileid' => $result->getId()])`.
- Das ist genau die Doppelspur, die `_file_id` (`provider_map.py:176-188`) nutzt: `attributes.fileId` zuerst, sonst das `/f/<fileid>`-Segment der URL.

**`notes`** [VERIFIED: raw.githubusercontent.com/nextcloud/notes/v6.0.2/lib/AppInfo/SearchProvider.php und .../lib/AppInfo/Application.php, gelesen 2026-08-25]
- Repo und Datei: `nextcloud/notes`, `lib/AppInfo/SearchProvider.php`, Tag `v6.0.2` (aktuellstes Release).
- Klasse: `SearchProvider implements IProvider` (Zeile 22).
- `getId(): string { return Application::APP_ID; }` (Zeile 37-39), und `Application::APP_ID = 'notes'` (`lib/AppInfo/Application.php:28`).
- Der Provider setzt **keine** Attribute; der Link ist `linkToRouteAbsolute('notes.page.indexnote', ['id' => $note->getId()])`.
- Genau deshalb liest `provider_map.py:135-138` die Note-Id per `_last_numeric_segment(url)` statt aus Attributen. Der Kommentar sollte das sagen, weil es die Begründung für die abweichende Ableitung ist.

Beide Belege gelten für ein Tag, nicht für `master`/`main`, damit der Kommentar so überprüfbar bleibt wie die vier bestehenden.

### SEC-02(b): das Quelltext-Gate zu T-11-29

**Was der einmalige Prüfschritt war.** `11-05-SUMMARY.md` protokolliert unter "Verification Results" ein Quelltext-Gate über `context.py` mit mehreren Behauptungen, darunter die sicherheitsrelevante: `level="messages"` **kommt nicht vor**. Dazu: `mail_tools.browse` und `asyncio.timeout(MAIL_BUDGET)` vorhanden, `MAX_LIMIT` vorhanden, kein `AsyncClient`/`clients.client`/`clients.creds`/OCS-/DAV-Präfix. Der letzte Teil ist schon dauerhaft: `test_this_module_reads_no_content_of_its_own` (`tests/unit/test_tools_context.py:1815-1830`). Der Teil zu `level="messages"` ist es nicht.

**Heutiger Ist-Zustand, geprüft.** In `src/mcp_connector/tools/context.py` kommt das Wort "messages" fünfmal vor, und zwar ausschließlich in Docstrings und Kommentaren (`:36`, `:43`, `:348`, `:355`, `:593`). Als Code steht dort nur `level="accounts"` (`:352`) und `level="mailboxes"` (`:367`). Ein Gate auf die exakte Zeichenkette `level="messages"` ist also heute grün und trifft keine Prosa.

**Vorbild und Ort.** Der natürliche Ort ist direkt neben `test_this_module_reads_no_content_of_its_own` in `tests/unit/test_tools_context.py`, im gleichen Stil (Quelltext lesen, Zeilen die mit `#` beginnen filtern, dann behaupten). Für maximale Robustheit gegen Docstring-Prosa ist `_code_lines` aus `tests/contract/test_no_destructive_calls.py:293-320` das schärfere Muster (`ast` blendet Docstrings aus, `tokenize` die Kommentare). Für die eine Zeichenkette `level="messages"` genügt die einfache Variante, weil sie in Prosa nie in dieser Schreibweise auftaucht.

**Gegenprobe ist Projektkultur.** `tests/unit/test_exapp_env_setup.py:1670-1672` formuliert die Regel: "a gate nobody has seen fail is not a gate, so each one has a counter probe below that feeds it a manipulated manifest". Für ein Quelltext-Gate heißt das: die Prüffunktion so schneiden, dass ein Test sie mit einem manipulierten Text speisen kann (Parameter statt fest verdrahtetem `read_text`), oder eine zweite Behauptung gegen einen konstruierten String. `test_no_destructive_calls.py` löst das per gemeinsam genutzter `_violations`-Funktion und `test_the_gate_would_notice_a_destructive_call_in_real_code` (`:378`).

### SEC-02(c): Reichweite des Vokabular-Gates

**Ist-Zustand.** `FORBIDDEN_VOCABULARY = "archiv"` in `tests/unit/test_exapp_env_setup.py:1686`, angewendet in `description_problems` (`:1787-1789`) auf `element_text_without_comments(root)`, also ausschließlich auf den Element-Text von `appinfo/info.xml`. Zweiter, engerer Halter: `:1874` prüft die drei `description`-Sprachvarianten einzeln. Gegenprobe existiert: `test_the_text_gate_rejects_the_forbidden_vocabulary` (`:1942`).

**Trefferlage im ganzen Repo, ausgezählt.** Über alle Markdown-Dateien (Wurzel und `docs/`, ohne `.planning/`) trägt genau eine Datei das Wort: `docs/store-submission.md`, in zehn Zeilen (`47`, `124`, `125`, `190`, `204`, `222`, `244`, `281`, `318`, `349`). `README.md`, `README.de.md`, `README.fr.md`, `CHANGELOG.md`, `CLAUDE.md` und die vierzehn anderen `docs/*.md` sind sauber. Die vom Requirement geforderte Ausweitung ist damit bei Einführung grün, und die Gegenprobe muss aus einem konstruierten Text kommen, nicht aus einer echten Datei.

**Warum eine begründete Ausnahme die konsistentere Wahl ist als eine Bereinigung.** Drei der zehn Zeilen lassen sich nicht sinnvoll umschreiben:
- `:124` und `:125` sind **datierte Proof-Zeilen** in der Nachweistabelle. Die Projektkultur behandelt Proof-Zeilen als Protokoll: `11-SECURITY.md` führt T-11-63 ausdrücklich als Bedrohung "Proof-Zeile vor ihrem Ereignis geschrieben" und belegt, welcher Commit welche Zeile geschrieben hat. Eine nachträgliche Umformulierung eines Protokolls ist genau die Art von Rückschreibung, gegen die dieses Register gebaut ist.
- `:281` nennt `ExAppArchiveFetcher`, einen Klassennamen aus dem Nextcloud-Serverquelltext. Der ist nicht umbenennbar, ohne die Aussage falsch zu machen.

Die sieben restlichen Zeilen sind Runbook-Prosa und könnten "release tarball" oder "store tarball" heißen. Eine halbe Bereinigung plus Ausnahme für drei Zeilen ist mehr Regelfläche als eine Datei-Ausnahme mit Begründung. Empfehlung: `docs/store-submission.md` als benannte interne Ausnahme führen, mit der Begründung im Docstring des Gates (interne Release-Dokumentation, reist nicht im Store-Archiv, trägt datierte Protokollzeilen und einen fremden Klassennamen) und mit einer positiven Behauptung darüber, was das Store-Archiv enthält: `scripts/build_store_release.sh:44` kopiert `appinfo/info.xml`, `CHANGELOG.md`, `LICENSE` und `README.md` in das Archiv, und alle vier sind sauber. Das macht die Ausnahme prüfbar statt bequem.

**Wo das erweiterte Gate wohnen kann, und der Haken dabei.** Das Repo hat `--import-mode=importlib` und keine `__init__.py` im Testbaum; es gibt heute keinen einzigen Test-zu-Test-Import (per grep bestätigt). Eine gemeinsam genutzte Konstante zwischen zwei Testdateien ist damit nicht auf dem üblichen Weg zu haben. Drei Optionen:

1. **Gate in derselben Datei** (`tests/unit/test_exapp_env_setup.py`): eine Wortliste, ein Ort, keine zweite Wahrheit. Kostet thematische Unschärfe (die Datei heißt nach dem ExApp-Env-Setup, prüft dann aber Markdown der Wurzel).
2. **Neuer Halter in `tests/contract/`** (etwa `test_public_vocabulary.py`) und die Konstante zieht dorthin; `test_exapp_env_setup.py` behält seinen Manifest-Check und liest die Wortliste nicht mehr. Dann steht das Wort an zwei Stellen, was der IN-03-Fix-Logik des Projekts widerspricht ("a count in this sentence would be a second truth").
3. **Neuer Halter, der `appinfo/info.xml` mitprüft**, und der Manifest-Check in `test_exapp_env_setup.py` verweist per Docstring auf ihn statt selbst zu prüfen. Eine Wahrheit, thematisch saubere Datei, aber Umbau an einem grünen Gate.

Option 1 ist die kleinste Änderung, Option 3 die sauberste. Beide sind mit den Success Criteria vereinbar. `tests/contract/test_tool_surface.py:766` zeigt das Muster für einen repo-weiten Markdown-Lauf (`[*sorted(DOCS.glob("*.md")), README]`) und ist die Vorlage für die Dateiliste.

## Architecture Patterns

### Pattern 1: Umbenennung eines Antwortschlüssels nach dem Vorbild `53ba602`

**What:** Der Vorbild-Commit für TOOL-17 existiert und ist vollständig lesbar (`git show 53ba602`). Er hat vier Dinge gleichzeitig getan, und alle vier sind für Talk anwendbar.
**When to use:** TOOL-17, vollständig.
**Muster:**

1. **Projektionsstelle** (`tools/mail.py:502-509`): der neue Schlüssel plus ein Kommentar, der die zwei Bedeutungen nebeneinander stellt und den Review-Befund nennt. Der Kommentar erklärt nicht die Umbenennung, sondern warum der alte Name nicht auflösbar war: "a cut page whose first entry carries a cut preview sets both keys at once".
2. **Refusal-Hint** (`tools/mail.py:89-92`): der `_CURSOR_HINT` sagt jetzt "page was cut" und nennt den anderen Schlüssel in Klammern. Für Talk ist das optional, weil der Talk-Hint über die Konversationsliste spricht.
3. **Tool-Docstring** (`server/reg_mail.py:75-81`) plus ein Absatz im Modul-Docstring (`:30-36`), der die Byte-Ausgabe rechtfertigt: "that is the one sentence of it that buys itself back ... a model that reads the entry level flag as a page flag pages in a circle, which costs more round trips than the fifty odd bytes this sentence occupies".
4. **Tests** (`tests/unit/test_mail_tools.py:508-547`): der bestehende Kappungstest wechselt den Schlüssel und behauptet zusätzlich `"truncated" not in entry`; dazu ein **neuer** Test, in dem beide Flags gleichzeitig gesetzt sind, mit vier Behauptungen (Seite gekappt, `next` vorhanden, `preview_truncated` nicht auf Antwortebene, `truncated` nicht auf Eintragsebene, ein unbeschnittener Eintrag trägt gar nichts).

**Für Talk zusätzlich nötig, was Mail nicht brauchte:** der Verbraucher in `tools/chatgpt.py:653` muss mitziehen. Mail hatte keinen zweiten Leser der Eintragsebene.

### Pattern 2: Quelltext-Gate mit ausgeblendeten Kommentaren und Docstrings

**What:** `tests/contract/test_no_destructive_calls.py::_code_lines` (`:293-320`) parst die Datei mit `ast`, blankt die Docstring-Zeilen von `Module`, `ClassDef`, `FunctionDef` und `AsyncFunctionDef`, und schneidet dann per `tokenize` jede `COMMENT`-Position ab. Zurück kommen `(zeilennummer, text)`-Paare, sodass jeder Fund Datei und Zeile nennt.
**When to use:** TOOL-19 (Privat-Durchgriff-Gate) und SEC-02(b), falls die schärfere Variante gewählt wird.
**Warum hier zwingend:** `tools/context.py` nennt in Prosa `mail_tools._mailboxes` (`:340`), `mail_tools._messages` (`:355`), `mail_tools._special_role` (`:394`) und `mcp_connector.tools.talk._conversation` (`:605`). Ein Grep-Gate wäre sofort rot, und die naheliegende Reparatur wäre, die erklärenden Sätze zu löschen. Genau davor warnt der Modul-Docstring des Vorbilds: "the usual repair is to delete the sentence, which trades documentation for a green check".
**Zuschnitt für TOOL-19:** Die Regel ist "kein Tool-Modul ruft eine `_`-präfixte Funktion eines fremden Tool-Moduls". Als AST-Prüfung: über die Dateien in `src/mcp_connector/tools/` laufen, `ast.Attribute`-Knoten sammeln, deren `attr` mit `_` beginnt und deren `value` ein `ast.Name` ist, der über `import ... as`/`from .. import x as y` auf ein anderes Modul aus `tools/` zeigt. Die Import-Aliase sind im Repo einheitlich (`from ..tools import talk as talk_tools`, `mail as mail_tools`, `tables as tables_tools`), also ist die Alias-Auflösung über die `Import`/`ImportFrom`-Knoten derselben Datei zuverlässig. `self._x` und modul-interne `_helper()`-Aufrufe werden vom Muster nicht getroffen, weil sie keine `Attribute` auf einem Modul-Alias sind.
**Gegenprobe:** eine konstruierte Quelle mit `talk_tools._room(...)` durch die Prüffunktion schicken und einen Fund erwarten, plus der Positivlauf über das echte `src/`.

### Pattern 3: Eine öffentliche Funktion mit dem Aufrufer im Docstring

**What:** `talk.one_message` (`tools/talk.py:531-556`) ist der Präzedenzfall. Sie ist öffentlich, weil `chatgpt.py` sie braucht, und ihr Docstring erklärt Rückgabewert, Sicherheitsgrund ("Never a neighbour", T-11-13) und was sie absichtlich nicht wiederholt.
**When to use:** TOOL-19, beim Freilegen von `_room`.
**Konkret:** Der Docstring von `_room` trägt die Mitigation von T-09-21 (nie `GET /room/{token}` mit einem Token aus einer Modellantwort, die Liste kostet denselben einen Request und trägt keinen Token im Pfad). Dieser Text ist in `11-SECURITY.md` als Beleg für T-11-12 und T-11-14 zitiert. Er muss vollständig mitwandern, und die neue Signatur sollte `include_last_message` als Keyword-only behalten, damit die drei Aufrufstellen unverändert lesbar bleiben.

### Anti-Patterns to Avoid

- **Den Verbraucher vergessen.** Wer `talk.py:525` umbenennt und `chatgpt.py:653` stehen lässt, produziert einen `fetch`, der eine gekappte Nachricht nicht mehr als gekappt meldet. Das ist stiller Informationsverlust an das Modell, und `tests/unit/test_chatgpt_fetch.py:1302` fängt es zwar, aber nur wenn der Test nicht mit angepasst wird.
- **Die Wortliste duplizieren.** Zwei Stellen mit `"archiv"` sind zwei Wahrheiten. Das Projekt hat diesen Fehler in IN-03 benannt und behoben ("a count in this sentence would be a second truth that the next switch makes wrong without a single test noticing").
- **Ein Gate ohne Gegenprobe.** `tests/unit/test_exapp_env_setup.py:1670` formuliert die Regel wörtlich. Jedes der drei neuen Gates dieser Phase (Privat-Durchgriff, T-11-29-Quelltext, Vokabular-Reichweite) braucht eine.
- **Proof-Zeilen umschreiben.** `docs/store-submission.md:124-125` sind datierte Protokollzeilen. Sie zu editieren, um ein Gate grün zu bekommen, dreht die Beweisrichtung um.
- **Prosa löschen, um ein Grep-Gate zu befriedigen.** Siehe Pattern 2.
- **Das Budget-Gate anheben.** `scripts/check_tool_budget.py:83` erlaubt Anhebung nur zusammen mit einer neuen Messzeile. SC5 verbietet sie ohnehin, und die Messung zeigt, dass sie unnötig ist.

## Byte-Budget: Messung statt Vermutung

Ausgangsmessung heute, `uv run --no-sync python scripts/check_tool_budget.py`:

```
tools/list: 15657 bytes, 21 tools, budget 18000
  mail_browse: 1376 bytes
  calendar_create_event: 1351 bytes
  calendar_list_events: 951 bytes
  search: 924 bytes
  deck_create_card: 877 bytes
```

`talk_browse` ist nicht unter den fünf Größten. Einzelmessung über `Client(mcp).list_tools()` mit demselben Serialisierungsverfahren wie das Gate (`json.dumps(separators=(",",":"), ensure_ascii=False)`, dann `len(...encode("utf-8"))`):

| Werkzeug | Bytes heute | Ceiling | Luft |
|----------|-------------|---------|------|
| `talk_browse` | 858 | 1400 | 542 |
| `mail_browse` | 1376 | 1400 | 24 |
| Oberfläche gesamt | 15657 | 18000 | 2343 |

Der Vorbild-Satz aus `mail_browse` lautet ` truncated: page cut; preview_truncated: preview cut.` Die Talk-Entsprechung ` truncated: page cut; message_truncated: message cut.` ist 53 ASCII-Zeichen, also 53 Bytes; ein zusätzlicher Zeilenumbruch im Docstring kostet im JSON zwei weitere (`\n`). Erwartete Werte danach: `talk_browse` rund 911 Bytes (65 Prozent des Ceilings), Oberfläche rund 15710 Bytes (87 Prozent des Budgets).

**Konsequenz für die Planung:** Keine Gegenkompression nötig, kein Byte-Handel mit anderen Werkzeugen, kein Risiko für SC5. Anders als beim `mail_browse`-Fix, wo die Filterzeile im selben Edit gekürzt werden musste, weil nur 24 Bytes Luft waren. Die Messung nach dem Edit gehört trotzdem in die Verifikation jedes Plans, der `reg_talk.py` anfasst.

**Was keine `tools/list`-Bytes kostet:** Modul-Docstrings in `tools/talk.py`, Kommentare, `_CURSOR_HINT` und andere Refusal-Texte, alles in `tests/`. Nur der Tool-Docstring in `server/reg_talk.py` und die `Field(description=...)`-Texte reisen in der Oberfläche.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Kommentare und Docstrings vor einer Quelltextsuche ausblenden | Eigene Zeilenfilter mit `startswith("#")` für den Docstring-Fall | `_code_lines` aus `tests/contract/test_no_destructive_calls.py:293-320` (Muster übernehmen) | Der einfache Filter erwischt Docstrings nicht, und `context.py` nennt private Fremdfunktionen in Docstrings |
| Id-String bauen | `f"mail{ids.SEPARATOR}{...}"` | `ids.encode_mail(...)` | Genau der Vertrag, den TOOL-18 herstellt. Der Codec bringt Leersegment- und Separator-Refusal mit |
| Byte-Kosten schätzen | Zeichen zählen im Kopf | `scripts/check_tool_budget.py` und die Einzelmessung über `Client(mcp).list_tools()` | Das Gate zählt UTF-8-Bytes des serialisierten `tools/list`, inklusive `title`-Keys und JSON-Escapes; eine Schätzung auf Zeichenbasis war bis 2026-08-21 genau der Fehler, den `MAX_TOOL_BYTES` behoben hat |
| Privatzugriffe finden | Eigener Grep über `\._[a-z]` | `ruff check --select SLF src/` für die Bestandsaufnahme, AST-Gate für die Durchsetzung | Ruff gibt die vollständige Liste ohne False Positives aus Kommentaren; gemessen: 3 Treffer in `src/`, 53 in `tests/` |
| Provider-Ids raten | Aus dem Gedächtnis in den Kommentar schreiben | Datei am Release-Tag lesen (`raw.githubusercontent.com/<repo>/<tag>/<pfad>`) | Der Zweck des Kommentars ist der Beweis. `search-deck-card-board` statt `deck` ist der Präzedenzfall dafür, dass die naheliegende Id falsch ist |

**Key insight:** Diese Phase baut nichts Neues, sie räumt vier Stellen auf, an denen dasselbe Prinzip zweimal verkörpert war. Für jede der vier gibt es im Repo bereits einen erfolgreichen Präzedenzfall (`preview_truncated`, `ids.encode_message`, `one_message`, `test_no_destructive_calls.py`). Der Plan sollte diese Präzedenzfälle namentlich zitieren, statt eigene Lösungen zu erfinden.

## Common Pitfalls

### Pitfall 1: Die Umbenennung bricht `fetch` still
**What goes wrong:** `tools/chatgpt.py:653` liest `entry.get("truncated")` aus der `talk._message`-Projektion. Nach der Umbenennung ist der Schlüssel weg, `entry.get("truncated")` ist `None`, und `metadata["truncated"]` wird nie gesetzt: eine bei 800 Bytes gekappte Nachricht kommt beim Modell als vollständig an.
**Why it happens:** Die Projektion und ihr zweiter Leser liegen in verschiedenen Dateien, und `entry.get(...)` wirft nicht.
**How to avoid:** `chatgpt.py:653` im gleichen Task ändern wie `talk.py:525`. `tests/unit/test_chatgpt_fetch.py:1302` (`result["metadata"]["truncated"] == "true"`) ist der Wächter; er darf nicht "angepasst" werden, ohne dass der Produktionscode mitzieht.
**Warning signs:** `test_chatgpt_fetch.py` wird rot bei einer Änderung, die nur `talk.py` anfasst. Das ist das System, das funktioniert, nicht das Problem.

### Pitfall 2: Das Privat-Durchgriff-Gate wird rot wegen Prosa
**What goes wrong:** Ein Grep über `src/mcp_connector/tools/` nach `_[a-z]+\(` hinter einem Modul-Alias findet die vier Prosa-Nennungen in `context.py` (`:340`, `:355`, `:394`, `:605`) und wird sofort rot.
**Why it happens:** Das Projekt erklärt Entscheidungen mit dem Namen der Funktion, auf die es sich bezieht. Das ist gewollt und dokumentiert.
**How to avoid:** AST-basiert prüfen, oder `_code_lines` vorschalten. Nie die erklärenden Sätze löschen.
**Warning signs:** Der erste rote Lauf zeigt Treffer in `context.py`, obwohl `context.py` keine fremde Privatfunktion aufruft.

### Pitfall 3: `ids.parse` wird strenger als `ids.encode_url`
**What goes wrong:** Wenn `parse` jedes Whitespace im Rest ablehnt, entsteht ein Wert, den `encode_url` baut und `parse` nicht mehr liest (eine URL mit innerem Leerzeichen). Der Roundtrip-Vertrag des Moduls ("encoded and parsed in exactly one place") bricht in die andere Richtung.
**Why it happens:** Der Requirement-Wortlaut "Whitespace im Rest" ist zweideutig.
**How to avoid:** Whitespace-only ablehnen (`not rest.strip()`), spiegelbildlich zu `encode_url`. Falls die strengere Lesart gewollt ist, `encode_url` im gleichen Task mitziehen und einen Roundtrip-Test für die Grenze schreiben.
**Warning signs:** `tests/unit/test_ids.py:176` (`test_url_keeps_colons_and_slashes`) oder `:30-31` (Roundtrip) werden rot.

### Pitfall 4: Ein neues Gate ohne Gegenprobe, das nie gefeuert hat
**What goes wrong:** Das erweiterte Vokabular-Gate ist bei Einführung grün, weil keine der geprüften Dateien das Wort trägt. Ein Tippfehler im Pfad oder eine leere Dateiliste bleibt unbemerkt, und das Gate schützt nichts.
**Why it happens:** Grün fühlt sich wie Erfolg an. Beim Manifest-Gate war der erste Lauf ebenfalls grün, weshalb die Datei ihre Gegenproben-Regel überhaupt formuliert.
**How to avoid:** Prüffunktion so schneiden, dass sie einen Text als Parameter nimmt; ein Test speist einen konstruierten Text mit dem Wort und erwartet einen Fund, ein zweiter behauptet, dass die Dateiliste nicht leer ist (Muster `_source_files()`: `assert files, f"no production sources found under {SRC}"`).
**Warning signs:** Der neue Test hat keinen Partner, der ihn scheitern sieht.

### Pitfall 5: Die falsche Datei für `_ID_KIND` suchen
**What goes wrong:** `REQUIREMENTS.md` und die Phasenbeschreibung nennen `tools/chatgpt.py`. Dort steht kein `_ID_KIND`. Ein Plan, der die Datei wörtlich übernimmt, findet nichts und deklariert das Requirement als erledigt oder als nicht reproduzierbar.
**Why it happens:** Die IN-Nummern und Dateiangaben in den v1.3-Requirements sind gegen `11-REVIEW.md` verschoben.
**How to avoid:** `grep -rn "_ID_KIND" src/` als erste Handlung des Tasks. Die Prosa des Requirements ist normativ, die Dateiangabe nicht.
**Warning signs:** Der Plan nennt `tools/chatgpt.py` in `files_modified` für TOOL-18 statt `tools/mail.py`.

### Pitfall 6: `docs/store-submission.md` bereinigen und die Beweislage beschädigen
**What goes wrong:** Zehn Textersetzungen im Runbook treffen zwei datierte Proof-Zeilen und einen Nextcloud-Klassennamen. Die Proof-Zeilen sind das Protokoll, gegen das `11-SECURITY.md` T-11-63 und T-11-71 prüft.
**Why it happens:** "Bereinigen" klingt sauberer als "Ausnahme".
**How to avoid:** Ausnahme mit Begründung, plus eine positive Behauptung darüber, was im Store-Archiv liegt (`scripts/build_store_release.sh:44`: `info.xml`, `CHANGELOG.md`, `LICENSE`, `README.md`, alle vier sauber).
**Warning signs:** Ein Diff in `docs/store-submission.md` berührt eine Zeile mit einem Zeitstempel in `Z`.

## Runtime State Inventory

Diese Phase ist eine Umbenennung, daher wird die Inventur ausdrücklich geführt.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | **Keine.** Der Server hält keinen Zustand über Antwortschlüssel. `truncated`/`message_truncated` entstehen bei jeder Antwort neu aus der Projektion; die Cursor-Handles (`paging.encode_cursor`) tragen nur `o`, `c`, `m`, `t` und keinen Kappungsschlüssel (verifiziert per `grep -rn "truncated" src/mcp_connector/paging.py`, nur ein Docstring-Treffer). Kein OAuth-Token, kein Store-Eintrag referenziert einen Antwortschlüssel. | keine |
| Live service config | **Keine.** Es gibt keine externe Konfiguration, die `truncated` oder `_room` nennt. Was ein Client zwischenspeichert, ist die `tools/list`-Antwort, und die enthält nur den Docstring, nicht den Antwortschlüssel; ein Client mit persistierter Tool-Liste sieht den neuen Satz nach seiner nächsten Auffrischung (dieselbe Lage wie beim 0.1.8-Fix, dort in `11-05-SUMMARY.md` unter "User Setup Required" protokolliert). | keine, aber in die Changelog-Zeile aufnehmen |
| OS-registered state | **Keine.** Kein Task Scheduler, kein pm2, kein systemd in diesem Projekt. Das Artefakt ist ein Docker-Image plus `appinfo/info.xml`. | keine |
| Secrets/env vars | **Keine.** Die deklarierten Umgebungsvariablen werden von `test_every_variable_the_code_reads_is_declared_in_the_manifest` (`tests/unit/test_exapp_env_setup.py`) als Mengengleichheit gehalten; keine von ihnen heißt nach einem Antwortschlüssel oder nach `_room`. Diese Phase fügt keine hinzu und entfernt keine. | keine |
| Build artifacts | **Nur lokale `__pycache__`.** Kein Paket-Rename, kein `egg-info`, keine `pyproject.toml`-Änderung, kein neues Image-Tag in dieser Phase (das Release ist Phase 13). Die `.pyc`-Dateien im Arbeitsbaum sind von pytest verwaltet. | keine |

**Nutzersichtbare Fläche der Umbenennung:** genau ein Schlüssel in genau einer Antwort (`talk_browse(level="messages")`, Eintragsebene). Das deckt sich mit SC5 ("die einzige nutzersichtbare Änderung ist der umbenannte Nachrichten-Schlüssel").

## Betroffene Tests

| Datei | Zeile | Heute | Nach der Phase |
|-------|-------|-------|----------------|
| `tests/unit/test_talk_tools.py` | 726 | `assert entry["truncated"] is True` (Byte-Kappung bei 800, Umlaut an der Grenze) | `entry["message_truncated"] is True` plus `"truncated" not in entry` |
| `tests/unit/test_talk_tools.py` | 730 | `assert "truncated" not in json.dumps(entry["message"])` | unverändert (Marker-Hygiene, ME-03) |
| `tests/unit/test_talk_tools.py` | 361, 530, 630, 655 | Antwortebene (`conversations` und `messages`) | unverändert; `:630` (`"truncated" not in result` bei 304) und `:655` (leeres Fenster mit Fortsetzung) sind die Wächter dafür, dass die Antwortebene nicht mitwandert |
| `tests/unit/test_talk_tools.py` | neu | - | Test für den gemeinsamen Fall: gekappte Seite **und** gekappte Nachricht, vier Behauptungen nach dem Muster `test_mail_tools.py:522-547` |
| `tests/unit/test_chatgpt_fetch.py` | 1302 | `result["metadata"]["truncated"] == "true"` | unverändert, aber nur wenn `chatgpt.py:653` mitzieht |
| `tests/unit/test_ids.py` | 30-31, 46, 167, 176-178, 195, 214 | `url`-Roundtrip und Ablehnungslisten | unverändert; neuer Negativtest für `url:   ` |
| `tests/unit/test_mail_tools.py` | alle | Id-Erzeugung über `_ID_KIND` implizit geprüft | unverändert (byte-identische Ausgabe, siehe TOOL-18-Abschnitt) |
| `tests/unit/test_provider_map.py` | 78-80, 287-299 | `spreed` war nie eine Provider-Id; Mengen-Freeze inklusive `"talk-conversations" not in PROVIDER_KINDS` | unverändert; sie sind der Beleg für die README-Korrektur |
| `tests/unit/test_tools_context.py` | 1616-1645 | T-11-29-Verhaltenstest (`mail.of("messages") == []`) | unverändert; daneben kommt das neue Quelltext-Gate |
| `tests/unit/test_tools_context.py` | 1815-1830 | `test_this_module_reads_no_content_of_its_own` | Vorbild und Nachbar des neuen Gates |
| `tests/unit/test_exapp_env_setup.py` | 1686, 1787-1789, 1942 | Vokabular-Gate über den Manifest-Text plus Gegenprobe | erweitert oder verlagert, siehe SEC-02(c) |
| `tests/contract/test_tool_surface.py` | 327-351 | `talk_browse`-Contract (Annotationen, Enum, kein `$defs`) | unverändert; prüft den Docstring-Wortlaut nicht, also bricht der neue Satz nichts |
| `tests/contract/` | neu | - | Privat-Durchgriff-Gate plus Gegenprobe (Vorschlag: `test_module_boundaries.py`) |

## Code Examples

### Die Projektionsstelle in Talk, nach dem Mail-Vorbild

```python
# Quelle: das Muster steht in src/mcp_connector/tools/mail.py:500-509 (Commit 53ba602),
# die Zielstelle ist src/mcp_connector/tools/talk.py:524-525
    if cut:
        # ``message_truncated`` and not ``truncated``, and the difference is the whole
        # point: one level up, ``truncated`` means "this window was cut and there is a
        # ``next``", down here it means "this message was cut at MAX_MESSAGE_BYTES". A cut
        # window whose first entry carries a cut message sets both keys at once, so a model
        # reading the entry level flag as a page flag pages in a circle (DF-11-01, the same
        # finding IN-01 named for mail_browse).
        entry["message_truncated"] = True
```

### Der Frühausstieg in `ids.parse`

```python
# Quelle: src/mcp_connector/ids.py:115-116 (Ist-Zustand)
    if kind == "url":
        return "url", (rest,)
```

Der gemeinsame Leersegment-Check steht erst in `:161-162` und wird von diesem `return` übersprungen. `encode_url` (`:100-105`) lehnt denselben Wert bereits ab, die Asymmetrie ist also einseitig.

### Das Alias-Muster, das ein AST-Gate auflösen muss

```python
# Quelle: src/mcp_connector/tools/chatgpt.py (Importblock) und :616
from ..tools import talk as talk_tools
...
    room = await talk_tools._room(clients, token, include_last_message=False)
```

`ruff check --select SLF src/` bestätigt diese Stelle als einen von drei Treffern im Produktionsbaum; die anderen zwei (`oauth/provider.py:554` und `:1544`) sind Zugriffe auf eigene Klassen-Interna innerhalb desselben Moduls.

### Der Verifikationskommentar, dem `files` und `notes` folgen sollen

```python
# Quelle: src/mcp_connector/provider_map.py:69-72 (bestehendes Format)
    # Verified against nextcloud/tables lib/Search/SearchTablesProvider.php, class
    # SearchTablesProvider: it sets no attributes at all, and getInternalLink builds
    # "#/" . $nodeType . "/" . $nodeId with $nodeType being "table" or "view".
    "tables-search-tables": "table",
```

Belegzitate für die zwei fehlenden Einträge, beide in dieser Recherche am Release-Tag gelesen:

```php
// nextcloud/server v34.0.0, apps/files/lib/Search/FilesSearchProvider.php
class FilesSearchProvider implements IFilteringProvider {
    public function getId(): string { return 'files'; }
    // ... $searchResultEntry->addAttribute('fileId', (string)$result->getId());
    //     $searchResultEntry->addAttribute('path', $path);
    //     linkToRoute('files.View.showFile', ['fileid' => $result->getId()])
```

```php
// nextcloud/notes v6.0.2, lib/AppInfo/SearchProvider.php
class SearchProvider implements IProvider {
    public function getId(): string { return Application::APP_ID; }   // 'notes'
    // ... new SearchResultEntry('', $note->getTitle(), $excerpt,
    //         $this->url->linkToRouteAbsolute('notes.page.indexnote', ['id' => $note->getId()]),
    //         'icon-notes-trans');   // keine Attribute, daher liest provider_map die Id aus der URL
```

### Der Changelog-Eintrag, dem der 0.1.9-Text folgen sollte

```markdown
<!-- Quelle: CHANGELOG.md:65-72, der 0.1.8-Eintrag zu preview_truncated -->
### Changed

- A change of the answer format, named here because a reader of the old key has to be
  updated: in an answer of `mail_browse` on the message level, the key `truncated` of a
  single entry is now called `preview_truncated`. ...
```

Für 0.1.9 ist die Entsprechung: `talk_browse` auf der Nachrichtenebene, Eintragsschlüssel `truncated` heißt `message_truncated`, die Antwortebene behält `truncated` mit `next` daneben, kein anderes Werkzeug ist betroffen. `CHANGELOG.md` hat heute keinen `Unreleased`-Block und kein Gate, das den obersten Versionsblock gegen `mcp_connector.__version__` hält (per grep über `tests/`, `scripts/` und `.github/workflows/` bestätigt), ein 0.1.9-Block in Phase 12 bricht also nichts.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `uv` | Jeder Verifikationsbefehl | ja | im Projekt eingerichtet, `uv run --no-sync` läuft | keiner nötig |
| pytest | Alle Gates | ja | Lauf über 8 Dateien: 588 passed in 19,14s | - |
| ruff | Lint, optional `SLF`-Bestandsaufnahme | ja | `ruff check --select SLF` lief | - |
| pyright | Typprüfung | ja (deklariert, `typeCheckingMode = "standard"`) | - | - |
| vulture | Toter Code nach dem Umbenennen | ja (deklariert, läuft in CI) | - | - |
| `scripts/check_tool_budget.py` | SC5 | ja | Lauf: 15657 Bytes, 21 Werkzeuge, Exit 0 | - |
| Netzzugriff auf raw.githubusercontent.com | SEC-02(a), Verifikation der Provider-Klassen | ja | beide Dateien gelesen | Belege stehen in dieser Datei, der Plan braucht das Netz nicht erneut |
| Docker / laufende Nextcloud | - | nicht nötig | - | Diese Phase braucht keinen Integrationslauf; `-m 'not integration and not matrix'` ist der Default |
| GitHub-API (`gh api`) | Auffinden des Notes-Release-Tags | ja | `v6.0.2` ermittelt | - |

**Missing dependencies with no fallback:** keine.

## Security Domain

SEC-02 ist selbst ein Sicherheits-Requirement; diese Phase erweitert keine Angriffsfläche.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | nein | Diese Phase berührt keinen Auth-Pfad. `oauth/provider.py` wird nur angefasst, falls der Planner die `SLF`-Lint-Variante wählt (zwei `noqa`-Kommentare, kein Logikwechsel) |
| V3 Session Management | nein | - |
| V4 Access Control | mittelbar | `_room` ist die Mitigation von T-09-21/T-11-12/T-11-14 (Berechtigungsdurchgriff über die eigene Konversationsliste statt `GET /room/{token}`). Beim Umbenennen muss die Begründung im Docstring erhalten bleiben, sonst verliert das Register seinen Beleg |
| V5 Input Validation | ja | `ids.parse` ist die Eingangsprüfung für jede Id aus einer Modellantwort. Der `url:`-Fix schließt die letzte Inkonsistenz gegenüber `encode_url`. Muster: Refusal vor jedem Request, `_DIGITS`/`_TOKEN`-`fullmatch` |
| V6 Cryptography | nein | - |
| V14 Configuration | ja | Die drei neuen Gates sind Konfigurations- und Quelltextprüfungen; sie laufen in CI über `pytest tests/unit tests/contract` |

### Known Threat Patterns für diese Phase

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Umbenennung entfernt still eine Kappungsangabe (`fetch` meldet gekappten Fremdtext als vollständig) | Information Disclosure | `chatgpt.py:653` im gleichen Task mitziehen; `test_chatgpt_fetch.py:1302` als Wächter |
| Zweiter Id-Bauer umgeht die Codec-Refusals | Tampering | `ids.encode_*` als einzige Quelle; Negativtest je Weg |
| Privater Fremdaufruf bricht bei einem Refactoring in `talk.py` und nimmt die T-09-21-Mitigation mit | Elevation of Privilege | Öffentlicher Name plus Gate; Sicherheitsbegründung wandert mit dem Docstring |
| Prosa-Löschung, um ein Grep-Gate grün zu bekommen | Repudiation | AST-basiertes Gate (Kommentare und Docstrings ausgeblendet), Muster aus `test_no_destructive_calls.py` |
| Regel ohne Durchsetzung (UF-1 bis UF-3) | Repudiation | Kommentar als Beleg, Regressionstest statt einmaligem Prüfschritt, Gate-Reichweite an die Regelformulierung angeglichen oder Regelformulierung an die Reichweite |
| Proof-Zeile nachträglich umgeschrieben | Repudiation | `docs/store-submission.md` als benannte Ausnahme, nicht als Bereinigungsziel |

Alle 74 Registereinträge aus Phase 11 sind `closed`; diese Phase löst keinen davon wieder auf, sondern schließt die vier `UF`-Abweichungen (UF-1, UF-2, UF-3) und die zwei sicherheitsnahen deferred Infos (IN-04, IN-06 aus `11-SECURITY.md`, "Unregistered Flags" Punkt 7).

## Diskrepanzen zwischen Requirements und Quelltext

Der Planner sollte diese vier Abweichungen kennen, bevor er Tasks schneidet. Die Prosa der Requirements ist in allen vier Fällen richtig, die Verweise sind es nicht.

| Requirement sagt | Quelltext sagt | Konsequenz |
|------------------|----------------|------------|
| TOOL-18: "`_ID_KIND`-Workaround in `tools/chatgpt.py`" | `_ID_KIND` steht in `tools/mail.py:70`, benutzt in `:490`. In `chatgpt.py` existiert kein `_ID_KIND` | `files_modified` für TOOL-18 nennt `tools/mail.py`, nicht `chatgpt.py` |
| TOOL-18: "(IN-05)" für `_ID_KIND`, "(IN-06)" für `ids.parse` | `11-REVIEW.md` führt `_ID_KIND` als **IN-01** und `ids.parse`/`url` als **IN-04** | Beim Zitieren von Review-Nummern in Kommentaren die REVIEW-Nummern verwenden, sonst zeigt der Kommentar auf einen anderen Befund |
| TOOL-19: "(IN-Reste aus 11-REVIEW.md)" | `spreed` ist IN-05, `talk_tools._room` ist IN-06 | Diese beiden stimmen inhaltlich, nur die Nummern in TOOL-18 sind belegt |
| TOOL-17: "Muster von IN-01/`preview_truncated` in Mail" | `preview_truncated` ist im Review als IN-01 geführt und in Commit `53ba602` umgesetzt; derselbe Commit trägt auch den IN-03-Fix | Das genannte Muster existiert und ist der richtige Bezug. `git show 53ba602` ist die vollständige Vorlage |

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Ein Wort (`truncated`) für Seiten- und Eintragskappung | Ein Wort je Bedeutung (`truncated` / `preview_truncated`) | 2026-08-25, Commit `53ba602`, Release 0.1.8 | Talk ist die letzte Familie, die dem Muster noch nicht folgt |
| Id-Präfix aus `SEPARATOR` von Hand gebaut | `ids.encode_*` als einzige Quelle | Plan 10-05 (`encode_mail`), Plan 11-01 (`encode_message`, `encode_table`) | Der `_ID_KIND`-Kommentar in `mail.py` beschreibt einen Zustand, der seit Plan 10-05 vorbei ist |
| Privater Fremdaufruf mit Begründung im Docstring | Öffentliche Funktion mit dem Aufrufer im Docstring (`one_message`) | Phase 11 | `_room` ist der letzte verbliebene Fall |
| Einmaliger Prüfschritt im Ausführungsprotokoll | Regressionstest in der Suite | seit Phase 6 durchgehende Linie, formuliert in `11-SECURITY.md` UF-2 | Der T-11-29-Quelltext-Check ist der letzte offene Fall |
| Budget-Gate gegen eine Vorgängermessung | Gate gegen eine eigene Messung der Phase (15612, Gate 18000) | Plan 11-07 | Diese Phase misst nur nach und hebt nichts |

**Deprecated/outdated im Repo:** der `_ID_KIND`-Kommentar in `tools/mail.py:67-69` ("Plan 10-05 is the one that adds `ids.encode_mail` ... until then") ist die einzige Stelle, die eine erledigte Planung als Zukunft beschreibt. Sie verschwindet mit TOOL-18.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Der Talk-Docstring-Satz kostet rund 53 Bytes, also bleibt `talk_browse` unter 950 Bytes und die Oberfläche unter 15750 | Byte-Budget | Gering. Der genaue Wert hängt am gewählten Wortlaut; die Messung nach dem Edit ist Pflicht und die Luft beträgt 542 beziehungsweise 2343 Bytes |
| A2 | Die konsistente Auslegung von "Whitespace im Rest" ist "nur Whitespace", nicht "enthält Whitespace" | TOOL-18 | Mittel. Bei der strengeren Lesart muss `encode_url` mitgezogen werden, sonst baut der Codec einen Wert, den er nicht parst. Entscheidung gehört in den Plan oder an einen Checkpoint |
| A3 | `pyright` im Modus `standard` meldet `reportPrivateUsage` nicht, deshalb existiert heute kein Typsignal für den Durchgriff | Standard Stack | Gering. Empirisch gestützt: der Durchgriff steht seit Phase 11 im Code und `pyright` ist grün |
| A4 | Eine benannte Ausnahme für `docs/store-submission.md` erfüllt SEC-02(c) ("bereinigt **oder** als interne Ausnahme begründet") | SEC-02(c) | Gering. Das Requirement nennt beide Wege ausdrücklich. Falls der Owner die Bereinigung will, sind sieben von zehn Zeilen umschreibbar und drei brauchen trotzdem eine Ausnahme |
| A5 | Phase 12 darf den Changelog-Block 0.1.9 anlegen, Phase 13 vervollständigt ihn | TOOL-17, Changelog | Gering. Kein Gate hält den obersten Block gegen `__version__`; Phase 13 SC2 verlangt den vollständigen Block ohnehin |
| A6 | Ein neuer Test in `tests/contract/` oder `tests/unit/` braucht keine CI-Änderung | Architecture Patterns | Gering. `ci.yml:36` führt `pytest tests/unit tests/contract` aus, verifiziert durch Lesen der Datei |

## Open Questions

1. **Welcher öffentliche Name für `_room`?**
   - Was wir wissen: `one_message` ist der Präzedenzfall im gleichen Modul; `room_of` ist der wörtliche Review-Vorschlag. Drei Aufrufstellen, keine externe API.
   - Was unklar ist: nur Geschmack und Konsistenzgewicht.
   - Empfehlung: `one_room`, weil das Modul mit `one_message` schon eine Konvention für "genau ein Objekt aus einer gelesenen Menge" hat. Im Plan festlegen, nicht dem Executor überlassen.

2. **AST-Gate oder `ruff --select SLF` für TOOL-19?**
   - Was wir wissen: SLF findet in `src/` drei Treffer, davon zwei legitime im selben Modul; in `tests/` 53, alle legitime Quelltext-Gates. Das AST-Gate prüft die Regel wörtlich und braucht keine Ausnahmen außerhalb der eigenen Datei.
   - Was unklar ist: ob der Owner Lint-Ausnahmen in `oauth/provider.py` und ein neues `per-file-ignores` akzeptabel findet.
   - Empfehlung: AST-Gate in `tests/contract/`. Es trifft die Requirement-Formulierung genau ("zwischen Tool-Modulen") und lässt `oauth/` unberührt. Die `SLF`-Messung dieser Recherche im Plan als Begründung zitieren.

3. **Wo wohnt die Vokabular-Wortliste nach der Ausweitung?**
   - Was wir wissen: kein Test-zu-Test-Import im Repo, `--import-mode=importlib`, kein Testpaket. Drei Optionen sind im SEC-02(c)-Abschnitt beschrieben.
   - Was unklar ist: ob ein Umbau am heute grünen Manifest-Gate erwünscht ist.
   - Empfehlung: die Wortliste bleibt an einer Stelle. Kleinste Änderung ist die Erweiterung in `test_exapp_env_setup.py`; sauberster Zuschnitt ist ein neuer Halter, der Manifest **und** Markdown prüft.

4. **Soll ein Gate das README-Beispiel gegen `PROVIDER_KINDS` halten?**
   - Was wir wissen: SC3 verlangt das Gate nur für den Privat-Durchgriff. Das `spreed`-Beispiel hat drei Releases überlebt, weil kein Test die READMEs auf Provider-Ids prüft.
   - Was unklar ist: ob das im Scope dieser Phase liegt oder Scope-Creep ist.
   - Empfehlung: als kleine Zusatzbehauptung im gleichen Task erwägen (drei READMEs nach `"provider":"..."` durchsuchen, jede Id muss entweder in `PROVIDER_KINDS` stehen oder in einer benannten Liste echter unregistrierter Ids). Wenn das den Task aufbläht, als Deferred-Kandidat notieren.

## Sources

### Primary (HIGH confidence)

- Arbeitsbaum `C:\Users\Student\nextcloud-mcp-connector`, HEAD `3cc8bb9`, gelesen 2026-08-25: `src/mcp_connector/tools/talk.py`, `tools/mail.py`, `tools/chatgpt.py`, `tools/context.py`, `tools/tables.py`, `ids.py`, `provider_map.py`, `server/reg_talk.py`, `server/reg_mail.py`, `scripts/check_tool_budget.py`, `tests/contract/test_no_destructive_calls.py`, `tests/contract/test_tool_surface.py`, `tests/unit/test_talk_tools.py`, `test_ids.py`, `test_provider_map.py`, `test_mail_tools.py`, `test_tools_context.py`, `test_exapp_env_setup.py`, `test_chatgpt_fetch.py`, `pyproject.toml`, `.github/workflows/ci.yml`, `CHANGELOG.md`, `README.md`, `README.de.md`, `README.fr.md`, `docs/store-submission.md`, `scripts/build_store_release.sh`
- Eigene Läufe 2026-08-25: `uv run --no-sync python scripts/check_tool_budget.py` (15657 Bytes, 21 Werkzeuge, Exit 0); Einzelmessung `talk_browse` 858 Bytes über `Client(mcp).list_tools()` mit der Serialisierung des Gates; `uv run --no-sync ruff check --select SLF .` (56 Treffer gesamt) und `... src/` (3 Treffer); `uv run --no-sync pytest tests/contract tests/unit/test_{talk_tools,ids,provider_map,chatgpt_fetch,mail_tools,exapp_env_setup,tools_context}.py` (588 passed in 19,14s)
- `git show 53ba602` (Vorbild-Commit für TOOL-17, vollständiger Diff über vier Dateien)
- `git show 661c609^:.planning/phases/11-b-ndelung-budget-und-release-0-1-6/11-REVIEW.md`, `11-SECURITY.md`, `deferred-items.md`, `11-05-SUMMARY.md`
- `.planning/ROADMAP.md` (Phase-12-Sektion, SC 1-5), `.planning/REQUIREMENTS.md` (TOOL-17..19, SEC-02), `.planning/STATE.md`, `.planning/config.json`, `CLAUDE.md`
- `https://raw.githubusercontent.com/nextcloud/server/v34.0.0/apps/files/lib/Search/FilesSearchProvider.php` (Klasse, `getId()`, Attribute, Link-Route)
- `https://raw.githubusercontent.com/nextcloud/notes/v6.0.2/lib/AppInfo/SearchProvider.php` und `.../main/lib/AppInfo/Application.php` (Klasse, `getId()`, `APP_ID = 'notes'`, keine Attribute, `notes.page.indexnote`)
- `gh api repos/nextcloud/notes/releases/latest` (aktuelles Release `v6.0.2`)

### Secondary (MEDIUM confidence)

- `Application.php` von `nextcloud/notes` wurde auf `main` gelesen, die `SearchProvider.php` zusätzlich am Tag `v6.0.2` gegengeprüft. Die Konstante `APP_ID = 'notes'` ist zwischen `main` und `v6.0.2` sehr wahrscheinlich identisch, aber nur `main` wurde für diese eine Zeile direkt gelesen. Der Plan sollte sie beim Schreiben des Kommentars am Tag bestätigen (ein `curl` auf `.../v6.0.2/lib/AppInfo/Application.php`).

### Tertiary (LOW confidence)

- Keine. Diese Recherche hat keine WebSearch-Ergebnisse verwendet; alle Aussagen stammen aus dem Arbeitsbaum, aus der git-Historie oder aus Quelltext am Release-Tag.

## Metadata

**Confidence breakdown:**

- Fundstellen und Kopplungen: HIGH. Jede Zeilenangabe wurde im Arbeitsbaum gelesen, nicht erinnert. Die Vollständigkeitsaussagen (ein Privat-Durchgriff, eine Eintragsebene mit `truncated`, eine Datei mit dem verbotenen Wort) sind per `grep`/`ruff` über den ganzen Baum belegt.
- Byte-Budget: HIGH für die Ausgangswerte (gemessen), MEDIUM für die Prognose nach dem Edit (hängt am Wortlaut, Luft ist reichlich).
- SEC-02(a) Provider-Verifikation: HIGH für `files` und `notes` (beide am Release-Tag gelesen, `Application.php` siehe Secondary).
- Gate-Bauweise: HIGH für das Vorbild (`_code_lines` gelesen), MEDIUM für die Alias-Auflösung im AST-Gate (das Muster ist im Repo einheitlich, ein Sonderfall ist aber nicht ausgeschlossen).
- Testfolgen: HIGH für die aufgezählten Dateien und Zeilen, MEDIUM für die Vollständigkeit der Liste (die 588 grünen Tests dieses Laufs decken die acht relevanten Dateien plus `tests/contract` ab; ein voller `pytest`-Lauf über alle 2764 Tests ist Sache der Ausführung).
- Diskrepanzen zwischen Requirements und Quelltext: HIGH (beide Seiten gelesen und gegeneinander gehalten).

**Research date:** 2026-08-25
**Valid until:** 2026-09-25 für die Repo-internen Befunde (nur eigene Commits können sie ändern). Für die zwei Nextcloud-Quelltextzitate: unbegrenzt, weil sie an Release-Tags hängen (`nextcloud/server v34.0.0`, `nextcloud/notes v6.0.2`).
