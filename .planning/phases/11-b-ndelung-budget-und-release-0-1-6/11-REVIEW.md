---
phase: 11-b-ndelung-budget-und-release-0-1-6
reviewed: 2026-08-25T03:24:04Z
depth: standard
files_reviewed: 29
files_reviewed_list:
  - scripts/acceptance_all_tools.py
  - scripts/check_tool_budget.py
  - src/mcp_connector/ids.py
  - src/mcp_connector/nextcloud/clients/talk.py
  - src/mcp_connector/provider_map.py
  - src/mcp_connector/server/reg_context.py
  - src/mcp_connector/server/reg_mail.py
  - src/mcp_connector/server/reg_tables.py
  - src/mcp_connector/server/reg_talk.py
  - src/mcp_connector/tools/chatgpt.py
  - src/mcp_connector/tools/context.py
  - src/mcp_connector/tools/mail.py
  - src/mcp_connector/tools/tables.py
  - src/mcp_connector/tools/talk.py
  - tests/contract/test_tool_surface.py
  - tests/integration/test_ctx_bundle.py
  - tests/unit/test_chatgpt_fetch.py
  - tests/unit/test_exapp_env_setup.py
  - tests/unit/test_ids.py
  - tests/unit/test_mail_tools.py
  - tests/unit/test_provider_map.py
  - tests/unit/test_talk_client.py
  - tests/unit/test_tools_context.py
  - CHANGELOG.md
  - appinfo/info.xml
  - README.md
  - README.de.md
  - README.fr.md
  - docs/store-submission.md
findings:
  critical: 0
  warning: 4
  info: 7
  total: 11
status: issues_found
---

# Phase 11: Code Review Report

**Reviewed:** 2026-08-25T03:24:04Z
**Depth:** standard
**Files Reviewed:** 29
**Status:** issues_found

## Summary

Geprüft wurden die vier Beine von `prepare_context` (Talk-Digest und Mail-Zähler mit eigenen Budgets und `degraded`-Einträgen), die fetch-Auflösung der zwei neuen id-Arten (`message:<token>:<id>` und `table:<id>` samt Codec, Provider-Map und `get_message_context`), die Schema-Diät mit dem Budget-Gate 18000, das Abnahmeskript, die `preview_truncated`-Umbenennung und die Release-Artefakte von 0.1.8. Kein Structural-Findings-Block wurde übergeben, daher entfällt der Fallow-Abschnitt.

Die Kern-Invarianten der Phase halten und sind je durch Tests gedeckt: `tools/context.py` liest keine Client-Schicht (Gate-Test `test_this_module_reads_no_content_of_its_own` grün gegen den Quelltext), die Zähler kommen aus den Postfachlisten und nie aus dem Navigations-`unread` (Messung 3/4 in `test_ctx_bundle.py`), die Kontext-Route trägt keinen der vier Leseparameter und wird über die Konversationsliste statt über sich selbst vermessen, der Ziffern- und Token-Guard der neuen id-Arten steht im Codec und kostet keinen einzigen Request, eine View wird nie als Tabelle gelesen, ein Mail-Treffer bleibt bewusst `url`. Das Budget-Gate ist auf eine Messung der Phase verankert (15612, Gate 18000) und das Abnahmeskript liest die erwartete Tool-Menge aus `tools/list` statt aus einer zweiten Liste. Em-Dashes und ASCII-Umlaute wurden in allen öffentlichen Texten nicht gefunden; das Vokabular-Gate über die Manifest-Texte greift samt Gegenprobe.

Vier Warnungen bleiben stehen: eine Tokenisierungs-Lücke im Mail-Filter-Gate, die exakt die stille Falschantwort durchlässt, gegen die das Gate gebaut wurde; stumme Tool-Schicht-Kappungen im Mail-Bein von `prepare_context`, die im Grenzfall einen faktisch falschen `degraded`-Satz erzeugen; die drei READMEs, die im signierten 0.1.8-Store-Archiv "Version 0.1.7" behaupten; und ein stiller Last-wins bei Spaltentitel-Aliassen auf dem Tables-Schreibpfad. Dazu sieben Hinweise.

## Narrative Findings (AI reviewer)

## Warnings

### WR-01: Das Mail-Filter-Gate tokenisiert anders als die Mail-App und lässt damit genau die stille Falschantwort durch, gegen die es existiert

