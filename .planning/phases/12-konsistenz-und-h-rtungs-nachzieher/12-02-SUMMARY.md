---
phase: 12-konsistenz-und-h-rtungs-nachzieher
plan: 02
subsystem: api
tags: [python, ids, codec, mcp, mail, unified-search]

# Dependency graph
requires:
  - phase: 10-mail
    provides: "ids.encode_mail und der mail-Zweig von ids.parse"
  - phase: 11
    provides: "Review-Befund IN-04 (url-Zweig liest mehr, als encode_url baut)"
provides:
  - "Die Mail-Id der mail_browse-Projektion kommt aus ids.encode_mail statt aus ids.SEPARATOR"
  - "ids.encode_card_short als Encode-Seite der schon akzeptierten Kurzform card:<cardId>"
  - "provider_map baut und liest Ids ausschliesslich ueber den Codec"
  - "Der url-Zweig von ids.parse lehnt whitespace-only und fuehrenden Whitespace ab"
  - "Drei Negativtests plus ein Spiegelsymmetrie-Test in tests/unit/test_ids.py"
affects: [12-03, 12-04, 13-release]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Encode und Parse sind spiegelbildlich: parse akzeptiert genau die Menge, die encode bauen kann"
    - "Jede akzeptierte Id-Form hat eine encode-Funktion; sonst baut ein Aufrufer den Praefix selbst"

key-files:
  created: []
  modified:
    - src/mcp_connector/tools/mail.py
    - src/mcp_connector/ids.py
    - src/mcp_connector/provider_map.py
    - tests/unit/test_ids.py

key-decisions:
  - "Whitespace im url-Rest: whitespace-only und fuehrender Whitespace werden abgelehnt, inneres Whitespace bleibt erlaubt; Massstab ist encode_url, das immer strippt und einen leeren Wert ablehnt"
  - "Die whitespace-only Haelfte steht ausgeschrieben im url-Zweig, obwohl der aeussere strip von parse sie heute schon erledigt, damit die Zusage nicht an einer Zeile haengt, die aus einem anderen Grund dort steht"
  - "ids.encode_card_short neu eingefuehrt, weil parse die Kurzform card:<cardId> seit Phase 1 akzeptiert, der Codec sie aber nicht bauen konnte und provider_map sie deshalb von Hand baute"
  - "provider_map.hit_url liest eine url-Id per ids.parse statt per partition; ein Handsplit haette bei jeder anderen Id-Art das nackte Id-Segment als Link zurueckgegeben"

patterns-established:
  - "Spiegelsymmetrie-Test: ein Test behauptet beide Richtungen der Grenze (was abgelehnt wird und was erlaubt bleibt), nicht nur die einzelne Ablehnung"

requirements-completed: [TOOL-18]

# Metrics
duration: 10min
completed: 2026-08-25
---

# Phase 12 Plan 02: Der Id-Codec ist die einzige Quelle Summary

**Jede Id im Produktionsbaum entsteht jetzt in `ids.py`, und `ids.parse` liest im `url`-Zweig genau die Menge, die `ids.encode_url` bauen kann.**

## Performance

- **Duration:** 10 min
- **Started:** 2026-08-25T14:34:00Z
- **Completed:** 2026-08-25T14:44:00Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- `tools/mail.py` baut seine Id über `ids.encode_mail`; die Konstante `_ID_KIND` und der Kommentar, der den abgeschlossenen Plan 10-05 als Zukunft beschrieb, sind weg.
- `provider_map.py` war der zweite, im Plan nicht erfasste Handbau: die Deck-Kurzform kommt jetzt aus dem neuen `ids.encode_card_short`, und `hit_url` liest eine `url`-Id über `ids.parse` statt über `partition(ids.SEPARATOR)`.
- Der `url`-Zweig von `ids.parse` lehnt einen Rest ab, der nur aus Whitespace besteht, und einen Rest, der mit Whitespace beginnt. Inneres Whitespace bleibt bewusst erlaubt.
- `tests/unit/test_ids.py` hält drei neue Ablehnungen in der bestehenden Parametrize-Liste und einen eigenen Test für die Spiegelsymmetrie.
- `ids.SEPARATOR` kommt außerhalb von `src/mcp_connector/ids.py` nicht mehr vor, `_ID_KIND` nirgends in `src/`.

