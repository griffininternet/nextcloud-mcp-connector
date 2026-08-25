<!--
  - SPDX-FileCopyrightText: 2026 street1983nk
  - SPDX-License-Identifier: AGPL-3.0-or-later
-->
---
phase: 11-b-ndelung-budget-und-release-0-1-6
plan: 10
subsystem: release
tags: [release, tag, workflow, signature, store-submission, proofs, exapp-07]

# Dependency graph
requires:
  - phase: 11-b-ndelung-budget-und-release-0-1-6
    plan: 09
    provides: "die freigegebene Fassung: vier identische Versionsstrings, der Changelog-Block 0.1.8, die Store-Texte in drei Sprachen und sechs lokal grüne Gates"
provides:
  - "der Tag v0.1.8 auf bbe9753, lokal und auf origin, nach ausdrücklicher Owner-Freigabe"
  - "das veröffentlichte GitHub-Release 0.1.8 mit dem Asset mcp_connector-0.1.8.tar.gz, 45546 Bytes"
  - "das Multi-Arch-Image ghcr.io/street1983nk/mcp_connector:0.1.8 mit linux/amd64 und linux/arm64"
  - "die im Nextcloud App Store angenommene Release 0.1.8 (HTTP 201)"
  - "sechs neue Proof-Zeilen in docs/store-submission.md, zusammen zehn Zeilen zu 0.1.8"
affects:
  - "der Meilenstein v1.2 ist bereit für seinen Abschluss"
  - "jede spätere Installation über AppAPI zieht das Asset dieser URL und das Image dieses Tags"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Signiert wird ausschließlich das vom GitHub-Release heruntergeladene Asset; der Größenunterschied zum lokal gebauten Archiv wird bei jedem Release neu gemessen und als Zeile festgehalten"
    - "Die Signatur wird nirgends aufgeschrieben: sie ist eine reine Funktion aus Asset und Schlüssel und mit zwei Befehlen neu berechenbar"
    - "Der Branch wird vor dem Tag gepusht, damit die auf main verlinkten Doku- und Screenshot-URLs des Manifests den Stand zeigen, zu dem das Release gehört"
    - "Eine Proof-Zeile, die etwas nicht geprüft hat, sagt das ausdrücklich, statt die Lücke zu verschweigen"

key-files:
  created:
    - .planning/phases/11-b-ndelung-budget-und-release-0-1-6/11-10-SUMMARY.md
  modified:
    - docs/store-submission.md

key-decisions:
  - "Die Freigabe umfasste auf Vorlage hin auch git push origin main: 42 Commits der Phase 11 lagen nur lokal, und die Store-Beschreibung verlinkt Doku- und Screenshot-URLs auf main"
  - "Die verzögerte Sichtbarkeit im Katalog-Endpunkt wurde als Cache-Verhalten notiert und abgewartet, nicht mit einer weiteren Version beantwortet"
  - "Die Sichtbarkeitszeile sagt ausdrücklich, dass sie über den Beschreibungstext nichts aussagt: er liegt nicht im initialen HTML der Store-Seite"

patterns-established:
  - "Der irreversible Schritt bekommt eine Vorlage mit allen vier Versionsstellen, dem Changelog-Block, den Store-Texten, der Unwiderruflichkeit und der Cache-Notiz, und die Antwort des Owners wird wörtlich festgehalten"

requirements-completed: [EXAPP-07]

# Metrics
duration: 20min
completed: 2026-08-25
---

# Phase 11 Plan 10: Tag, Release und die Einreichung von 0.1.8 Summary

**Release 0.1.8 ist im Nextcloud App Store: Tag nach ausdrücklicher Freigabe, grüner
Workflow-Lauf 32803041518, Signatur über das veröffentlichte Asset mit `Verified OK`, HTTP 201
vom Store, und alle vier Nachweise aus Runbook-Schritt 8 stehen mit Datum in der Tabelle.**

## Was passiert ist

Der Plan hatte zwei menschliche Tore und dazwischen den irreversiblen Teil. Beide Tore wurden
vorgelegt, beide wurden beantwortet, und die Antworten stehen unten wörtlich.

