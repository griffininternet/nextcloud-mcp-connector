---
phase: 05-hardening-und-store-einreichung
plan: 16
subsystem: docs
tags: [gap-closure, mucgpt, truth-4, backlog, deferred-items, owner-decision]

# Dependency graph
requires:
  - phase: 05-hardening-und-store-einreichung
    plan: 07
    provides: "die Form, in der ein verprobter Client in diesem Projekt belegt wird (05-07-MEASUREMENTS.md: Topologie-Tabelle, nummerierte Pruefschritte, woertliche Logzeilen, Gegenprobe)"
  - phase: 05-hardening-und-store-einreichung
    plan: 15
    provides: "die geschlossenen Funde CR-01 und WR-01 bis WR-03; IN-01 bis IN-06 blieben bewusst offen fuer diesen Plan"
provides:
  - "docs/client-setup.md: Abschnitt 'Closing the gap: the protocol, three checks in the order they can fail' im MUCGPT-Teil, mit Voraussetzungen, drei Pruefpunkten samt Notierpflicht, Gegenprobe und der Identitaetsfrage aus BL-12"
  - "BACKLOG BL-12, Abschnitt 'Verprobung offen': Trigger, Verweis auf das Protokoll, dieselben drei Pruefpunkte, Abschlussbedingung"
  - "BACKLOG BL-13: die sechs Advisory-Funde IN-01 bis IN-06 mit Datei, Fund und vorgeschlagenem Fix als Tabelle"
  - "deferred-items.md: je eine Zeile fuer die offene MUCGPT-Verprobung und fuer IN-01 bis IN-06"
  - "Schriftliche Owner-Entscheidung zu Truth 4 und EXAPP-05 (option-b)"
affects: [EXAPP-05, docs/client-setup.md, .planning/BACKLOG.md]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Eine Luecke, die nicht geschlossen werden kann, wird einloesbar gemacht: statt einer Absichtserklaerung ein Protokoll mit Voraussetzungen, Pruefreihenfolge und Notierpflicht, damit sie in einer Sitzung abgearbeitet werden kann"
    - "Pruefpunkte werden in der Reihenfolge notiert, in der sie scheitern koennen; jeder Punkt nennt, was zu notieren ist, damit der Nachweis dieselbe Form hat wie die bereits belegten Clients"
    - "Ein offener Punkt wird an genau zwei gefuehrten Stellen getragen (BACKLOG plus deferred-items.md) statt im Fliesstext einer Doku"

key-files:
  created: []
  modified:
    - docs/client-setup.md
    - .planning/BACKLOG.md
    - .planning/phases/05-hardening-und-store-einreichung/deferred-items.md

key-decisions:
  - "option-b: EXAPP-05 wird mit der dokumentierten, gefuehrten Luecke abgenommen; option-a ist nicht ausfuehrbar, weil kein Zugang zu einer MUCGPT-Instanz samt Keycloak besteht"
  - "Das Protokoll steht in docs/client-setup.md und nicht in der Planung, weil es die Person adressiert, die den Zugang hat, und die liest die Doku und nicht .planning/"
  - "Der Absatz 'A gap, named up front' bleibt woertlich stehen und zeigt nur noch auf das Protokoll: die Ehrlichkeit der Seite ist der Grund, warum die Luecke ueberhaupt sichtbar ist"
  - "Die drei Pruefpunkte stehen wortgleich in docs/client-setup.md und in BL-12, damit Doku und Backlog nicht auseinanderlaufen"
  - "Die Werkzeugzahl im Protokoll ist mit dem Contract-Test verankert (tests/contract/test_tool_surface.py) statt mit einer Zahl im Text, weil IN-04 genau diese Divergenz beschreibt"

patterns-established:
  - "Gap-Closure ohne Code: eine Wahrheit, die an einem fremden System haengt, wird durch Protokoll, Fuehrung an zwei Stellen und schriftliche Entscheidung abgeschlossen"

requirements-completed: [EXAPP-05]

# Metrics
duration: 20min
completed: 2026-08-20
---

# Phase 05 Plan 16: Gap Closure MUCGPT und Truth 4 Summary

Die einzige unsichere Wahrheit der Phase ist abgeschlossen, ohne dass eine fremde Instanz
dafuer noetig war: der MUCGPT-Abschnitt traegt jetzt ein abhakbares Verprobungsprotokoll, die
Luecke ist an zwei gefuehrten Stellen sichtbar, die sechs Advisory-Funde des Reviews sind als
BL-13 gefuehrt, und die Owner-Entscheidung steht schriftlich.

## Owner-Entscheidung

**Gewaehlte Option: `option-b` (Mit dokumentierter Luecke abnehmen)**, entschieden am
**2026-08-20**.

