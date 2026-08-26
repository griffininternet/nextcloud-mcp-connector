---
phase: 12-konsistenz-und-h-rtungs-nachzieher
slug: konsistenz-und-haertungs-nachzieher
status: verified
threats_open: 0
asvs_level: 1
created: 2026-08-25
updated: 2026-08-25
---

# Phase 12 , Security

> Sicherheitsvertrag dieser Phase: Bedrohungsregister, akzeptierte Risiken, Prüfprotokoll.
> Geprüfter Stand: HEAD `3ee4d43`, also nach dem Review-Fix-Pass
> (`60ac592`, `a3a846b`, `6318ba0`, `85859e6`, `a7ee8ee`, `c9a6f9d`) und nach `813b81b`.
> Grundhaltung dieser Prüfung: jede Minderung gilt als abwesend, bis eine Fundstelle im
> Implementierungsstand sie belegt. Doku und Absicht allein sind kein Beweis.
> Register aufgebaut aus den vier `<threat_model>`-Blöcken von `12-01-PLAN.md` bis
> `12-04-PLAN.md` (`register_authored_at_plan_time: true`): 18 nummerierte Zeilen plus
> `T-12-SC` in jedem der vier Pläne, zusammen 22 Registerzeilen in 19 Registereinträgen.
> Gate-Läufe dieses Audits:
> `uv run --no-sync pytest tests/contract tests/unit/test_{ids,provider_map,talk_tools,chatgpt_fetch,tools_context,exapp_env_setup,mail_tools}.py`
> = 617 passed in 14,85 s; `uv run --no-sync python scripts/check_tool_budget.py`
> = 15711 Bytes bei 21 Werkzeugen gegen Budget 18000, größtes Werkzeug `mail_browse`
> mit 1376 Bytes gegen 1400, `talk_browse` 912 Bytes, Exit 0;
> `uv run --no-sync ruff check .` = All checks passed;
> `uv run --no-sync ruff check --select SLF src/` = 2 Treffer, `tests/` = 53 Treffer,
> also genau die Messung, die der Docstring des neuen Gates behauptet.
> Implementierungsdateien wurden von diesem Audit nicht angefasst.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Projektion zu zweitem Leser | `tools/talk.py` baut den Eintrag, `tools/chatgpt.py` liest ihn; `entry.get(...)` wirft nicht, ein Bruch wäre still | Eintragsschlüssel, Kappungsflagge |
| Antwortschlüssel zu Modellverständnis | Ein Wort mit zwei Bedeutungen in derselben Antwort wird auf einer Ebene falsch gelesen und lässt ein Modell im Kreis blättern | `truncated` (Seite), `message_truncated` (Text eines Eintrags) |
| Fremdtext zu Antwortstruktur | Eine Kappung, die als Marker im Text steht statt als Feld daneben, ist ein Einfallstor (ME-03) | Chattext, Kappungsmarker |
| Tool-Docstring zu Byte-Budget | Nur der Docstring in `reg_talk.py` reist in `tools/list`; jede Zeile dort ist Kontextkosten jeder Sitzung | Beschreibungstexte, Enums |
| Modellantwort zu Id-Prüfung | Jede Id, die `fetch` erreicht, kommt aus einer Modellantwort; `ids.parse` ist die Eingangsprüfung vor dem ersten Request (ASVS V5) | Id-Art, Segmente, Whitespace |
| Id-Erzeugung zu Id-Prüfung | Ein zweiter Bauer außerhalb des Codecs umgeht dessen Refusals, ohne dass ein Gate es merkt | `SEPARATOR`, Präfixe, Kurzform `card:<id>` |
| Codec zu sich selbst | Was `encode` baut, muss `parse` lesen, und was `parse` liest, muss `encode` bauen können; jede Lücke ist ein Wert ohne Herkunft | `url:`, `file:`, `note:`, `event:` |
| Fremder Quelltext zu eigener Datenkarte | Die Zuordnung Provider-Id zu Ressourcenart ist eine Behauptung über Code, der nicht in diesem Repo liegt | Provider-Id, Attribute, Fragment |
| Fremdtext zu Kontextbündel | `prepare_context` darf die Nachrichtenebene von Mail nie anfragen, sonst gelangt Fremdtext ohne Not in das Bündel (T-11-29) | Betreff, Absender, Mailtext |
| Repo zu Öffentlichkeit | READMEs, `CHANGELOG.md` und `docs/` sind das öffentliche Gesicht; die Vokabular-Regel gilt für sie und nicht nur für das Manifest | Markdown-Text, Manifest-Beschreibungen |
| Regel zu Durchsetzung | Ein einmaliger Prüfschritt und ein Kommentar ohne Gate sind Zusagen ohne Wächter | Quelltext-Behauptungen, Wortlisten |
| Modellantwort zu Talk-Route | Ein Konversations-Token aus einer Modellantwort darf nie in den Pfad von `GET /room/{token}` gelangen (T-09-21) | Token als Pfadsegment |
| Tool-Modul zu Tool-Modul | Ein privater Name ist die Zusage, dass niemand von außen daran hängt; ein Durchgriff bricht sie unsichtbar und nimmt Mitigationen mit | Funktionsnamen, Import-Kanten |
| Dokumentation zu Nutzer | Ein Beispiel mit einer erfundenen Id lehrt ein falsches Modell der Provider-Landschaft | Provider-Ids in drei READMEs |
| Erklärende Prosa zu Gate | Ein Grep-Gate über Quelltext macht Dokumentation zum Kostenfaktor und lädt zum Löschen von Sätzen ein | Docstrings und Kommentare mit fremden Privatnamen |

