---
plan: 15-04
phase: 15-release-0-1-10
completed: 2026-08-28
requirements-completed: [EXAPP-10]
one_liner: "Release 0.1.10 ist im Nextcloud App Store: signiert wurde das heruntergeladene Asset (46973 Bytes, Verified OK), der Store antwortete mit HTTP 201, und der Katalog trägt neben allen zehn früheren Releases jetzt die gekürzte Enterprise-Beschreibung mit admin@infranode.dev statt der alten Adresse."
key-files:
  modified:
    - docs/store-submission.md
    - .planning/REQUIREMENTS.md
---

# Plan 15-04: Signatur, Store-Upload und die vier Nachweise

## Was entstanden ist

Der letzte Plan der Phase führte die Runbook-Schritte 6 bis 8 aus. Signiert wurde
ausschließlich das von GitHub heruntergeladene Asset (46973 Bytes, sha256 `4236d2e8…`),
nicht der lokale Bau aus Schritt 3 (47299 Bytes, sha256 `4682e06d…`). Die Differenz von
326 Bytes ist der erwartete Befund: `tar.gz` ist nicht bytereproduzierbar, dieselbe
Messung steht in den Zeilen zu 0.1.2, 0.1.8 und 0.1.9. Die Verifikation gegen das
zusammengeführte Zertifikat antwortete wörtlich `Verified OK`.

Der Upload lief aus dem Seitenkontext der angemeldeten Store-Sitzung (Owner-Entscheid
zum Weg für Schritt 7) und antwortete mit HTTP 201 bei leerem Body. Kein Token verließ
den Browser, keine Anmeldedaten stehen in einem Dokument dieser Phase.

## Die Nachweise aus Schritt 8

| Nachweis | Ergebnis |
|----------|----------|
| Katalog `appapi_apps.json` | 11 Releases für `mcp_connector`, `0.1.10` darunter; der Store führt 27 ExApps |
| Asset-Download | 302 dann 200, `Content-Length: 46973`, exakt die signierten Bytes |
| Image-Index `ghcr.io/street1983nk/mcp_connector:0.1.10` | `linux/amd64` und `linux/arm64` |
| Tagliste | elf `v0.1.*`-Tags, `v0.1.10` darunter, keiner umgeschrieben |
| Zweck des Releases | Die Store-Beschreibung trägt in EN und DE den gekürzten Enterprise-Abschnitt mit `admin@infranode.dev` genau einmal; `k.cherif@outlook.de` kommt darin null mal vor |

## Zwei Funde, die aufgeschrieben gehören

**Die Sortier-Falle.** `0.1.10` sortiert in einer Zeichenketten-Sortierung VOR `0.1.9`.
Eine absteigend sortierte Ausgabe der Release-Liste zeigt deshalb `0.1.9` an erster Stelle
und liest sich wie ein fehlgeschlagener Upload. Die richtige Prüfung fragt, ob die
Zeichenkette `0.1.10` in der Liste enthalten ist, statt der Reihenfolge zu trauen. Diese
Falle trifft jede Version ab der zehnten Patch-Nummer und damit alle künftigen Releases.

**Die Detailseite ist kein Beleg mehr.** `https://apps.nextcloud.com/apps/mcp_connector`
rendert die Beschreibung clientseitig; ein `curl` bekommt 24 KB Rahmen ohne einen Satz der
Beschreibung. Die Seite antwortet 200 und nennt `0.1.10`, taugt aber nicht mehr als Beleg
für den Beschreibungstext. Lesbar ist der Text im `translations`-Feld des Katalogeintrags,
und genau dort wurde er geprüft.

## Was diese Phase nicht angefasst hat

Kein Tag wurde umgeschrieben, kein Asset gelöscht, keine `info.xml` nach dem Tag geändert.
Die Kürzung des Trifecta-Absatzes in der Store-Beschreibung (Commit `b3267cd`, außerhalb
dieses Plans nach Owner-Wunsch entstanden) liegt bewusst NACH dem Tag `v0.1.10` und ist
deshalb nicht Teil dieses Releases; sie fährt mit dem nächsten mit und braucht dort einen
eigenen Changelog-Eintrag.

## Abweichung vom Plan

Plan 15-04 Task 3 sah vier getrennte Proof-Zeilen fuer die vier Nachweise des
Runbook-Schritts 8 vor. Geschrieben wurde eine zusammengefasste Zeile, die alle
vier Nachweise plus den Beschreibungs-Beleg traegt. Grund: die vier Messungen
entstanden in derselben Minute und aus demselben Katalog-Abruf, und eine
gemeinsame Zeile haelt die Sortier-Falle an genau der Stelle fest, an der sie
jemanden treffen wuerde. Inhaltlich fehlt kein Nachweis; die Zeile nennt jeden
einzeln mit eigenem Befehl und eigenem Ergebnis. Nachgetragen am 2026-08-28
nach dem Verifikationsbefund.

## Self-Check: PASSED

- Signatur über das heruntergeladene Asset, nicht über `dist/`: belegt durch die zwei
  verschiedenen sha256-Summen in der Proof-Zeile zu Schritt 6
- Store-Annahme mit 201: Proof-Zeile zu Schritt 7
- Vier Nachweise plus Beschreibungs-Beleg: Proof-Zeile zu Schritt 8
- `EXAPP-10` steht auf Complete, weil das Release im Store gelistet ist und alle sieben
  Teilforderungen der Anforderung belegt sind