Begruendung im Wortlaut der Entscheidung: Eine MUCGPT-Verprobung ist ohne Zugang zu einer
fremden Instanz samt Keycloak (Stadt Muenchen, it@M) nicht durchfuehrbar; der Kontakt laeuft
ausschliesslich ueber den Owner und ist als Follow-up bereits vorgemerkt (BL-12). Entscheidung
getroffen im Auto-Modus durch den Orchestrator am 2026-08-20, da option-a physisch nicht
ausfuehrbar ist. Die Luecke bleibt ueber BL-12 und deferred-items.md gefuehrt und wird mit dem
Verprobungsprotokoll eingeloest, sobald Zugang besteht.

Damit wird **Truth 4 aus 05-VERIFICATION.md** (sechs von sieben Client-Abschnitten live
verprobt) mit der gefuehrten Luecke abgenommen, und **EXAPP-05** gilt als erfuellt. Die beiden
Orte, an denen die Luecke gefuehrt ist:

1. `.planning/BACKLOG.md`, BL-12, Abschnitt "Verprobung offen (verification still open, plan
   05-16)": Trigger, Protokollverweis, die drei Pruefpunkte, Abschlussbedingung.
2. `.planning/phases/05-hardening-und-store-einreichung/deferred-items.md`, Zeile "05-16,
   Task 1" zur offenen MUCGPT-Verprobung.

Es wurde nichts an Dritte gesendet: kein Mailentwurf, keine Nachricht, kein Formular. Outreach
loest ausschliesslich der Owner selbst aus.

## Was sich im MUCGPT-Abschnitt geaendert hat

Vorher endete der Absatz "A gap, named up front" mit einem Satz, der die drei Dinge nennt, die
zu pruefen waeren. Das war eine Absichtserklaerung: es fehlten die Voraussetzungen, die
Reihenfolge und vor allem, was ein Ergebnis ueberhaupt festhalten muss, damit es spaeter noch
etwas beweist.

Neu ist der Abschnitt "Closing the gap: the protocol, three checks in the order they can fail"
am Ende des MUCGPT-Teils:

| Teil | Inhalt |
|------|--------|
| Voraussetzungen | Instanz samt Keycloak und ein Konto darauf, dieser Connector ueber https erreichbar samt `/mcp`-Adresse, ein eigenes Nextcloud-Konto mit eigenem App-Passwort plus die zwei `config.yaml`-Zeilen (`forward_token: true` und `forward_auth_override`), Zugang zum Container-Log |
| Topologie zuerst | MUCGPT-Version und Image-Digest, Version des Connectors, Wert von `NC_MCP_PUBLIC_URL`, Datum und Uhrzeit des Laufs, in der Form der Tabelle aus 05-07-MEASUREMENTS.md |
| Pruefpunkt 1 | Kommt der `Authorization`-Header ueberhaupt an? Zu notieren: die von MUCGPT geloggten Headernamen fuer die Quelle und der Status der ersten `POST /mcp`-Zeile im Log. `401` heisst, die Zugangsdaten kamen nie an (fast immer der `headers`-Block statt der zwei Schluessel) |
| Pruefpunkt 2 | Kommt die Werkzeugliste zurueck? Zu notieren: die Anzahl der gelisteten Werkzeuge (verankert an `tests/contract/test_tool_surface.py`) und ob die Namen zu dieser Seite passen |
| Pruefpunkt 3 | Antwortet ein Werkzeugaufruf mit Inhalten des konfigurierten Kontos? Zu notieren: aufgerufenes Werkzeug, `POST /mcp 200` im Log, ein Detail der Antwort, das nur aus diesem Konto stammen kann, plus die Gegenprobe mit einer Datei, die das Konto nicht sehen darf |
| Identitaetsfrage | Ein `forward_auth_override` pro Quelle heisst: alle MUCGPT-Nutzer laufen unter einem Nextcloud-Konto, die einzige Stelle, an der die Kernzusage des Projekts nicht gilt. Wer das Protokoll faehrt, soll fragen, ob ein Team- oder Servicekonto reicht oder ob Pro-Nutzer-Treue gebraucht wird (BL-12) |
| Abschluss | Ergebnis als Messdatei neben die anderen, dann ersetzt eine datierte Zeile den Luecken-Absatz |

Der Absatz "A gap, named up front" bleibt woertlich stehen; nur sein letzter Satz zeigt jetzt
auf das Protokoll statt die drei Punkte lose aufzuzaehlen.

## Gefuehrte Restposten

| Nummer | Gegenstand | Trigger | Zweite Fuehrung |
|--------|------------|---------|-----------------|
| BL-12 | MUCGPT-Verprobung offen: der Abschnitt ist aus dem Quelltext von `it-at-m/mucgpt` (Stand 2026-08-18) abgeleitet, nicht aus einem Lauf. Der neue Abschnitt "Verprobung offen" nennt Trigger, Protokoll, die drei Pruefpunkte und die Abschlussbedingung | Zugang zu einer laufenden MUCGPT-Instanz samt Keycloak, ueblicherweise ueber den it@M-Kontakt der Outreach-Linie; der Kontakt ist Sache des Owners | `deferred-items.md`, Zeile "05-16, Task 1" (MUCGPT) |
| BL-13 | Die sechs Advisory-Funde IN-01 bis IN-06 aus 05-REVIEW.md, als Tabelle mit Id, Datei, Fund und dem im Review vorgeschlagenen Fix | Das naechste Mal, wenn eine der genannten Dateien ohnehin geoeffnet wird; keiner der sechs ist ein Blocker | `deferred-items.md`, Zeile "05-16, Task 1" (IN-01 bis IN-06) |

