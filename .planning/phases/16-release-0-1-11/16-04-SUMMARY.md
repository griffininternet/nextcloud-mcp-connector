---
phase: 16-release-0-1-11
plan: 04
status: complete
completed: 2026-08-28
requirements: [EXAPP-11]
---

# Plan 16-04: Signieren, einreichen, nachweisen

Der letzte Plan der Phase. Runbook-Schritte 6 bis 8 sind erledigt, das Release 0.1.11
ist im Nextcloud App Store, und EXAPP-11 ist damit geschlossen.

## Was geliefert wurde

**Schritt 6, die Signatur.** Signiert wurde ausschließlich das veröffentlichte Asset,
geholt mit `curl -sSLO` von der Release-URL: 47046 Bytes, sha256
`e4b570c0cb9fa9ba44ce9a6bf40fb2518e99945d8c1676a7489293e86f2584b7`. Das lokal gebaute
Archiv aus Plan 16-02 misst 47349 Bytes bei sha256
`df5a9ca97d08f9e21f0315b6b40802af9e837f1edee587107425e8cb29012364`. Die Signatur selbst
steht in keiner Datei und in keinem Commit; sie ist eine reine Funktion aus Asset und
Schlüssel und wurde dort berechnet, wo sie gebraucht wurde.

Die Gegenprobe ist der eigentliche Beleg: dieselbe Signatur verifiziert über das
heruntergeladene Asset mit wörtlich `Verified OK` und scheitert über das lokale Archiv
mit einem Signaturfehler. Damit ist nicht behauptet, sondern gezeigt, welches Artefakt
signiert wurde.

**Schritt 7, die Einreichung.** `POST /api/v1/apps/releases` aus dem Seitenkontext der
angemeldeten Store-Sitzung, dem Weg aus der Owner-Freigabe, antwortete mit **HTTP 201**
und leerem Körper, `nightly` false. Der API-Token wurde im Seitenkontext aus dem DOM der
Kontoseite gelesen und von dort direkt gesendet, er steht in keinem Dokument und in
keinem Commit. Genau eine Einreichung, genau ein Release.

**Schritt 8, die fünf Nachweise.** Release-Liste zwölf Einträge mit 0.1.11, Asset
erreichbar mit 302 dann 200 bei 47046 Bytes, OCI-Index mit `linux/amd64` und
`linux/arm64`, Registry-Tagliste zwölf Tags mit 0.1.11, und `authors[0].mail` im Katalog
gleich `admin@infranode.dev`, deckungsgleich mit `<author mail>` im Manifest am Tag.

## Zwei Befunde

**Ein Akzeptanzkriterium des Plans war falsch formuliert.** Es erwartete den englischen
Satz "An assistant also reads text that strangers wrote" dreimal im Asset, einmal je
Sprache. Die drei Beschreibungen sind aber Übersetzungen voneinander und keine Kopien,
also kann der englische Satz nur einmal vorkommen. Der tatsächliche Zustand wurde je
Sprache einzeln nachgemessen und ist richtig: der gekürzte Absatz steht in allen drei
Fassungen, mit 258 Zeichen in Englisch, 274 in Deutsch und 293 in Französisch, je drei
Sätze statt vier, und kein Satz der langen Fassung steht noch irgendwo. Die deutsche
Fassung trägt echte Umlaute und keinen Gedankenstrich. Das 0.1.10-Asset trug an
denselben Stellen den langen Absatz mit 569 Zeichen und die private Adresse; das ist der
Zustand, den dieses Release ablöst. Für das nächste Release gehört das Kriterium je
Sprache formuliert, nicht als Zählung eines englischen Satzes.

**Die alte Adresse steht noch zweimal im Katalogeintrag**, beide Male innerhalb der
Changelog-Texte der Releases 0.1.10 und 0.1.11, an genau dem Satz, der den Wechsel weg
von ihr festhält. Das ist kein Rest, sondern die Stelle, an der die Adresse stehen muss,
damit der Eintrag verständlich bleibt. In `authors` und in den Beschreibungen kommt sie
nicht mehr vor, im getaggten Manifest null mal.

## Der Cache-Versatz

Der Katalog-Endpunkt trug die neue Version rund vierzehn Minuten nach der Annahme,
etwas jenseits des bisher gemessenen Fensters von zwei bis zwölf Minuten. Die erste
Abfrage eine Minute nach dem 201 nannte weiter elf Releases und die alte Adresse. Es
wurde gewartet und erneut gefragt, kein zweites Release gebaut.

## Bedeutung für Phase 19

Der `[Unreleased]`-Block ist geleert und abgeholt. Die Textänderungen aus AUDIT-06 können
ihn neu füllen, ohne dass ein ausgeliefertes Paket Text über ein Modul mitführt, das es
zum Zeitpunkt des Uploads nicht gab. Die Auslieferung dieser Texte ist EXAPP-12 und
bewusst nicht Teil dieses Milestones.

## Verifikation

| Kriterium | Ergebnis |
|-----------|----------|
| Signatur über das heruntergeladene Asset | `Verified OK`, Gegenprobe über `dist/` scheitert |
| Store-Annahme | HTTP 201, leerer Körper |
| Release-Liste | zwölf Einträge, `grep -cx '0.1.11'` gibt 1 |
| Asset erreichbar | 302 dann 200, 47046 Bytes |
| OCI-Index | `linux/amd64` und `linux/arm64` |
| Registry-Tagliste | zwölf Tags, `grep -cx '0.1.11'` gibt 1 |
| Autorenkontakt | `admin@infranode.dev` im Katalog wie im Manifest |
| Proof-Zeilen | drei neue Zeilen, `git diff --numstat` gibt 3 und 0 |
| Kein Geheimnis in einem Dokument | kein Token, kein Schlüssel, keine Signatur |
