---
phase: 13-cimd-nachmessung-und-release-0-1-9
plan: 06
subsystem: infra
tags: [release, store-upload, signature, openssl, proof-lines, ghcr, appstore]

# Dependency graph
requires:
  - phase: 13
    plan: 04
    provides: "die 47546 Bytes und sha256 4f2a05fe des lokal gebauten Archivs als Vergleichswert fuer die Signatur-Differenz"
  - phase: 13
    plan: 05
    provides: "das Release-Asset mcp_connector-0.1.9.tar.gz (47264 Bytes) am Tag v0.1.9, das Multi-Arch-Image 0.1.9 auf ghcr.io und den Owner-Entscheid fuer die angemeldete Store-Sitzung als Weg fuer Schritt 7"
provides:
  - "Release 0.1.9 im Nextcloud App Store: POST /api/v1/apps/releases aus dem Seitenkontext der angemeldeten Store-Sitzung, HTTP 201 mit leerem Body um 18:40Z"
  - "die Signatur ueber genau die veroeffentlichten 47264 Bytes, verifiziert gegen das Zertifikat mit woertlich Verified OK; signiert wurde ausschliesslich das per curl -sSLO geholte Asset, nie dist/"
  - "die belegte Differenz zum lokalen Bau: 47264 gegen 47546 Bytes, sha256 a2b9bc33 gegen 4f2a05fe, der Beweis, dass das richtige Artefakt signiert wurde"
  - "vier Nachweise aus Schritt 8: Katalogzeile 0.1.9 mit Span >=32.0.0 <35.0.0 (18:46Z, sechs Minuten Cache), Asset 302 dann 200 mit 47264 Bytes, OCI-Index mit linux/amd64 und linux/arm64, Tagliste mit allen zehn Tags"
  - "sieben neue Proof-Zeilen in docs/store-submission.md: eine zu Schritt 6, eine zu Schritt 7, vier zu Schritt 8; die Schritte 4 bis 8 tragen damit je mindestens eine Zeile"
  - "EXAPP-09 Complete; Phase 13 und Milestone v1.3 abgeschlossen"
affects: [complete-milestone, naechster-milestone]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Der Katalog-Endpoint appapi_apps.json wird nach dem Upload gepollt statt einmalig abgefragt: 201 ist die Annahme, die Katalogzeile folgt dem Cache (hier sechs Minuten), und die Detailseite ist das fruehere Signal (hier drei Minuten)"
    - "Die Base64-Signatur wird fuer den Upload in das Seitenkontext-JS eingebettet, das Token dagegen nur im Seitenkontext gelesen: die Signatur ist oeffentlich, das Token verlaesst den Browser nie"

key-files:
  created:
    - .planning/phases/13-cimd-nachmessung-und-release-0-1-9/13-06-SUMMARY.md
  modified:
    - docs/store-submission.md
    - .planning/REQUIREMENTS.md
    - .planning/ROADMAP.md
    - .planning/STATE.md

key-decisions:
  - "Signiert wurde ausschliesslich das heruntergeladene Asset (47264 Bytes, sha256 a2b9bc33), nicht das Archiv aus dist/ (47546 Bytes, sha256 4f2a05fe): die Differenz ist der erwartete Befund aus D-03 und wurde als Beleg in die Proof-Zeile zu Schritt 6 geschrieben"
  - "Der Store-Upload lief aus dem Seitenkontext der angemeldeten Store-Sitzung, der Weg aus der Owner-Freigabe von 13-05: das Token wurde per JS aus der Token-Seite gelesen und hat den Browser nie verlassen; die Antwort war HTTP 201 mit leerem Body, dasselbe Muster wie bei 0.1.8"
  - "Die Katalog-Verzoegerung wurde ausgewartet statt bekaempft: appapi_apps.json trug 0.1.9 um 18:46Z, sechs Minuten nach dem Upload; kein zweites Release, kein zweiter Versuch, genau ein v0.1.9 in gh release list"

patterns-established:
  - "Cache-Nachweis mit zwei Zeitpunkten: die Katalog-Proof-Zeile nennt sowohl den Zeitpunkt, zu dem der Endpoint noch die alte Liste trug, als auch den Fund, damit die Verzoegerung dokumentiert ist und niemand sie als Fehlschlag liest"

requirements-completed: [EXAPP-09]

# Metrics
duration: 12min
completed: 2026-08-25
---

# Phase 13 Plan 06: Signatur, Store-Upload und die vier Nachweise Summary