**File:** `src/mcp_connector/tools/mail.py:253`
**Issue:** `_checked_filter` prüft die Bedingungen über `wanted.split()` (jeder Unicode-Whitespace), die Mail-App splittet ihren Filter aber ausschließlich an Leerzeichen. Ein Filter, dessen Bedingungen durch einen Tab oder ein geschütztes Leerzeichen getrennt sind, besteht die Prüfung hier ("is:unread" und "from:chef" sind einzeln gültig), erreicht die App jedoch als **ein** Token `is:unread\tfrom:chef`, dessen Wert kein bekanntes Flag ist. Die App verwirft es wortlos und antwortet mit der ungefilterten Liste, exakt das gemessene `is:ungelesen`-Szenario, dessen Verhinderung der dokumentierte Zweck der Positivliste ist. Der Docstring behauptet die sichere Richtung ("a tab inside a value is checked as two tokens here and refused"); das stimmt nur, wenn der Tab ein einzelnes Token ungültig macht, nicht wenn er zwei gültige Tokens trennt. Nachgestellt: `"is:unread\tfrom:chef".split()` ergibt zwei gültige Tokens, `.split(" ")` (App-Sicht) ergibt eines.
**Fix:**
```python
# in _checked_filter, vor der Token-Schleife:
if any(ch.isspace() and ch != " " for ch in wanted):
    raise ToolError(
        message="The filter contains whitespace the Mail app does not split on.",
        hint=_FILTER_HINT,
    )
# alternativ: for token in wanted.split(" ") iterieren (leere Tokens überspringen),
# damit Prüfung und App dieselbe Zerlegung sehen.
```

### WR-02: Das Mail-Bein von prepare_context verschluckt die Kappungen der Tool-Schicht und schreibt im Grenzfall einen faktisch falschen degraded-Satz

**File:** `src/mcp_connector/tools/context.py:346-370` (`_mail`), `:389-395` (`_counter`), `:417-445` (`_counters`)
**Issue:** Zwei Verstöße gegen die eigene Regel des Moduls "every cap writes its own degraded entry":
1. Die Postfachliste je Konto ist über den Envelope von `mail_browse` bei `MAX_LIMIT` (50) gekappt. Liegt die Inbox eines Kontos mit mehr als 50 Postfächern hinter dem Schnitt, findet `_counter` keine Rolle `inbox` und `_counters` schreibt "The mail account X has no mailbox with the inbox role", eine falsche Aussage; `truncated`/`note` des Postfach-Envelopes werden in `_counter` kommentarlos verworfen. Der Modulkommentar adressiert die 20er-Falle durch `MAX_LIMIT`, dieselbe Falle eine Größe weiter bleibt offen und wird falsch benannt statt still.
2. Auch die Kontenliste ist bei 50 gekappt; `total = len(accounts)` unterschlägt dann Konten, und der Envelope-Schnitt erreicht `degraded` nie: `degraded.extend(_degraded_of(outcome))` in `_counters` ist für dieses Bein toter Code, weil `_mail` das Antwort-Dict selbst baut und nie einen `degraded`-Schlüssel setzt. Der Docstring-Satz "the cut that decides this answer is always this module's own and never the one of the tool layer" ist damit für das gemeldete `total` nicht wahr.
**Fix:** In `_mail` die `truncated`-Flags der Envelopes mitnehmen (z. B. `("boxes_truncated": bool(answer.get("truncated")))` je Konto und `("accounts_truncated": bool(listed.get("truncated")))`) und in `_counters` verwerten: bei gekappter Postfachliste ohne gefundene Inbox den Satz "the mailbox list of account X was cut at 50, so its inbox may be behind the cut" schreiben statt "has no mailbox with the inbox role"; bei gekappter Kontenliste einen eigenen Eintrag mit der Zahl. Ein Unit-Test mit 60 Postfächern (Inbox an Position 55) pinnt beides.

### WR-03: Die drei READMEs nennen "Version 0.1.7" und reisen so im signierten 0.1.8-Store-Archiv mit