Zwischen den Toren lief Runbook-Schritt 4 bis 6 in der vorgeschriebenen Reihenfolge. Der Tag
`v0.1.8` zeigt auf `bbe97539bf93c75c26be5f92a61f3e584c6aaa35`, den Zustand, den Plan 11-09
hinterlassen hat. Der Release-Workflow baute das Multi-Arch-Image, pushte es nach
`ghcr.io/street1983nk/mcp_connector:0.1.8`, baute das Store-Archiv und hängte es an das
GitHub-Release. Danach wurde genau dieses veröffentlichte Asset heruntergeladen und signiert.

## Die Antworten des Owners, wörtlich

**Task 1, Freigabe für den Tag:** "freigegeben", ausdrücklich inklusive `git push origin main`
unmittelbar vor `git tag v0.1.8` und `git push origin v0.1.8`.

Der Vorlage lagen bei: die vier Versionsstellen nebeneinander (`pyproject.toml:3`,
`src/mcp_connector/__init__.py:7`, `appinfo/info.xml:171` und `:245`, alle 0.1.8), der
Changelog-Block 0.1.8 mit Added, Changed und Security, die drei Beschreibungsblöcke aus
`appinfo/info.xml` in EN, DE und FR, der Beleg `git tag --list v0.1.8` leer, die
Unwiderruflichkeit und die Cache-Notiz.

**Task 3, Store-Sitzung:** "eingereicht". Der POST auf
`https://apps.nextcloud.com/api/v1/apps/releases` wurde am 2026-08-25 gegen 02:58Z aus dem
Seitenkontext der angemeldeten Store-Sitzung ausgeführt, der Token wurde aus `/account/token` in
der Seite gelesen und hat den Browser nicht verlassen. Ergebnis: **HTTP 201** mit leerem Body,
Payload `download` plus `signature`, `nightly` false.

## Die Zahlen

| Sache | Wert |
|-------|------|
| Tag | `v0.1.8` auf `bbe9753`, lokal und auf `origin` |
| Workflow-Lauf | `32803041518`, grün in jedem Schritt, Job `publish` in 1m29s, `gh run watch --exit-status` Exit 0 |
| Asset | `mcp_connector-0.1.8.tar.gz`, 45546 Bytes, HTTP 302 dann 200 |
| Signaturverifikation | `Verified OK` gegen den Public Key aus `mcp_connector.crt` |
| Store-Upload | HTTP 201, leerer Body |
| Katalog-Endpunkt | Release-Zeile 0.1.8 mit `>=32.0.0 <35.0.0`, dem Span des Manifests (min-version 32, max-version 34) |
| GHCR-Manifest | `application/vnd.oci.image.index.v1+json` mit `linux/amd64`, `linux/arm64` und zwei attestation-Einträgen |
| GHCR-Tags | `0.1.0` bis `0.1.8`, neun Stück, keiner entfernt oder umgeschrieben |
| Spendenlink | Store-Seite antwortet 200, nennt 0.1.8 und trägt `paypalme/KhaledCherifDev` |
| Tests | `uv run --no-sync pytest -q`: 2766 passed, 163 deselected in 64.93s |

Die Signatur selbst ist hier ausdrücklich nicht notiert. Sie ist eine reine Funktion aus dem
veröffentlichten Asset und dem Schlüssel und mit den zwei Befehlen aus Runbook-Schritt 6
jederzeit neu berechenbar. Sie steht in keiner Datei dieses Repositories, per Grep über `docs/`
und `src/` geprüft. Der Store-Token hat den Browser nie verlassen und steht ebenfalls nirgends.

## Der Beleg, dass das richtige Artefakt signiert wurde

Das veröffentlichte Asset hat 45546 Bytes und den sha256 `2769c587…`, das lokal in `dist/`
gebaute Archiv aus Plan 11-09 hat 45710 Bytes und `15fc8719…`. Damit wiederholt sich die Messung
vom 2026-08-20 (31909 gegen 32168) für dieses Release: `tar.gz` ist nicht byte-reproduzierbar,
und der Store prüft die Signatur gegen die Bytes, die er von der URL lädt. Das Archiv aus
`dist/` wurde nicht signiert und nicht hochgeladen.

## Die Cache-Beobachtung, als Beobachtung

Der Katalog-Endpunkt `appapi_apps.json` antwortete um 02:58Z noch mit der 0.1.7-Liste und trug
0.1.8 rund zwei Minuten später. Das ist der Cache, den das Runbook beschreibt, kein
fehlgeschlagener Upload, und es war kein Anlass für eine weitere Version. Zum Vergleich: bei
0.1.3 lagen zwölf Minuten dazwischen.

