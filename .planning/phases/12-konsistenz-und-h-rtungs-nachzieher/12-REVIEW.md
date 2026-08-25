---
phase: 12-konsistenz-und-h-rtungs-nachzieher
reviewed: 2026-08-25T09:30:00Z
depth: standard
files_reviewed: 14
files_reviewed_list:
  - src/mcp_connector/tools/talk.py
  - src/mcp_connector/tools/chatgpt.py
  - src/mcp_connector/tools/mail.py
  - src/mcp_connector/ids.py
  - src/mcp_connector/provider_map.py
  - src/mcp_connector/server/reg_talk.py
  - tests/unit/test_talk_tools.py
  - tests/unit/test_ids.py
  - tests/unit/test_tools_context.py
  - tests/unit/test_exapp_env_setup.py
  - tests/unit/test_provider_map.py
  - tests/contract/test_module_boundaries.py
  - README.md
  - README.de.md
  - README.fr.md
findings:
  critical: 0
  warning: 6
  info: 3
  total: 9
status: issues_found
---

# Phase 12: Code Review Report

**Reviewed:** 2026-08-25T09:30:00Z
**Depth:** standard
**Files Reviewed:** 14
**Status:** issues_found

## Summary

Geprüft wurden die Phase-12-Nachzieher: die Umbenennung `message_truncated` auf der Talk-Nachrichtenebene (inklusive Verbraucher `chatgpt.py`), der Id-Codec als einzige Quelle (`encode_mail`-Nutzung in `mail.py`, neues `encode_card_short`, `hit_url` über `ids.parse`, `url:`-Whitespace-Grenze), das öffentliche `talk.one_room` mit mitgewandertem T-09-21-Docstring, das neue AST-Gate `test_module_boundaries.py`, die Ausweitung des Vokabular-Gates auf READMEs/CHANGELOG/docs, den T-11-29-Regressionstest, die PROVIDER_KINDS-Verifikationskommentare und das README-Beispiel `talk-conversations` mit Halter-Test.

Die Kernzusagen der Phase halten der Prüfung stand: die zwei Truncation-Schlüssel sind auf allen Ebenen konsistent (Erzeuger `talk._message`, Verbraucher `chatgpt._fetch_message`, Registrierungs-Docstrings `reg_talk`/`reg_mail`, Tests DF-11-01), kein Modul baut mehr Id-Präfixe von Hand (verifiziert per Grep über `src/`), die Client-Schicht fängt geparste Segmente korrekt ab (`safe_segment`/`quote` in caldav, lxml-Escaping plus Numerik-Guard in `dav.build_fileid_body`), und der Halter-Test in `test_provider_map.py` liest die drei READMEs durch dieselbe Extraktion wie seine Gegenprobe.

Keine Critical-Befunde. Sechs Warnungen betreffen Lücken in genau den Härtungen, die diese Phase liefert: das Modul-Grenzen-Gate übersieht die naheliegendste Schreibweise des Verstoßes (direkter Symbol-Import), der Id-Codec liest für drei Arten weiterhin eine strikt größere Menge zurück als die Encode-Seite bauen kann (dieselbe Asymmetrieklasse, die 12-02 für `url:` geschlossen hat), `provider_map` verwendet `str.isdigit()` entgegen der eigenen `_DIGITS`-Begründung, drei `fetch`-Zweige filtern Titel nicht durch `marks.without_marks` (während drei andere es tun), das erweiterte Vokabular-Gate erreicht Unterordner von `docs/` nicht, und `encode_card_short` hat keinen direkten Unit-Test für seinen Fehlerpfad.

## Narrative Findings (AI reviewer)

### Warnings

#### WR-01: Modul-Grenzen-Gate übersieht den direkten Import eines privaten Namens