**File:** `README.md:27`, `README.de.md:29`, `README.fr.md:31`
**Issue:** Release 0.1.8 ist im Store (CHANGELOG, `info.xml` `<version>0.1.8</version>`, Proof-Zeilen vom 2026-08-25 in `docs/store-submission.md`), die Statuszeile aller drei READMEs blieb aber auf 0.1.7 stehen (letzte Anhebung in Commit `6b67cbc`, dem 0.1.7-Release). `README.md` liegt laut Proof-Zeile 2026-08-24 22:39Z im Store-Archiv (`appinfo/info.xml`, `CHANGELOG.md`, `LICENSE`, `README.md`), das Archiv ist signiert und veröffentlicht: Wer 0.1.8 herunterlädt, liest darin "Version 0.1.7". Der Release-Runbook-Schritt 1 nennt vier Stellen für die Versionsanhebung, die README-Statuszeile ist keine davon, und kein Gate hält sie (der Tool-Count-Test prüft nur Tool-Zahlen), also wiederholt sich die Drift.
**Fix:** Statuszeile in allen drei READMEs auf die aktuelle Version heben (nächstes Release, das Archiv von 0.1.8 ist unveränderlich). Dauerhaft: entweder die READMEs in Runbook-Schritt 1 aufnehmen oder ein Contract-Test, der `Version <x>` in den drei READMEs gegen `mcp_connector.__version__` vergleicht (analog zur bestehenden Tool-Count-Regel in `tests/contract/test_tool_surface.py`).

### WR-04: tables_create_row lässt zwei Eingabe-Schlüssel, die auf dieselbe Spalte normalisieren, still zum Last-wins werden

**File:** `src/mcp_connector/tools/tables.py:237-254` (`_by_column_id`)
**Issue:** Die Titel-Auflösung normalisiert mit `strip().casefold()`. Zwei verschiedene JSON-Schlüssel in `values`, die auf dieselbe Spalte zeigen (etwa `"Task"` und `"task "`), überschreiben sich in `data[str(column_id)]` und in `written` gegenseitig: der zuletzt iterierte Wert wird geschrieben, der erste verschwindet ohne Refusal. Das widerspricht der Refusal-first-Linie der Familie, die den Spiegelfall (ein Titel, zwei Spalten) als "ambiguous" ablehnt, und ist auf einem Schreibpfad ein stiller Datenverlust: die Antwort (`values_written`) trägt nur den Gewinner, und der Aufrufer hat keinen Fehler gesehen.
**Fix:**
```python
seen: dict[str, str] = {}
for title, value in wanted.items():
    key = _normalise(title)
    if key in seen:
        raise ToolError(
            message=f"values names the column {seen[key]!r} twice (also as {str(title)!r}).",
            hint="The comparison ignores case and surrounding spaces; keep one key per column.",
        )
    seen[key] = str(title)
    ...
```

## Info

### IN-01: Veralteter _ID_KIND-Workaround in mail.py, obwohl ids.encode_mail existiert

**File:** `src/mcp_connector/tools/mail.py:66-70, 478`
**Issue:** Der Kommentar zu `_ID_KIND` sagt "Plan 10-05 is the one that adds `ids.encode_mail` ... **until then** the prefix is built from the separator". Plan 10-05 ist längst geliefert (`ids.encode_mail` existiert und ist getestet), `_message` baut die id aber weiter von Hand (`f"{_ID_KIND}{ids.SEPARATOR}..."`), also ein zweiter id-Bauer außerhalb des Codecs, dessen Docstring "encoded and parsed in exactly one place" verspricht. Korrektheit ist heute nicht betroffen (`databaseId` ist per Filter > 0), aber die Codec-Garantien (Leersegment-, Separator-Refusal) gelten hier nicht.
**Fix:** `entry["id"] = ids.encode_mail(_number(raw.get("databaseId")))` und `_ID_KIND` samt Kommentar entfernen.

### IN-02: Stale-Kommentar in info.xml beschreibt ein Ampersand-Entity, das es seit dem paypal.me-Wechsel nicht mehr gibt

**File:** `appinfo/info.xml:211-213`
**Issue:** "The ampersand of the PayPal address is written as an entity because this is XML: a bare one is a parse error" - die 0.1.8-Korrektur ersetzte die alte URL mit Query-Parametern durch `https://www.paypal.com/paypalme/KhaledCherifDev`; kein Ampersand und kein Entity mehr vorhanden. Der Kommentar beschreibt einen Zustand, der weg ist, und schickt den nächsten Leser auf die Suche nach einem `&amp;`, das nicht existiert.
**Fix:** Den Satz streichen oder auf "früher trug die URL ein Entity" umformulieren.

### IN-03: Das Abnahmeskript meldet ein Tool, das nur FAIL-Zeilen hat, zusätzlich als "never called"