---

## Threat Register

Alle 19 Registereinträge CLOSED. Belege (Datei:Zeile bzw. Test) aus dem Audit-Lauf 2026-08-25:

| Threat ID | Category | Component | Disposition | Mitigation / Evidence | Status |
|-----------|----------|-----------|-------------|-----------------------|--------|
| T-12-01 | Information Disclosure | `tools/chatgpt.py::_fetch_message`, zweiter Leser der Projektion | mitigate | `if entry.get("message_truncated"):` steht im Quelltext (`tools/chatgpt.py:660`), `metadata["truncated"] = "true"` bleibt wörtlich (`:665`) mit Begründungskommentar (`:663`); der Wächter `tests/unit/test_chatgpt_fetch.py` ist über beide Task-Commits von 12-01 (`066d8ec..cc0037b`) unverändert, Gegenprobe per `git diff --stat` leer; Assertionen `result["metadata"]["truncated"] == "true"` (test_chatgpt_fetch.py:1373) und die Nicht-Kappung (`:1357`) grün | closed |
| T-12-02 | Tampering | `talk_browse`-Antwort, Eintrags- gegen Antwortebene | mitigate | Eigener Schlüssel je Ebene: `entry["message_truncated"] = True` (`tools/talk.py:536`) gegen `answer["truncated"] = True` (`:499`, `:719`); Quelltext-Trennung im Audit nachgerechnet, keine `answer[...]`-Zuweisung trägt den Eintragsnamen und umgekehrt; der gemeinsame Fall in einer einzigen Antwort mit getrennten Behauptungen: `test_a_cut_window_and_a_cut_message_are_two_keys_with_two_meanings` (test_talk_tools.py:735, Zeilen 760 bis 766) | closed |
| T-12-03 | Tampering | Kappungsangabe innerhalb des Nachrichtentexts | accept | Bereits mitigiert und hier nur bewahrt: die Kappung bleibt Feld statt Marker (`tools/talk.py:518-536`, ME-03 im Docstring wörtlich), und die vier Behauptungen der Kappungsstelle stehen unverändert (test_talk_tools.py:726-731: Zeichengrenze, kein Ersatzzeichen, `MARKER not in`, kein Wort im serialisierten Text). Siehe AR-12-1 | closed |
| T-12-04 | Denial of Service | Werkzeugoberfläche, `tools/list` | mitigate | `scripts/check_tool_budget.py` ist über die ganze Phase unangetastet (`git diff 066d8ec^..HEAD` leer, letzte Änderung `969cc1e` aus Phase 11); `BUDGET_BYTES = 18_000` (`:83`) und `MAX_TOOL_BYTES = 1400` (`:117`) unverändert; eigener Lauf des Audits: 15711 Bytes, 21 Werkzeuge, Exit 0 | closed |
| T-12-05 | Tampering | `tools/mail.py`, Id-Bau aus `ids.SEPARATOR` | mitigate | `ids.SEPARATOR` kommt in `src/` außerhalb von `ids.py` nicht vor (nur ein `.pyc`-Treffer), `_ID_KIND` nirgends in `src/`; die Id entsteht im Codec: `ids.encode_mail(...)` (`tools/mail.py:485`, `tools/chatgpt.py:470`) und `ids.encode_card_short(...)` (`provider_map.py:159`) mit T-12-05 im Kommentar (`:155-158`); `hit_url` liest per `ids.parse` statt per `partition` | closed |
| T-12-06 | Spoofing | `ids.parse`, `url`-Zweig | mitigate | `if not rest.strip() or rest != rest.strip():` mit dem gemeinsamen Refusal-Satz und `_HINT` (`ids.py:138-139`), Begründung mit dem Encode-Maßstab darüber (`:128-137`); drei Negativfälle `"url:   "`, `"url:  https://x/y"`, `"url:\thttps://x"` in der Parametrize-Liste (test_ids.py:216-218) plus `test_the_url_kind_reads_exactly_what_encode_url_can_build` (`:184`) | closed |
| T-12-07 | Denial of Service | `ids.parse`, strengere Lesart | accept | Inneres Whitespace bleibt erlaubt, weil `encode_url("https://a b")` genau das baut; die Entscheidung steht im Code (`ids.py:135-137`) und der Toleranz-Wächter `test_url_keeps_colons_and_slashes` ist unverändert grün. Siehe AR-12-2 | closed |
| T-12-08 | Repudiation | Verhaltensänderung der Mail-Id unbemerkt | mitigate | Der Filter, der die Byte-Identität trägt, steht im Code: `entries = [_message(item) for item in raw if _number(item.get("databaseId")) > 0]` (`tools/mail.py:435`, im Plan als 440 bis 441 zitiert, um fünf Zeilen verschoben); der Wächter `tests/unit/test_mail_tools.py` ist über beide Task-Commits von 12-02 (`7bd2f8d^..3de9dac`) unverändert (`git diff --stat` leer) und im Audit grün | closed |
| T-12-09 | Spoofing | `provider_map.PROVIDER_KINDS`, Einträge ohne Beleg | mitigate | Alle sechs Einträge tragen "Verified against nextcloud/" plus einen `.php`-Pfad (`provider_map.py:55-86`); die zwei Nachzieher nennen zusätzlich den Release-Tag: `v34.0.0` für `files` samt Doppelspur-Begründung zu `_file_id`, `v6.0.2` für `notes` samt `Application.php:28` und der Ableitung über `_last_numeric_segment`. Vollständigkeits-Skript des Plans im Audit nachgelaufen: "every provider entry carries its proof"; `PROVIDER_KINDS` selbst unverändert, eingefrorener Mengen-Halter `test_the_provider_table_is_not_a_list_of_installed_apps` grün. Abweichung siehe UF-1 | closed |
| T-12-10 | Information Disclosure | `tools/context.py`, Mail-Nachrichtenebene | mitigate | Regressionstest `test_no_line_of_this_module_asks_mail_for_level_messages` (test_tools_context.py:1853) über die geteilte Prüffunktion `_message_level_calls` (`:1838`), Nadel `level="messages"` (`:1835`); der bestehende Verhaltenstest zu T-11-29 ist unverändert. Damit ist UF-2 aus 11-SECURITY.md geschlossen | closed |
| T-12-11 | Repudiation | Gate ohne Gegenprobe | mitigate | Beide neuen Gates haben Gegenprobe und Nicht-leer-Anker über dieselbe Funktion: Quelltext-Gate mit `test_the_message_level_gate_notices_the_call_and_leaves_the_prose_alone` (test_tools_context.py:1874) und den Ankern `source.strip()`, `"mail_tools" in source`, `level="accounts"` (`:1868-1870`, Anker bewusst nicht die manipulierte Zeile, Grund im Kommentar); Vokabular-Gate mit `test_the_widened_vocabulary_gate_reports_the_word_with_its_line` (test_exapp_env_setup.py:2098) und `test_the_vocabulary_gate_reads_a_list_that_is_not_empty` (`:2056`) | closed |
| T-12-12 | Repudiation | `docs/store-submission.md`, datierte Proof-Zeilen | accept | Die Datei ist benannte Ausnahme `VOCABULARY_EXCEPTION` (test_exapp_env_setup.py:1978) mit der Begründung im Docstring des Gates (`:2040-2042`), keine nachträgliche Umformulierung eines Protokolls; prüfbar gemacht über die positive Behauptung `test_the_store_archive_carries_no_exempt_page` (`:2075`), die die Dateiliste aus `scripts/build_store_release.sh` liest (`archive_members`, `:2028-2031`). Siehe AR-12-3 | closed |
| T-12-13 | Tampering | Wortliste an zwei Stellen | mitigate | `FORBIDDEN_VOCABULARY = "archiv"` ist über `tests/**/*.py` genau einmal definiert (test_exapp_env_setup.py:1686, im Audit per Grep über den ganzen Testbaum nachgeprüft); Manifest-Anwendung (`:1788`), Beschreibungs-Halter (`:1874`) und die neue Markdown-Prüfung (`vocabulary_findings`, `:1993`) lesen dieselbe Konstante | closed |
| T-12-14 | Elevation of Privilege | `tools/chatgpt.py` zu `tools/talk.py`, Privat-Durchgriff | mitigate | `async def one_room(...)` ist öffentlich und nennt den Aufrufer samt Grund für die Sichtbarkeit im Docstring (`tools/talk.py`, Absatz "Public for the same reason `one_message` is", mit `tools/chatgpt.py`, `fetch`, TOOL-19 und dem Gate als Halter); der Aufrufer geht durch die Vordertür (`tools/chatgpt.py:623`), `talk_tools._room` kommt in `src/` nicht mehr vor; AST-Gate `tests/contract/test_module_boundaries.py` mit `test_no_module_reaches_into_the_privates_of_a_tool_module` (`:170`) über alle `.py` unter `src/mcp_connector` (`_source_files`), fünf Tests grün, `ruff check --select SLF src/` im Audit: 2 Treffer, beide `oauth/provider.py`, keiner in `tools/` | closed |
| T-12-15 | Information Disclosure | Mitigation von T-09-21 im Docstring von `_room` | mitigate | Der Absatz ist wörtlich mitgewandert: derselbe Satz über `GET /room/{token}`, "counted brute force attempt against the address of this container", die `429` und `threat T-09-21` stehen im Docstring von `one_room` (`tools/talk.py`); die Phase-11-Dokumente sind unangetastet (`git diff --stat 066d8ec^..HEAD -- .planning/phases/11-b-ndelung-budget-und-release-0-1-6/` leer; der Pfad existiert seit `661c609` nicht mehr, das Zitat lebt in der Historie und wurde nicht zurückgeschrieben) | closed |
| T-12-16 | Repudiation | Erklärende Prosa in `tools/context.py` | mitigate | AST statt Grep: das Gate wandelt über `ast.ImportFrom` (`test_module_boundaries.py:109`, `:156`) und `ast.Attribute` (`:164`), Docstrings und Kommentare sind keine Attribut-Knoten; die Gegenprobe schickt die echte `tools/context.py` durch die Prüfung und erwartet null Funde (`test_the_gate_stays_green_on_the_module_that_explains_its_neighbours`, `:227-243`), Begründung im Modul-Docstring (`:13-19`). Kein erklärender Satz musste gekürzt werden | closed |
| T-12-17 | Spoofing | README-Beispiel mit `spreed` | mitigate | `spreed` kommt in keinem der drei READMEs mehr vor (Grep leer), `"provider":"talk-conversations"` steht in README.md:372, README.de.md:381, README.fr.md:389; Halter `test_every_provider_id_in_the_readmes_is_one_that_exists` (test_provider_map.py:362) über `READMES` (`:334`) und `REAL_BUT_UNREGISTERED` (`:342`) mit Gegenprobe, die genau `{"spreed"}` als unerklärt zurückmeldet (`:398`); `kind=url` und `resolvable=false` daneben sind durch `test_a_talk_conversation_hit_stays_a_url_because_a_conversation_is_no_document` belegt | closed |
| T-12-18 | Tampering | Lint-Ausnahmen als Kollateralschaden eines Gates | accept | `ruff --select SLF` bewusst nicht eingeführt; die Messung steht im Modul-Docstring des Gates (`test_module_boundaries.py:22-28`: drei Treffer in `src/` vor der Umbenennung, 53 in `tests/`, zwei `noqa` plus `per-file-ignores` als Preis, andere Aussage als das Requirement) und wurde im Audit gegengeprüft: heute 2 in `src/`, 53 in `tests/`. Siehe AR-12-4 | closed |
| T-12-SC (4x) | Tampering | Paketinstallation | mitigate | Über die ganze Phase (`066d8ec^..HEAD`) ändert sich an `pyproject.toml` und `uv.lock` keine Zeile (`git diff --stat` leer). Kein `uv add`, kein `pip install`, kein `npm install`; das neue Gate benutzt nur `ast` und `pathlib` aus der Standardbibliothek (`test_module_boundaries.py:31-32`). Der einzige Netzzugriff der Phase war ein lesender `curl` auf `raw.githubusercontent.com` an zwei Release-Tags (12-03-SUMMARY.md:82-90) | closed |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-12-1 | T-12-03 | Die Kappung eines Nachrichtentexts bleibt ein Feld neben dem Text und wird in dieser Phase nicht umgebaut. Ein Marker im Text wäre der Einfallsweg (ME-03), und jeder Teilnehmer einer Konversation darf Text schreiben; die vier Behauptungen der Kappungsstelle bleiben deshalb wörtlich stehen, statt dass eine Umbenennung sie mitzieht (`tools/talk.py:518-536`, test_talk_tools.py:726-731) | Audit-Lauf (Plan-Disposition 12-01) | 2026-08-25 |
| AR-12-2 | T-12-07 | Inneres Whitespace in einer `url:`-Id bleibt erlaubt. Eine strengere Prüfung als `encode_url` würde gültige Ids ablehnen und Aufrufer in eine Wiederholungsschleife schicken, die Mitigation wäre also selbst der Schaden. Der Maßstab ist ausdrücklich die Spiegelseite und steht im Code (`ids.py:135-137`) | Audit-Lauf (Plan-Disposition 12-02) | 2026-08-25 |
| AR-12-3 | T-12-12 | `docs/store-submission.md` bleibt vom Vokabular-Gate ausgenommen und wird nicht bereinigt: die Datei ist ein Protokoll mit datierten Proof-Zeilen, und eine nachträgliche Umformulierung würde die Beweisrichtung umdrehen (T-11-63). Die Ausnahme hängt nicht an Prosa, sondern an der positiven Behauptung über die Paketliste aus `scripts/build_store_release.sh` (test_exapp_env_setup.py:2075) | Audit-Lauf (Plan-Disposition 12-03) | 2026-08-25 |
| AR-12-4 | T-12-18 | `ruff --select SLF` wird nicht eingeführt. Gemessen statt vermutet: zwei `noqa`-Zeilen in `oauth/provider.py` plus ein `per-file-ignores` für 53 legitime Treffer in `tests/`, und danach prüft die Regel eine andere Aussage als TOOL-19. Das AST-Gate prüft die gemeinte Aussage direkt (`test_module_boundaries.py:22-28`) | Audit-Lauf (Plan-Disposition 12-04) | 2026-08-25 |
| AR-12-5 | T-12-13, Reichweite | `LICENSE` trägt das verbotene Wort in Zeile 653 im AGPL-3.0-Volltext und ist als `VERBATIM_ARCHIVE_TEXT` benannte zweite Ausnahme: Fremdtext, dessen Bearbeitung einen Lizenztext verfälschen würde. Ebenso bleiben `scripts/*.sh` außerhalb der Reichweite, weil dort ein Variablenname und ein Werkzeugname gemeint sind und nicht die Hausregel (12-03-SUMMARY.md:100-103, 109-116) | Ausführung 12-03 (Rule-1-Autofix), im Audit bestätigt | 2026-08-25 |