BL-13 im Ueberblick: IN-01 (Body-Schranke des Purge-Handlers per Chunked-Encoding umgehbar,
`purge.py:283-306`), IN-02 (doppelte Opener-Logik in `connect.py:127-146` gegen
`store.py:1275-1310`), IN-03 (toter `doc_url`-Link im Admin-Formular auf frischer Installation,
`admin_settings.py:80-89`), IN-04 (15 gegen 16 Werkzeuge in `oauth-setup.md` gegen
`client-setup.md` und `store-submission.md`), IN-05 (`privacy.md:38` liest sich, als lagen
Client-Secrets im Klartext), IN-06 (Consent-Screen wird einem pausierten Konto beim Reload noch
gerendert, `consent.py:302-304`).

## Tasks Completed

| Task | Name | Commit | Dateien |
|------|------|--------|---------|
| 1 | Verprobungsprotokoll im MUCGPT-Abschnitt und die zwei gefuehrten Eintraege | `785bfe9` | `docs/client-setup.md`, `.planning/BACKLOG.md`, `.planning/phases/05-hardening-und-store-einreichung/deferred-items.md` |
| 2 | Owner entscheidet ueber die MUCGPT-Verprobung (checkpoint:decision) | dieses SUMMARY | keine Codedatei; Entscheidung im Abschnitt "Owner-Entscheidung" |

## Deviations from Plan

Keine. Der Plan wurde ausgefuehrt wie geschrieben.

Kein Quellcode wurde angefasst: `git status --porcelain src tests scripts` ist leer. Die
Dreisprachigkeit fiel nicht an, weil weder README noch Store-Text beruehrt wurden; die Regel
haette gegriffen, wenn der Lauf einen README-Satz veraendert haette.

## Threat Flags

| Threat ID | Kategorie | Disposition | Umsetzung |
|-----------|-----------|-------------|-----------|
| T-05-61 | Information Disclosure | mitigate | Im neuen Abschnitt steht kein echter Hostname und kein echtes App-Passwort: die einzige Adresse ist `https://<nextcloud>/exapps/mcp_connector/mcp` im Platzhalterstil der Nachbarabschnitte, das App-Passwort wird nur als Anforderung genannt ("ein eigenes App-Passwort"), nicht als Beispielwert. Der bestehende `forward_auth_override`-Block ist unveraendert und traegt weiterhin `<base64 of user:app-password>` |
| T-05-62 | Elevation of Privilege | mitigate | Die Identitaetsfrage steht ausdruecklich im Protokoll (ein `forward_auth_override` pro Quelle, alle Nutzer unter einem Konto, die einzige Stelle ohne die Kernzusage) und verweist auf BL-12; die Empfehlung, sie beim Erstkontakt zu stellen, steht in BL-12 und jetzt auch in der Doku |
| T-05-63 | Repudiation | mitigate | Fuehrung an zwei Stellen (BL-12 mit eigenem Abschnitt, `deferred-items.md` mit eigener Zeile) plus die schriftliche Owner-Entscheidung in diesem SUMMARY mit Option und Datum |
| T-05-SC | Tampering | accept | Keine Installation; `git diff --stat uv.lock` ist leer |

Keine neue Angriffsflaeche: keine Route, kein Netzwerkpfad, keine Schemaaenderung, kein
Quellcode. Die Aenderung ist Text.

## Verification

| Gate | Ergebnis |
|------|----------|
| `uv run --no-sync pytest -q` | gruen (voller Lauf, keine Deselektion) |
| `uv run --no-sync ruff check .` | All checks passed |
| `uv run --no-sync ruff format --check .` | 166 files already formatted |
| `grep -c "BL-13" .planning/BACKLOG.md` | 1 (groesser als 0) |
| `grep -ci "mucgpt" deferred-items.md` | 1 |
| Zaehlung der langen Gedankenstriche (U+2014 und U+2013) ueber die drei Dateien | je 0 |
| `grep -ci 'archiv' docs/client-setup.md` | 0 |
| `git status --porcelain src tests scripts` | leer |
| `git diff --diff-filter=D HEAD~1 HEAD` nach Task 1 | keine Loeschung |

## Self-Check: PASSED

Alle drei geaenderten Dateien liegen auf der Platte, das SUMMARY existiert, und der Commit
`785bfe9` ist in `git log` auffindbar.