Die Detailseite nannte 0.1.8 direkt beim ersten Abruf und trug den korrigierten
PayPal-Spendenbutton `paypalme/KhaledCherifDev`, der der Anlass dieses Releases ist. Was dieser
Abruf nicht belegt, sagt die Proof-Zeile ausdrücklich: der Beschreibungstext liegt nicht im
initialen HTML dieser Seite, weder mit dem Standard-User-Agent noch mit einem Browser-Agent. Das
ist eine Eigenschaft der Anfrage und keine Aussage über die Beschreibung; die Beschreibung selbst
ist beim Upload in den Store gelangt, was die Annahme mit HTTP 201 bestätigt.

## Im Runbook entdeckte Ungenauigkeiten

**1. `scripts/build_store_release.sh` druckt eine irreführende Signatur.** Das Skript gibt am Ende
eine base64-Signatur über das lokal gebaute Archiv aus, mit dem Hinweis, sie in das
Store-Formular einzusetzen. Genau das ist falsch: verbindlich ist Runbook-Schritt 6, der über das
heruntergeladene Release-Asset signiert. Der Befund stammt aus Plan 11-09, wurde hier beim Lesen
bestätigt, und die Ausgabe des Skripts wurde nicht benutzt. Die Nachweiszeile dieses Releases
nennt den Größenunterschied, der zeigt warum. Die Korrektur des Skripts ist nicht Teil dieses
Plans und bleibt offen.

**2. Runbook-Schritt 4 setzt einen gepushten Branch stillschweigend voraus.** Der Schritt nennt
nur `git tag` und `git push origin v<version>`. Bei diesem Release lagen 42 Commits der Phase 11
nur lokal. Ein Tag-Push hätte technisch funktioniert, aber der öffentliche `main` hätte den Stand
vor der Phase gezeigt, und die Store-Beschreibung verlinkt Dokumentation und Screenshots über
`blob/main/` und `raw.githubusercontent.com/.../main/`. Der Branch-Push wurde deshalb als Teil
der Freigabe vorgelegt und ausgeführt. Das Runbook nennt ihn bisher nicht.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Branch-Push vor dem Tag**

- **Found during:** Task 1, bei der Vorbereitung der Vorlage
- **Issue:** `main` lag 42 Commits vor `origin/main`. Der Tag hätte auf einen Commit gezeigt, den
  kein öffentlicher Branch enthält, und die auf `main` verlinkten Doku- und Screenshot-URLs des
  Manifests hätten den Stand vor Phase 11 ausgeliefert.
- **Fix:** Nicht eigenmächtig behoben. Der Befund wurde dem Owner im Checkpoint vorgelegt, und
  `git push origin main` wurde Teil der Freigabe. Ausgeführt als `d36356d..bbe9753`, unmittelbar
  vor dem Tag.
- **Files modified:** keine
- **Commit:** kein eigener Commit (reiner Push)

Sonst keine Abweichungen. Der Plan lief in der Reihenfolge, die er vorgibt.

## Auth Gates

Zwei, beide geplant und beide als Checkpoint des Plans vorgesehen:

- Task 1, die Owner-Freigabe für den irreversiblen Tag. Ohne sie wäre der Plan ohne
  Veröffentlichung geendet.
- Task 3, die angemeldete Store-Sitzung. Der Token gehört dem Store-Konto, ist kein
  Repository-Secret und liegt nicht in dieser Arbeitskopie.

## Was nicht passiert ist

Kein Release-Asset wurde gelöscht, kein Tag wurde umgeschrieben oder entfernt: die GHCR-Tag-Liste
zeigt alle neun Tags, `git ls-remote --tags origin` ebenso. Es gab keine zweite Version als
Reaktion auf eine verzögerte Sichtbarkeit. Es wurde kein Paket installiert, `pyproject.toml` und
`uv.lock` blieben unangetastet.

## Requirements

EXAPP-07 ist damit erfüllt: das Release ist im Store, mit dem Spendenlink
`paypal.me/KhaledCherifDev` auf der Detailseite.

## Self-Check: PASSED

Geprüft am 2026-08-25: `docs/store-submission.md` und diese Datei existieren, die Commits
`dd9d137` und `08e960e` liegen in `git log`, und die Datei enthält keine Em-Dashes und keine
En-Dashes.