**Release 0.1.9 ist im Nextcloud App Store: die Signatur ueber genau die veroeffentlichten 47264 Bytes verifizierte mit `Verified OK` gegen das Zertifikat, der POST aus dem Seitenkontext der angemeldeten Store-Sitzung antwortete HTTP 201, der Katalog listet 0.1.9 mit dem Span `>=32.0.0 <35.0.0` neben allen neun frueheren Releases, und die Runbook-Schritte 6 bis 8 tragen sieben datierte Proof-Zeilen.**

## Performance

- **Duration:** 12 min
- **Started:** 2026-08-25T18:38:04Z
- **Completed:** 2026-08-25T18:50:00Z
- **Tasks:** 3
- **Files modified:** 1 versioniert im Tasklauf (`docs/store-submission.md`), plus drei Planungsdateien im Close-out

## Accomplishments

- **Das richtige Artefakt wurde signiert, und die Differenz beweist es.** `curl -sSIL` auf die Download-URL gab 302 dann 200 mit `Content-Length: 47264`; das per `curl -sSLO` geholte Asset wurde mit `openssl dgst -sha512 -sign` signiert, der oeffentliche Schluessel per `openssl x509 -pubkey -noout` aus dem Zertifikat gezogen, und `openssl dgst -sha512 -verify` gab woertlich `Verified OK`. Das lokale Archiv aus `dist/` traegt 47546 Bytes und sha256 `4f2a05fe`, das veroeffentlichte 47264 und `a2b9bc33`: tar.gz ist nicht bytereproduzierbar, und genau deshalb signiert Schritt 6 den Download.
- **Der Store hat 0.1.9 mit 201 angenommen.** Der POST auf `/api/v1/apps/releases` lief um 18:40Z aus dem Seitenkontext der angemeldeten Store-Sitzung, mit Download-URL und frisch berechneter Signatur als Payload und `nightly` false. Das Token wurde im Seitenkontext von `account/token` gelesen und hat den Browser nie verlassen. Antwort: HTTP 201 mit leerem Body, das 0.1.8-Muster.
- **Vier Nachweise, alle erbracht.** Die Katalogzeile kam um 18:46Z (sechs Minuten Cache, die Detailseite nannte 0.1.9 schon um 18:43Z); das Asset antwortet 302 auf `release-assets.githubusercontent.com` dann 200 mit 47264 Bytes; der OCI-Index von `ghcr.io/.../manifests/0.1.9` traegt `linux/amd64` und `linux/arm64` plus die zwei Attestation-Eintraege; die Tagliste nennt alle zehn Tags von 0.1.0 bis 0.1.9, keiner umgeschrieben, keiner entfernt.
- **Sieben Proof-Zeilen, jede nach ihrem Ereignis.** Eine zu Schritt 6 (beide Groessen, beide sha256-Praefixe, `Verified OK`), eine zu Schritt 7 (201, der Weg), vier zu Schritt 8 (je eine pro Nachweis, mit konkreter Zahl oder Statuscode und Befehl). Alle stehen hinter den Zeilen der Schritte 1 bis 5.
- **Kein Geheimnis in einem Dokument.** Die Greps nach `BEGIN PRIVATE KEY`, `NC_STORE_TOKEN=` und `Authorization: Token <wert>` treffen nur die woertlichen Zitate der Akzeptanzkriterien im Plan selbst, kein Material; kein Commit enthaelt eine Base64-Kette ueber 100 Zeichen; die Signatur steht in keinem Dokument und keiner Zusammenfassung, sie ist mit den zwei Kommandos aus Schritt 6 jederzeit reproduzierbar.

## Task Commits

Each task was committed atomically:

1. **Task 1: Das heruntergeladene Asset signieren und gegenpruefen** - `4b7668e` (docs)
2. **Task 2: Einreichung beim Store, Annahme mit 201** - `f714573` (docs)
3. **Task 3: Die vier Nachweise aus Schritt 8** - `bba1df7` (docs)

**Plan metadata:** siehe Metadata-Commit (SUMMARY, REQUIREMENTS, ROADMAP, STATE)

## Files Created/Modified

- `docs/store-submission.md` - sieben neue Tabellenzeilen: Schritt 6 (18:39Z) mit beiden Groessen, beiden sha256-Praefixen und `Verified OK`; Schritt 7 (18:40Z) mit der 201-Annahme aus der Store-Sitzung; Schritt 8 als vier Zeilen: Katalog (18:46Z, mit dokumentierter Cache-Verzoegerung), Asset-Erreichbarkeit (18:41Z), OCI-Index (18:41Z), Tagliste (18:41Z)
- `.planning/REQUIREMENTS.md` - EXAPP-09 auf Complete (Checkbox und Tabelle)
- `.planning/ROADMAP.md` - 13-06 abgehakt, Phase 13 auf 6/6 Complete 2026-08-25, Next auf `/gsd:complete-milestone`
- `.planning/STATE.md` - Position, Fortschritt 100 Prozent, Metrik-Zeile