## Task Commits

1. **Task 1: Die Mail-Id kommt aus dem Codec** - `7bd2f8d` (refactor)
2. **Task 2: Der url-Zweig akzeptiert genau, was encode_url baut** - `3de9dac` (fix)

## Files Created/Modified

- `src/mcp_connector/tools/mail.py` - `_ID_KIND` samt stale Kommentar entfernt, `"id": ids.encode_mail(_number(raw.get("databaseId")))`
- `src/mcp_connector/ids.py` - neue Funktion `encode_card_short`, Guard plus Begründungskommentar im `url`-Zweig von `parse`
- `src/mcp_connector/provider_map.py` - Kurzform über den Codec, `hit_url` liest per `ids.parse`
- `tests/unit/test_ids.py` - drei Negativfälle (`"url:   "`, `"url:  https://x/y"`, `"url:\thttps://x"`) und `test_the_url_kind_reads_exactly_what_encode_url_can_build`

## Decisions Made

**Die Auslegung von "Whitespace im Rest"** (im Plan festgelegt, hier protokolliert): Maßstab ist die Spiegelseite. `encode_url` baut `url:` plus `url.strip()` und lehnt einen leeren Wert ab. Genau diese Menge darf `parse` lesen, keine größere:

- Ein Rest, der nur aus Whitespace besteht, wird abgelehnt (`not rest.strip()`). Diese Hälfte war schon vorher wahr, aber nur mittelbar: der äußere `strip` in `parse` räumt den Rest von `"url:   "` komplett weg, worauf der gemeinsame Refusal greift. Die Prüfung steht jetzt ausdrücklich im `url`-Zweig, damit die Zusage nicht an einer Zeile hängt, die aus einem anderen Grund dort steht.
- Ein Rest, der mit Whitespace beginnt, wird abgelehnt (`rest != rest.strip()`). Das war der wirklich erreichbare Bruch: `parse("url:  https://x/y")` lieferte vorher `("url", ("  https://x/y",))`, also einen Wert, den `encode_url` nie baut.
- Inneres Whitespace bleibt erlaubt: `encode_url("https://a b")` baut genau `"url:https://a b"`, eine Ablehnung wäre strenger als die Encode-Seite und würde die Asymmetrie nur umdrehen (T-12-07, bewusst akzeptiert). Der Toleranz-Wächter `test_url_keeps_colons_and_slashes` ist unverändert und grün.

**Byte-Identität der Mail-Id protokolliert:** `mail_browse(level="messages")` filtert `_number(item.get("databaseId")) > 0`, bevor `_message` läuft. Kein Wert, der diesen Filter passiert, kann `_join` zu einem Refusal bringen, also ist die Ausgabe zeichengleich mit vorher. Belegt und nicht behauptet: `tests/unit/test_mail_tools.py` ist unverändert (keine Zeile im Diff) und grün, ebenso `tests/unit/test_chatgpt_fetch.py`.

**Nicht in den Changelog von 0.1.9:** Beide Änderungen sind nicht nutzersichtbar. Die Mail-Id ist byte-identisch, und die neuen Ablehnungen betreffen `url:`-Formen, die kein Suchtreffer dieses Servers jemals ausgegeben hat (`encode_url` strippt seit Phase 1). Die einzige nutzersichtbare Änderung der Phase 12 bleibt `message_truncated` aus Plan 12-01.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `provider_map.py` war der zweite Handbau, den der Plan nicht kannte**