*Accepted risks do not resurface in future audit runs.*

---

## Unregistered Flags (WARNING, geprüft, kein Blocker)

1. **UF-1, Klassenangabe und Tag in `PROVIDER_KINDS`.** T-12-09 verlangt den Beleg mit
   "Repository, Datei, Klasse und Verhalten für jeden Eintrag, am Release-Tag gelesen". Der
   Audit-Lauf des Vollständigkeits-Skripts zeigt: alle sechs Einträge nennen Repository und
   eine `.php`-Datei, fünf nennen eine Klasse, und nur die zwei Nachzieher `files` und
   `notes` nennen einen Release-Tag. Ohne Klassenangabe bleibt
   `search-deck-card-board` ("Verified against nextcloud/deck lib/Search/DeckProvider.php."),
   der Eintrag aus Phase 1. Die automatisierte Prüfung des Plans verlangt `class ` nur für
   `files` und `notes`, die Akzeptanzkriteriums-Zeile formuliert es für alle sechs. Die
   geschützte Eigenschaft, keine Zuordnung ohne benannte fremde Fundstelle, hält; der
   eingefrorene Mengen-Halter deckt die ganze Tabelle. Deshalb CLOSED mit benannter
   Abweichung, und ein billiger nächster Schritt ist die Klassenangabe für Deck.