**File:** `tests/contract/test_module_boundaries.py:90-122` (`_aliases`), `:145-151` (`_reaches`)
**Issue:** Das Gate erkennt nur `ast.Attribute` auf Modul-Aliases. Die direkteste Schreibweise des Verstoßes bleibt unsichtbar: `from .talk import _conversation` (oder `from ..tools.talk import _room` aus `server/`) bindet den privaten Namen lokal. In `_aliases.keep()` ist der `prefix` dann `mcp_connector.tools.talk` und nicht `mcp_connector.tools`, also wird der Alias verworfen, und der spätere Aufruf ist ein `ast.Name` ohne Attribut, den `_reaches` nie sieht. Ebenso unsichtbar: `import mcp_connector.tools.talk` ohne Alias mit anschließender Attribut-Kette `mcp_connector.tools.talk._x` (der Kommentar in Zeile 116-118 räumt das ein, behandelt es aber als unmöglich statt als ungeprüft). Die Gegenprobe `test_every_import_form_in_the_tree_is_resolved` deckt fünf Modul-Import-Formen ab, aber keinen Symbol-Import. Damit ist genau der Verstoß, gegen den das Gate laut Docstring existiert (TOOL-19), in seiner billigsten Form nicht gedeckt.
**Fix:**
```python
# in _reaches, zusaetzlich zu den Attribute-Hits:
package = _package_of(relative)
own = _dotted(relative)
tools = _tool_modules()
for node in ast.walk(tree):
    if not isinstance(node, ast.ImportFrom):
        continue
    base = _base_of(node, package)
    prefix, _, stem = base.rpartition(".")
    if base == own or prefix != TOOLS_PACKAGE or stem not in tools:
        continue
    for alias in node.names:
        if _is_private(alias.name):
            hits.append((node.lineno, f"from {base} import {alias.name}"))
```
Dazu eine Gegenprobe mit `from .talk import _conversation`, damit die neue Kante gesehen wurde, bevor sie grün ist.

#### WR-02: `provider_map` prüft Ziffern mit `str.isdigit()` entgegen der eigenen `_DIGITS`-Begründung

**File:** `src/mcp_connector/provider_map.py:198`, `:203`, `:259`
**Issue:** Der Kommentar an `_DIGITS` (Zeile 98-100) benennt selbst, dass `str.isdigit()` auch eine hochgestellte Zwei und arabisch-indische Ziffern akzeptiert (WR-04-Klasse aus dem Mail-Review). Trotzdem verwenden `_file_id` (zweimal) und `_last_numeric_segment` (Quelle der note- und card-Ids) `isdigit()`. Ein manipulierter oder deformierter Suchtreffer mit `fileId: "٤٢"` baut so `file:٤٢`; `ids.parse` hat für `file`/`note`/`card` keinen Ziffern-Guard, also stoppt erst `dav.build_fileid_body`, das mit `isdigit()` ebenfalls Nicht-ASCII durchlässt (dav.py:285). Konsequenz ist kein Fremdobjekt-Zugriff, aber eine Anfrage mit einem Wert, den Nextcloud nie ausgegeben hat, statt der Zero-Request-Ablehnung, die das Projekt für genau diese Klasse eingeführt hat.
**Fix:** In allen drei Stellen `_DIGITS.fullmatch(candidate)` statt `candidate.isdigit()` (die Konstante steht bereits im Modul); in `dav.build_fileid_body` denselben Tausch als Backstop.

#### WR-03: `ids.parse` liest für `file:`, `note:` und `event:` eine größere Menge zurück als die Encode-Seite bauen kann