- **Found during:** Task 1 (erste Handlung war `grep -rn "_ID_KIND" src/`, direkt danach `grep -rn "ids.SEPARATOR" src/`)
- **Issue:** Der Plan nennt `mail.py:490` "den einzigen verbliebenen Handbau im Produktionsbaum". Das ist falsch. `provider_map.py:142` baute die Deck-Kurzform als `f"card{ids.SEPARATOR}{card_id}"`, und `provider_map.py:173` las eine `url`-Id per `identifier.partition(ids.SEPARATOR)[2]`. Beide sind Code-Zeilen mit `ids.SEPARATOR` außerhalb von `ids.py`, und damit hätte der Prüfschritt von Task 1 (und Punkt 3 der `<verification>`, und das Akzeptanzkriterium "`ids.SEPARATOR` wird außerhalb von `ids.py` nirgends mehr benutzt") zwingend rot gemeldet, egal wie sauber `mail.py` geändert wird.
- **Fix:** Zwei Änderungen, minimal und in der vom Plan festgelegten Richtung (T-12-05: der Codec ist die einzige Quelle). (a) Neue Funktion `ids.encode_card_short(card_id)` als Encode-Seite der Kurzform, die `parse` seit Phase 1 akzeptiert (`test_short_card_form_is_accepted`); ohne sie kann der eine Aufrufer, der sie braucht, den Präfix nur selbst bauen. (b) `hit_url` liest die `url`-Id per `ids.parse` und gibt `base_url` zurück, wenn die gelesene Art keine `url` ist. Das ist zugleich eine Korrektur: der alte Handsplit hätte bei jeder anderen Id-Art das nackte Id-Segment (etwa `"5"` aus `note:5`) als Link zurückgegeben, was kein Link ist.
- **Files modified:** `src/mcp_connector/ids.py`, `src/mcp_connector/provider_map.py`
- **Verification:** Der Prüfschritt aus Task 1 meldet "the codec is the only place that builds an id string"; `tests/unit/test_provider_map.py` ist unverändert und grün (die Datei erreicht die geänderte Zeile in `hit_url` nie, weil alle ihre Fälle ein `resourceUrl` tragen); `vulture` bleibt grün, weil `encode_card_short` genau einen Aufrufer hat.
- **Committed in:** `7bd2f8d` (Task-1-Commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Notwendig, damit der Prüfschritt des Plans überhaupt grün werden kann; die Erweiterung bleibt innerhalb der erklärten Absicht (T-12-05) und ändern kein Verhalten, das ein Test vorher festhielt. Kein Scope Creep: `pyproject.toml`, `uv.lock`, `appinfo/info.xml`, `CHANGELOG.md` und `scripts/check_tool_budget.py` sind unangetastet.

**Hinweis für Plan 12-03:** Der Plan 12-03 ändert `provider_map.py` ebenfalls (SEC-02a, Verifikationskommentare an `PROVIDER_KINDS`). Die hier geänderten Zeilen liegen in `extract_id` und `hit_url`, nicht in der Tabelle; die beiden Änderungen berühren sich nicht.

## Issues Encountered

Keine. Alle Gates liefen im ersten Anlauf grün: `ruff check .`, `ruff format --check .`, `pyright` (0 errors), `pytest -q` (vollständige Suite), `pytest tests/contract -q`, `vulture src scripts vulture_whitelist.py`.

## Threat Flags

Keine neue sicherheitsrelevante Oberfläche. Beide Änderungen verengen die akzeptierte Eingabemenge und fügen keinen Netzwerkpfad, keinen Auth-Pfad und keinen Dateizugriff hinzu.

## Byte-Stand

`tools/list`: 15711 Bytes, 21 Tools, Budget 18000 (unverändert gegenüber 12-01). Größtes Tool `mail_browse` mit 1376 Bytes gegen `MAX_TOOL_BYTES` 1400.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- TOOL-18 ist erledigt, ROADMAP SC2 der Phase 12 erfüllt.
- Plan 12-03 (TOOL-19 plus SEC-02a) kann laufen; `provider_map.py` ist an den dort adressierten Stellen unverändert.

## Self-Check: PASSED

Alle vier geänderten Dateien und die SUMMARY existieren auf der Platte, beide Commit-Hashes (`7bd2f8d`, `3de9dac`) stehen im Log, und `tests/unit/test_mail_tools.py` hat über beide Commits hinweg null geänderte Zeilen.

---
*Phase: 12-konsistenz-und-h-rtungs-nachzieher*
*Completed: 2026-08-25*