2. **UF-2, zwei `title`-Felder ohne Marker-Filter.** Der Review-Fix WR-04 (`85859e6`) hat
   Datei-, Notiz- und Kartentitel durch `marks.without_marks` gelegt
   (`tools/chatgpt.py:272`, `:293`, `:320`), zusätzlich zu Mail, Message und Table. Zwei
   Rückgaben derselben Datei tun es weiter nicht: die Suchtreffer-Projektion
   (`:183` Titel, `:184` Text aus `subline`) und der Kalendereintrag (`:391`,
   `str(event["summary"])`). Beide sind Fremdtext derselben Klasse wie die drei gefixten
   Zweige. Kein Blocker, weil keine Registerzeile dieser Phase sie nennt und weil der
   Review sie nicht als Warnung geführt hat; Kandidat für den nächsten Härtungs-Nachzieher.
3. **UF-3, deferred Review-Findings mit Sicherheitsbezug, informativ.** Die drei Infos aus
   `12-REVIEW.md` sind nicht gefixt und nicht Teil des Registers: IN-01 (der Kommentar an
   `provider_map.hit_url` behauptet eine Unerreichbarkeit, die für einen Talk-Treffer mit
   gefüllten Attributen und leerem `resourceUrl` nicht gilt; Verhalten defensiv in Ordnung,
   Kommentar falsch), IN-02 (der `fetch`-Hint reflektiert für eine `url:`-Id eine
   unvalidierte Adresse mit der Aufforderung, sie zu öffnen; der Server holt sie nie,
   T-01-75 bleibt dicht), IN-03 (`talk.send` schickt eine Nachricht aus nur Whitespace mit
   zwei Anfragen auf die Reise, statt sie ohne Anfrage abzulehnen).