**File:** `src/mcp_connector/ids.py:141-142` (file/note), `:178-181` (event)
**Issue:** Genau der Maßstab, den 12-02 für `url:` in den Code geschrieben hat ("exactly that set and no larger one may be read back", Zeile 128-131), gilt für drei andere Arten nicht: `_join` refust den SEPARATOR in jedem Segment, aber `parse("note:4:2")` liefert `("4:2",)`, `parse("file:a:b")` liefert `("a:b",)`, und `parse("event:a:b:c")` liefert wegen `maxsplit=1` `("a", "b:c")`. Alle drei sind Ids, die dieses Modul nie gebaut haben kann. Die Folge ist heute eine 404/Ablehnung eine Schicht tiefer (caldav quotet, dav prüft numerisch), also kein falsches Objekt, aber die Asymmetrie ist dieselbe, die diese Phase für `url:` als IN-04 geschlossen hat, und sie kostet pro erfundener Id eine Anfrage, die eine Zero-Request-Ablehnung wäre.
**Fix:**
```python
if kind in ("file", "note"):
    if SEPARATOR in rest:
        raise ToolError(message=f"{raw!r} is not a valid resource id.", hint=_HINT)
    parts = (rest,)
...
elif kind == "event":
    parts = tuple(rest.split(SEPARATOR))
    if len(parts) != 2:
        raise ToolError(message=f"{raw!r} is not a valid event id.", hint=_HINT)
```
Dazu in `test_ids.py` die Fälle `note:4:2`, `file:a:b`, `event:a:b:c` als Ablehnungen pinnen (heute testet nur `test_encode_rejects_separator_inside_a_part` die Encode-Seite).

#### WR-04: Drei `fetch`-Zweige filtern den Titel nicht durch `marks.without_marks`

**File:** `src/mcp_connector/tools/chatgpt.py:269` (`_fetch_file`), `:288` (`_fetch_note`), `:313` (`_fetch_card`)
**Issue:** Die drei neueren Zweige derselben Funktion filtern den Titel als Fremdtext: `_fetch_mail:464`, `_fetch_message:664` und `_fetch_table:735` laufen durch `marks.without_marks`. Die drei älteren tun es nicht, obwohl der Titel dort genauso Fremdtext ist: der Dateiname wird von wem auch immer die Datei teilt gewählt, Notiz- und Kartentitel von jedem Schreibberechtigten (`notes_tools.read` filtert den Titel ebenfalls nicht, geprüft in notes.py:109; `deck.py` enthält kein `without_marks`). Ein Titel, der eine der Marker-Sequenzen dieses Servers trägt, landet damit ungefiltert im `title`-Feld der Fetch-Antwort, direkt neben dem gefilterten `text`, und kann die Rahmung beanspruchen, gegen die ME-03/BL-09 den Rest der Antwort härten. Die Modulregel (Docstring Zeile 43-53) ist auf `text` formuliert, aber die Mail-/Message-/Table-Zweige zeigen, dass das Projekt die Regel bereits breiter anwendet, nur nicht rückwirkend.
**Fix:** In den drei Rückgaben `marks.without_marks(...)` um den Titel legen, analog `_fetch_mail`:
```python
"title": marks.without_marks(path.rsplit("/", 1)[-1] or path),
"title": marks.without_marks(str(note["title"])),
"title": marks.without_marks(str(card.get("title") or "")),
```

#### WR-05: Vokabular-Gate erreicht Unterordner von `docs/` nicht, beansprucht aber "the rest of docs/"

**File:** `tests/unit/test_exapp_env_setup.py:2017` (`public_markdown_pages`)
**Issue:** `(ROOT / "docs").glob("*.md")` ist nicht rekursiv. `docs/contrib/227-pr-body.md` existiert und liegt außerhalb der Reichweite des Gates, obwohl Testname und Docstring (Zeile 2030-2031, UF-3) beanspruchen, die Regel erreiche neben den vier benannten Seiten "the rest of docs/". Die Datei ist heute clean (per Grep verifiziert), aber jede künftige Seite unter einem `docs/`-Unterordner entkommt still, und der Selbsttest `test_the_vocabulary_gate_reads_a_list_that_is_not_empty` bemerkt das nicht, weil er nur eine Untermenge und die Nicht-Leere prüft. Das ist exakt die Sorte "Gate, das grün ist, ohne hinzusehen", gegen die derselbe Testblock seine Gegenproben baut.
**Fix:**
```python
docs = sorted(
    page for page in (ROOT / "docs").rglob("*.md") if page != VOCABULARY_EXCEPTION
)
```
Falls Unterordner bewusst ausgenommen bleiben sollen (z. B. `docs/contrib/` als Fremd-Repo-Text), die Ausnahme wie `VOCABULARY_EXCEPTION` benennen und im Selbsttest pinnen, statt sie im Glob verschwinden zu lassen.