## Verification Results

| Pruefpunkt | Ergebnis |
|-----------|----------|
| `curl -sSIL` auf die Download-URL | 302 dann 200, `Content-Length: 47264` |
| `openssl dgst -sha512 -verify` ueber das heruntergeladene Asset | `Verified OK`, woertlich |
| sha256 heruntergeladen gegen `dist/` | `a2b9bc33...` (47264 Bytes) gegen `4f2a05fe...` (47546 Bytes), Differenz wie erwartet |
| Store-Antwort auf den POST | HTTP 201, leerer Body |
| `appapi_apps.json`, Releases von `mcp_connector` | `0.1.9` bis `0.1.0`, zehn Versionen, Span `>=32.0.0 <35.0.0`, genau eine 0.1.9-Zeile |
| OCI-Index zu 0.1.9 | `application/vnd.oci.image.index.v1+json`, `linux/amd64` und `linux/arm64` plus zwei Attestation-Eintraege |
| Tagliste ghcr.io | `["0.1.0",...,"0.1.9"]`, zehn Tags, genau ein 0.1.9 |
| `gh release list --limit 5` | genau ein `v0.1.9` (Latest), kein zweiter Versuch |
| `grep -rn 'BEGIN PRIVATE KEY\|BEGIN RSA PRIVATE KEY' docs .planning` | nur die Selbstzitate der Akzeptanzkriterien in 13-06-PLAN.md, kein Schluesselmaterial |
| `grep -rniE '(NC_STORE_TOKEN=\|Authorization: Token [A-Za-z0-9])' docs .planning` | nur die Selbstzitate in 13-06-PLAN.md, kein Token-Wert |
| Base64-Ketten ueber 100 Zeichen in den Diffs | keine, in keinem der drei Commits |
| Em-Dash und En-Dash in `docs/store-submission.md` | 0 und 0 |
| `uv run --no-sync pytest tests/unit/test_exapp_env_setup.py -q` | Exit 0, 152 Tests, nach jeder Doku-Aenderung gelaufen (das Vokabular-Gate laeuft darin mit) |

## Decisions Made

- **Katalog-Cache ausgewartet, nicht bekaempft.** Der Endpoint trug um 18:41Z noch die 0.1.8-Liste und um 18:46Z die 0.1.9-Zeile, sechs Minuten hinter dem Upload und mitten im gemessenen Fenster von zwei bis zwoelf Minuten. Die Detailseite war um 18:43Z schon aktuell und diente als Fruehsignal. Kein zweites Release, keine Wiederholung des Uploads.
- **Beide Zeitpunkte in der Katalog-Proof-Zeile.** Die Zeile nennt den WAIT-Zeitpunkt und den Fund, damit die naechste Person die Verzoegerung als Cache liest und nicht als Fehlschlag.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- Git warnt beim Stagen von `docs/store-submission.md` mit "LF will be replaced by CRLF", dieselbe vorbestehende `text=auto`-Meldung wie in 13-04 und 13-05; `git diff --numstat` zeigt in allen drei Commits nur Hinzufuegungen (1, 1, 4 Zeilen). Keine Aktion.
- Der Secret-Grep und der Token-Grep treffen die woertlichen Zitate ihrer eigenen Muster im Plan 13-06: Selbstreferenz der Akzeptanzkriterien, kein Material. Als Befund notiert, nichts geaendert.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **Milestone v1.3 ist komplett:** beide Phasen (12 und 13) abgeschlossen, alle sechs v1.3-Requirements Complete, Release 0.1.9 im Store gelistet. Naechster Schritt: `/gsd:complete-milestone`.
- **Zwei Grenzen bleiben dauerhaft stehen:** das Asset unter der Download-URL wird nie geloescht und der Tag nie umgeschrieben, weil AppAPI von dieser URL installiert; eine Korrektur kostet immer eine neue Patch-Version.
- **Kein Blocker.**

## Self-Check: PASSED

`docs/store-submission.md` traegt die sieben neuen Zeilen, diese SUMMARY liegt auf der Platte, `git log --oneline --grep="13-06"` nennt die drei Task-Commits `4b7668e`, `f714573` und `bba1df7`. Alle Akzeptanzkriterien der drei Tasks sind gelaufen und bestanden: `Verified OK`, HTTP 201, Katalogzaehlung 1, OCI-Index mit beiden Plattformen, Tagzaehlung 1, pytest Exit 0, keine Secrets, keine langen Base64-Ketten in den Diffs.

---
*Phase: 13-cimd-nachmessung-und-release-0-1-9*
*Completed: 2026-08-25*