**File:** `scripts/acceptance_all_tools.py:94, 531-536`
**Issue:** `Report.called()` zählt nur OK- und SKIP-Zeilen. Ein Tool, dessen sämtliche Aufrufe fehlschlugen, steht in `failures()` **und** in `never_called = registry - report.called()`, die Ausgabe behauptet dann "never called" über ein Tool, das aufgerufen wurde und fehlschlug. Der Exit-Code ist so oder so 1, aber die Diagnose-Zeile ist falsch und schickt den Leser in die falsche Richtung ("das Skript kennt das Tool nicht" statt "das Tool ist kaputt").
**Fix:** `called()` auf `verdict in ("OK", "SKIP", "FAIL")` erweitern (oder `never_called -= set(failures)`), damit "never called" nur Tools nennt, für die wirklich keine Zeile existiert.

### IN-04: ids.parse überspringt für die url-Art den Leersegment-Check

**File:** `src/mcp_connector/ids.py:115-116, 161-162`
**Issue:** `parse` kehrt für `kind == "url"` vor dem gemeinsamen `any(not part.strip())`-Check zurück. `url:   ` (nur Whitespace hinter dem Doppelpunkt) parst deshalb erfolgreich zu `("url", ("   ",))`, während jede andere Art ein leeres Segment ablehnt; `fetch` antwortet dann mit dem Hinweis "Open the url in a browser to read it:" gefolgt von Leerzeichen. Kein Sicherheitsproblem (die url wird nie angefragt), aber eine Inkonsistenz gegenüber `encode_url`, das denselben Wert ablehnt.
**Fix:** `rest.strip()` prüfen und bei leerem Ergebnis mit dem bestehenden "not a valid resource id"-Satz ablehnen.

### IN-05: Das unified_search-Beispiel der drei READMEs zeigt die Provider-Id "spreed", die Nextcloud nie meldet

**File:** `README.md:372`, `README.de.md:381`, `README.fr.md:389`
**Issue:** Das JSON-Beispiel trägt `"provider":"spreed"`. Die echten Talk-Provider-Ids sind `talk-conversations`, `talk-message` und `talk-message-current`; `tests/unit/test_provider_map.py:80` hält ausdrücklich fest, dass "spreed" nie eine Provider-Id war. Ein Leser, der das Beispiel in den `providers`-Parameter kopiert, bekommt einen `degraded`-Eintrag über einen unbekannten Provider.
**Fix:** Im Beispiel `"provider":"talk-conversations"` schreiben (die Zeile ist ohnehin der Konversations-Fall mit `kind":"url"`).

### IN-06: chatgpt.py ruft die private Funktion talk_tools._room über die Modulgrenze

**File:** `src/mcp_connector/tools/chatgpt.py:616`
**Issue:** `_fetch_message` benutzt `talk_tools._room` (Unterstrich-privat) aus einem fremden Modul. Die Nutzung ist per Docstring begründet (Konversationsliste statt Einzelroute, T-09-21), aber eine private Funktion trägt keinen Stabilitätsvertrag: ein Refactoring in `talk.py` bricht `fetch`, ohne dass ein Name es ankündigt. `one_message` wurde für exakt diesen Aufrufer öffentlich gemacht; `_room` sollte denselben Weg gehen.
**Fix:** `_room` unter einem öffentlichen Namen exportieren (z. B. `room_of(clients, token, *, include_last_message)`) und `_fetch_message` darauf umstellen.

### IN-07: Die Vokabular-Regel "archiv" ist repo-weit formuliert, aber nur über das Manifest erzwungen; docs/store-submission.md nutzt das Wort in neuen 0.1.8-Zeilen

**File:** `tests/unit/test_exapp_env_setup.py:1685-1686`, `docs/store-submission.md:47, 124-131`
**Issue:** Das Gate sagt über sich selbst "this word must not appear in a public artefact of this repo, and the manifest is the most public one there is", geprüft wird aber ausschließlich der Element-Text von `info.xml`. Die in dieser Phase ergänzten Proof-Zeilen von 0.1.8 in `docs/store-submission.md` verwenden "store archive" mehrfach (englischer tar.gz-Sinn, nicht der gesperrte Postfach-Sinn). Entweder ist die Regel enger gemeint als ihr Docstring (dann sollte er "manifest" statt "public artefact of this repo" sagen), oder das Gate müsste `docs/` mitprüfen und der Runbook-Text ein anderes Wort ("release tarball") verwenden. Aktuell widersprechen sich Regeltext und Durchsetzung.
**Fix:** Docstring des Gates auf den tatsächlichen Geltungsbereich präzisieren, oder Scope erweitern und den Runbook-Text umformulieren; eine der beiden Richtungen bewusst wählen.

---

_Reviewed: 2026-08-25T03:24:04Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