#### WR-06: `encode_card_short` ohne direkten Unit-Test, Fehlerpfad ungetestet

**File:** `tests/unit/test_ids.py:20-35` (Roundtrip-Liste), `:225-238` (`test_encode_rejects_empty_parts`)
**Issue:** Die in dieser Phase neu eingeführte Codec-Funktion `ids.encode_card_short` (ids.py:96-105) wird in `test_ids.py` weder im Roundtrip (`parse(encode_card_short("99")) == ("card", ("99",))`) noch im Fehlerpfad (`encode_card_short("")` und `encode_card_short("9:9")` müssen ToolError werfen) geprüft; `test_encode_rejects_empty_parts` wurde nicht erweitert. Der Happy Path ist nur indirekt über `test_provider_map.py` gedeckt. Das verletzt die Projektregel, alle Pfade (Fehler/Edge) zu testen, und lässt genau die `_join`-Refusals ungeprüft, auf die der Kommentar in `provider_map.extract_id` (Zeile 153-156, T-12-05) sich verlässt.
**Fix:** In `test_ids.py` den Roundtrip-Fall in die Achterliste aufnehmen und `lambda: ids.encode_card_short("")` sowie einen Separator-Fall in die beiden Reject-Tests eintragen.

### Info

#### IN-01: `provider_map.hit_url`-Kommentar behauptet eine Unerreichbarkeit, die nicht gilt

**File:** `src/mcp_connector/provider_map.py:185-191`
**Issue:** Der Kommentar sagt, keine andere Art als `url` erreiche die letzte Zeile ohne `resourceUrl`, weil `extract_id` den Eintrag sonst übersprungen hätte. Ein Talk-Treffer mit gefüllten `attributes` (`conversation` + `messageId`) und leerem `resourceUrl` liefert aber `kind="message"` (Attribute genügen `_message_target`), und `hit_url` antwortet dann mit `base_url` statt mit dem Konversationslink, dessen Bestandteile in `parts` vorliegen. Das Verhalten ist defensiv in Ordnung (nicht-leere URL auf der Instanz), der Kommentar ist falsch.
**Fix:** Kommentar korrigieren oder den Zweig ergänzen: `if read_kind == "message": return f"{base_url}/index.php/call/{parts[0]}"`.

#### IN-02: `fetch`-Hint reflektiert eine unvalidierte URL mit der Aufforderung, sie zu öffnen

**File:** `src/mcp_connector/tools/chatgpt.py:224-228`
**Issue:** Für eine `url:`-Id sagt der Hint "Open the url in a browser to read it: {parts[0]}". Selbst gebaute `url:`-Ids liegen immer auf der konfigurierten Instanz, aber `fetch` nimmt auch frei erfundene Ids an: `url:file:///etc/passwd` oder `url:https://evil.test/x` passieren `ids.parse` und werden im Hint mit Öffnungsempfehlung zurückgegeben. Der Server fetcht nie (T-01-75 bleibt dicht), aber die Empfehlung, eine fremde Adresse zu öffnen, ist billig vermeidbar.
**Fix:** Vor der Empfehlung prüfen, dass der Wert mit `clients.creds.base_url` beginnt; andernfalls den Hint ohne die URL formulieren ("Run search again and open the url of a fresh hit").

#### IN-03: `talk.send` schickt eine leere Nachricht mit zwei Anfragen auf die Reise

**File:** `src/mcp_connector/tools/talk.py:263-301`
**Issue:** Eine Nachricht aus nur Whitespace passiert alle sechs Refusals (`counted = 0 <= allowed`), kostet den Room-Lookup plus den POST und scheitert erst an Talks eigener Antwort (der Server trimmt und lehnt Leeres ab). Die Familie begründet ihre Reihenfolge damit, dass der billigste Fehler keine Anfrage kostet; hier kostet er zwei.
**Fix:** Nach dem Trim-Zählen `if not counted: raise ToolError(message="The message is empty after trimming.", hint="Write the text to post; talk_send sends exactly one plain text message.")`.

---

_Reviewed: 2026-08-25T09:30:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