4. **UF-4, Prozesshinweis zu `## Threat Flags`.** Nur zwei der vier SUMMARYs tragen den
   Abschnitt (12-02, 12-04), beide melden "keine neue sicherheitsrelevante Oberfläche".
   12-01 und 12-03 tragen ihn nicht; ihre Pläne wurden einzeln gegen das Register geprüft,
   es wurde keine ungemappte Fläche gefunden (12-01 benennt seine Antwortformat-Änderung in
   einem eigenen Abschnitt, 12-03 fügt nur Kommentare und Prüfungen hinzu).
5. **Neue Fläche aus dem Review-Fix-Pass**, nicht im Plan-Register, geprüft und mit den
   bestehenden Threats vereinbar: die ASCII-Ziffernprüfung in `provider_map` an drei Stellen
   plus Backstop in `nextcloud/clients/dav.py:292` (`a3a846b`, verschärft die Klasse von
   T-11-03), die engere Lesart von `file:`, `note:` und `event:` in `ids.parse`
   (`6318ba0`, dieselbe Symmetrie, die T-12-06 für `url:` hergestellt hat), die
   Import-Kante des AST-Gates (`60ac592`, erweitert T-12-14 um den direkten Symbol-Import),
   der rekursive Lauf des Vokabular-Gates über `docs/` (`a7ee8ee`, erweitert T-12-13) und
   die Direkttests für `encode_card_short` (`c9a6f9d`, deckt die `_join`-Refusals ab, auf
   die T-12-05 sich verlässt). Alle fünf bringen eigene Tests mit und sind Härtungen, keine
   Erweiterungen der Angriffsfläche; keiner hat ein Gate angehoben.
6. **Nachzieher aus 11-SECURITY.md, hier geschlossen:** UF-1 aus Phase 11
   (Kommentarabdeckung von `PROVIDER_KINDS`) ist bis auf die Klassenangabe für Deck
   erledigt (siehe UF-1 oben), UF-2 (fehlendes Quelltext-Gate zu T-11-29) ist als
   Regressionstest im Baum (T-12-10), und AR-11-2 (Reichweite des Vokabular-Gates) ist auf
   READMEs, `CHANGELOG.md` und `docs/` rekursiv ausgeweitet, mit zwei benannten Ausnahmen
   (T-12-12, T-12-13, AR-12-3, AR-12-5).

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-08-25 | 19 (18 nummeriert + T-12-SC 4x) | 19 | 0 | gsd-security-auditor (opus) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-08-25
