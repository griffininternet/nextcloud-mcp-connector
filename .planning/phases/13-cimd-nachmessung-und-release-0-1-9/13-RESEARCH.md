# Phase 13: CIMD-Nachmessung und Release 0.1.9 - Research

**Researched:** 2026-08-25
**Domain:** Release-Engineering (Nextcloud App Store, Signatur, Tag-Disziplin) + Live-Nachmessung eines OAuth-2.1-Pfades (Client ID Metadata Documents) gegen eine laufende HaRP-Topologie
**Confidence:** HIGH (alles Wesentliche in dieser Sitzung am Repo, an der laufenden Topologie und am Store gemessen)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Release-Disziplin (aus ROADMAP/Phase-12-Übergaben, LOCKED)**
- D-01: Tag v0.1.9 entsteht NUR nach ausdrücklicher Owner-Freigabe; Branch/main
  ist gepusht, BEVOR irgendein Tag existiert (Runbook Schritt 4).
- D-02: Changelog 0.1.9 nennt `message_truncated` ausdrücklich als
  Formatänderung und das README-Provider-Beispiel als Doku-Korrektur
  (Übergaben aus Phase 12).
- D-03: Signiert wird das HERUNTERGELADENE Release-Asset, nie das lokal gebaute
  (Runbook Schritt 6); jeder Runbook-Schritt 4-8 bekommt eine Proof-Zeile mit
  Datum, Befehl und Ergebnis in docs/store-submission.md.
- D-04: Gates bleiben auf der v1.2-Messung (BUDGET_BYTES 18000,
  MAX_TOOL_BYTES 1400, 21 Tools); Vokabular-Gate in der neuen
  Phase-12-Reichweite läuft lokal VOR dem Push.

**ISV-Vorhaben: Enterprise-Fake-Door fährt mit Release 0.1.9 mit (Owner 25.08., LOCKED)**
- D-05: Ein Abschnitt "Enterprise" kommt in die Connector-READMEs (EN/DE/FR
  synchron, echte Umlaute/Accents, keine Em-Dashes): Audit-Log,
  Gruppen-Policies und SSO sind als kommerzielles Add-on GEPLANT (nichts davon
  existiert; ehrlich als Plan formulieren), Interessens-Kontakt
  k.cherif@outlook.de. KEIN Preis nennen. Quelle: validation-plan.md,
  Methode Fake-Door, Konzept-Brief concept-brief-1-connector-enterprise.md.
- D-06: Derselbe Enterprise-Hinweis kommt in die Store-Beschreibung
  (info.xml-Description EN/DE/FR; Regeln: kein Backtick, keine Tabelle).
  Er wird erst mit dem Release-Upload 0.1.9 sichtbar (Store liest das
  Manifest nur beim Release-Upload), deshalb gehört er in DIESE Phase.
- D-07: Das GitHub-Issue "Enterprise features: what would your org need
  before allowing MCP access?" (Fake-Door Schritt 2) wird als ENTWURF
  vorbereitet (Titel + Body als Datei im Repo-Doku-Bereich oder Messdokument),
  aber NICHT automatisch veröffentlicht; Veröffentlichung nur nach
  Owner-Freigabe (analog Tag-Regel; Owner sendet Outreach selbst).
- D-08: Kein Enterprise-Feature wird in dieser Phase GEBAUT (kein Audit-Log,
  keine Policies, kein SSO). Baustart frühestens nach ISV-Klarheit und
  Findling v1.1 (Anfang 2027). Diese Phase liefert nur die Fake-Door-Texte.

### Claude's Discretion
- Genaue Formulierung des Enterprise-Abschnitts (Ton wie bestehende READMEs,
  AIquila-artig kurz in der Store-Beschreibung).
- Platzierung des Enterprise-Abschnitts in den READMEs (sinnvoll nahe
  Grenzen/Support-Themen).
- Aufbau des CIMD-Messdokuments und Wahl des Messwegs, solange die
  Success-Criteria-Formulierung erfüllt ist (Proof-Zeile im Doku-/Messdokument,
  nicht in einer Zusammenfassung).

### Deferred Ideas (OUT OF SCOPE)
- Enterprise-Feature-BAU (Audit-Log, Policies, SSO): nach ISV-Klarheit +
  Findling v1.1, frühestens Anfang 2027.
- Fake-Doors 2 (Findling Pro) und 3 (Approved-Write-Suite): andere Repos/
  Projekte, nicht Teil dieser Phase.
- ISV-Call-Vorbereitung 14.09. (Dossier liegt auf dem Desktop): Owner-seitig,
  kein Phase-13-Artefakt.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description (REQUIREMENTS.md) | Research Support |
|----|-------------------------------|------------------|
| EXAPP-08 | Der CIMD-Weg ist nach den v1.1-Review-Fixes live nachgemessen: E2E-Lauf gegen die laufende Topologie zeigt, dass ein CIMD-Client sich weiterhin ohne Registrierung verbindet, mit Proof-Zeile (Datum, Befehl, Ergebnis) in der Doku oder im Messdokument der Phase | Abschnitt "CIMD-Nachmessung": laufende Topologie inventarisiert (Container, Versionen, Digest), drei Messwege mit Empfehlung, Wortlaut des v1.1-Debt-Befunds W-5, die exakten Belegstellen des Vorlaufs (06-09-MEASUREMENTS aus der Git-Historie rekonstruiert), Beleg-Mechanik (der geglückte Fetch schreibt KEINE Logzeile), Pitfalls 1 bis 5 |
| EXAPP-09 | Release 0.1.9 ist im Store: Version an allen fünf Stellen, Changelog-Block mit `message_truncated` als Formatänderung, alle Gates grün (inkl. Vokabular-Gate in neuer Reichweite), Branch-Push vor dem Tag, Signatur über das heruntergeladene Asset, Tag `v0.1.9` erst nach Owner-Freigabe, Runbook-Schritte 4 bis 8 mit Proof-Zeilen | Abschnitte "Die fünf Versionsstellen" (mit Datei:Zeile), "Gates", "Changelog-Inhalt 0.1.9" (exakte Übergaben aus Phase 12), "Store-Beschreibung und Enterprise-Text" (Gate-Regeln), "Release-Pipeline" (release.yml, Signatur-Falle, 500er-Falle, Store-Caches), Pitfalls 6 bis 14 |
</phase_requirements>

## Summary

Diese Phase hat zwei sehr verschiedene Hälften, und ihre Reihenfolge ist die wichtigste
Planungsentscheidung. Die Release-Hälfte ist ein durchgemessenes Runbook: acht Schritte in
`docs/store-submission.md`, neun Vorgänger-Releases als Belegtabelle, zwei menschliche Tore
(Owner-Freigabe vor dem Tag, angemeldete Store-Sitzung beim Upload) und ein Workflow, der
einen Tag ablehnt, dessen Name nicht der `<version>` des Manifests entspricht. Es gibt hier
nichts zu erfinden, nur nachzugehen, und die Fehler, die es zu vermeiden gibt, sind alle
schon einmal passiert und alle aufgeschrieben. Die CIMD-Hälfte ist eine echte Messung: der
letzte Live-Beleg der CIMD-Kette stammt vom 2026-08-20 gegen 0.1.2 und ist älter als die
Review-Fixes `a47bb57` und `bd75cd8` (das ist wörtlich der v1.1-Tech-Debt-Befund W-5), und
die laufende Topologie steht heute auf einem gemischten Stand (AppAPI meldet 0.1.7, der
Container läuft auf dem Image 0.1.6).

Die kritische Kopplung: Der Tag v0.1.9 hängt an einer Owner-Freigabe, die innerhalb des
Ausführungsfensters der Phase nicht kommen muss. Ein CIMD-Beweis, der auf dem
veröffentlichten 0.1.9-Image aufsetzt, wäre damit von dieser Freigabe abhängig und könnte
Erfolgskriterium 1 blockieren, obwohl es technisch längst erfüllbar ist. Deshalb: Die
Nachmessung läuft gegen den 0.1.9-Kandidaten aus dem lokalen Registry
(`127.0.0.1:5000/mcp_connector:0.1.9`), also gegen genau den Quellstand, der getaggt wird,
und sie läuft VOR dem Tag. Der Beweis ist damit unabhängig vom Freigabezeitpunkt, und er
belegt exakt die Fassung, die in den Store geht.

Die dritte Hälfte, die es formal nicht gibt: der Enterprise-Fake-Door aus dem ISV-Vorhaben.
Er ist reine Textarbeit an vier Dateien (drei READMEs plus `appinfo/info.xml`), er hat keine
Codewirkung, und er ist genau deshalb an dieses Release gebunden: der Store liest das
Manifest ausschließlich beim Release-Upload, eine Beschreibungsänderung ohne Release ist
unsichtbar (im Runbook mit zwei verbrannten Versionen, 0.1.5 und 0.1.6, belegt). Der Store
duldet solche Texte: die Katalogabfrage dieser Sitzung findet kommerzielle Hinweise in
mehreren gelisteten Apps.

**Primary recommendation:** Vier Pläne in dieser Reihenfolge: (1) CIMD-Nachmessung gegen den
0.1.9-Kandidaten im lokalen Registry, Proof-Zeile in `docs/oauth-setup.md` plus Protokoll als
Phase-Messdokument; (2) Versions-Bump an allen fünf Stellen, Changelog-Block 0.1.9,
Enterprise-Text in drei READMEs und drei Manifest-Beschreibungen, Issue-Entwurf als Datei,
alle sechs Gates lokal grün, Proof-Zeilen der Schritte 1 bis 3; (3) `autonomous: false`,
Owner-Freigabe, `git push origin main`, Tag, Workflow, Signatur über das heruntergeladene
Asset, Store-POST, vier Nachweise, Proof-Zeilen der Schritte 4 bis 8; (4) optional, sehr
klein: die tote Verweiszeile in `docs/oauth-setup.md` auf das archivierte Phase-6-Protokoll
schließen.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| CIMD-Client-Identifikation (client_id = https-URL) | API / Backend (`src/mcp_connector/oauth/`) | Externer Client (Claude Code) | Der Server liest das Dokument des Clients und leitet daraus die Client-Information ab; der Client registriert nichts. Gemessen wird die Serverseite über die volle Kette |
| Messung der Kette | Lokale Topologie (Docker/WSL2: Caddy, HaRP, Nextcloud 34.0.3, ExApp-Container) | Lokales Registry `127.0.0.1:5000` | Der Beweis muss durch Reverse Proxy und HaRP laufen, sonst belegt er nur In-Process-Verhalten (Muster aus `scripts/oauth_flow_check.py`) |
| Versions-Wahrheit | Repo-Artefakte (`pyproject.toml`, `__init__.py`, `appinfo/info.xml`) | READMEs (Statuszeile, ungegatet) | Zwei Gates halten vier Stellen; die fünfte reist ungegatet mit und wurde bei 0.1.8 genau deshalb verpasst |
| Store-Metadaten (Beschreibung, Enterprise-Text) | `appinfo/info.xml` im signierten Archiv | Store-Katalog (Cache, Minuten) | Der Store liest das Manifest nur beim Release-Upload, nie später |
| Auslieferung des Codes | GitHub Release Asset (`tar.gz`) + ghcr.io-Image | Store (hält nur URL und Metadaten) | AppAPI installiert von unserer URL, nicht aus dem Store: Asset niemals löschen, Tag niemals umschreiben |
| Freigabe-Entscheidung | Owner (Mensch) | - | Tag und Store-Upload sind die zwei nicht automatisierbaren Tore |

## Standard Stack

### Core

Diese Phase führt **kein neues Paket** ein. Sie arbeitet ausschließlich mit dem, was
installiert und in dieser Sitzung geprüft ist.

| Werkzeug | Version (gemessen) | Zweck | Warum Standard |
|----------|--------------------|-------|----------------|
| `uv` | 0.11.7 [VERIFIED: `uv --version`] | Gate-Läufe (`uv run --no-sync ...`) | Projekt-Constraint, System-Python defekt |
| `gh` | 2.92.0, angemeldet als `street1983nk` [VERIFIED: `gh auth status`] | Workflow beobachten, ggf. Issue anlegen (nur nach Freigabe) | Runbook Schritt 5 nennt es wörtlich |
| `openssl` | 3.5.6 [VERIFIED: `openssl version`] | Signatur über das heruntergeladene Asset | Runbook Schritt 6 |
| `curl` | 8.19.0 [VERIFIED: `curl --version`] | Vier Nachweise aus Schritt 8, Store-Katalog, ghcr-Manifeste | Runbook Schritt 8 |
| `docker` | Server 29.5.2 [VERIFIED: `docker version`] | Topologie, Image-Bau, `occ`-Aufrufe | Messumgebung |
| `claude` (Claude Code) | 2.1.233 [VERIFIED: `claude --version`] | echter CIMD-Client, exakt dieselbe Version wie im Vorlauf 06-09 | Kein Client-Drift gegenüber dem letzten Beweis |
| `jq`, `python` | jq-1.8.1, CPython 3.13.1 [VERIFIED] | JSON-Auswertung der Nachweise | vorhanden |

### Supporting

| Artefakt | Zweck | Wann |
|----------|-------|------|
| `scripts/build_store_release.sh` | Store-Archiv bauen (Strukturprüfung); die ausgegebene Signatur ist **diagnosis only** | Runbook Schritt 3 (optional) |
| `scripts/bootstrap_exapp.sh` | Topologie mit dem 0.1.9-Kandidaten bestücken (baut, pusht nach `127.0.0.1:5000`, registriert) | CIMD-Nachmessung, mit dem Vorbehalt aus Pitfall 3 |
| `scripts/oauth_flow_check.py` | Vollständiger OAuth-Rundlauf, aber über **dynamische Registrierung**; `sign_in` ist der wiederverwendbare Browser-Schenkel | CIMD-Messweg B als Treiber-Baustein |
| `scripts/check_tool_budget.py` | Werkzeug-Oberflächen-Gate | Gate 6 |
| `~/.nextcloud/certificates/mcp_connector.key` und `.crt` | Signatur und Gegenprobe | Runbook Schritt 6 [VERIFIED: beide Dateien vorhanden, 3324 bzw. 1460 Bytes] |

### Alternatives Considered

| Statt | Möglich | Abwägung |
|-------|---------|----------|
| Messung gegen den 0.1.9-Kandidaten im lokalen Registry (Weg A) | Messung gegen das veröffentlichte ghcr-Image 0.1.9 nach dem Tag (Weg B) | B belegt das veröffentlichte Artefakt und ist die stärkere Aussage, hängt aber an der Owner-Freigabe und verschiebt einen Fehlerfund hinter den irreversiblen Schritt. Bei einem Fund kostet eine Korrektur eine neue Patch-Version |
| Echter Client (`claude mcp login`) | HTTP-Treiber mit `client_id` = URL eines echten Metadatendokuments | Der echte Client ist der ehrlichere Beweis (er wählt den CIMD-Weg selbst anhand von `client_id_metadata_document_supported`), kostet aber die Pseudo-Konsole. Der HTTP-Treiber belegt nur die Serverseite und muss als solcher benannt werden |
| Proof-Zeile in `docs/oauth-setup.md` | Proof-Zeile nur im Phase-Messdokument | Das Phase-Verzeichnis wird beim Milestone-Abschluss entfernt: der Verweis in `docs/oauth-setup.md:315` auf `06-09-MEASUREMENTS.md` ist heute ein toter Link, weil Commit `02dd6e1` die v1.1-Phasenverzeichnisse gelöscht hat [VERIFIED: `ls` schlägt fehl, `git log --diff-filter=D` nennt den Commit]. Eine dauerhafte Aussage gehört in `docs/`, das Rohprotokoll ins Phasenverzeichnis |

**Installation:** keine. Kein `uv add`, kein `pip install`, kein `npm install`. `uv.lock` und
der Dependency-Block von `pyproject.toml` bleiben unangetastet; geändert wird dort
ausschließlich die `version`-Zeile.

## Package Legitimacy Audit

**Nicht anwendbar.** Diese Phase installiert kein externes Paket. Der einzige Schreibzugriff
auf `pyproject.toml` ist die `version`-Zeile (Zeile 3), `uv.lock` wird nicht angefasst.
Slopcheck, Registry-Verifikation und Postinstall-Prüfung entfallen mangels Kandidaten.

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Architecture Patterns

### System Architecture Diagram

Der Messpfad der CIMD-Nachmessung (Weg A, empfohlen):

```
[claude.exe 2.1.233]                          [Browser-Schenkel: sign_in-Treiber]
  |  client_id = https://claude.ai/oauth/            |
  |             claude-code-client-metadata          | Login Flow v2 + "Approve access"
  v                                                  v
POST /mcp  --401-->  GET /.well-known/oauth-protected-resource/mcp
                          |
                          v
                     GET /.well-known/oauth-authorization-server
                          |  liest client_id_metadata_document_supported = true
                          v
                     GET /authorize?client_id=<https-URL>&...
                          |
        +-----------------+-----------------------------+
        |                                               |
        v                                               v
  [Allowlist-Prüfung]  (bd75cd8: VOR dem Fetch)   [DCR-Schalter-Kopplung]
        |                                               |
        v                                               v
  ausgehender GET https://claude.ai/oauth/...  (5120 B Limit, 5 s, TLS-Pin auf
        |                                        aufgelöste Adresse, sni_hostname)
        v
  clients-Zeile geschrieben: client_secret_hash = NULL,
  cimd_fetched_at / cimd_expires_at aus Cache-Control (300..3600 s)
        |
        v
  302 -> /authorize/consent (nennt Client-ID-Host claude.ai)
        |
        v
  POST /authorize/decide -> Rücksprung auf http://localhost:<Port>/callback
        |
        v
  POST /token -> 200  ==>  POST /mcp -> 200 (Werkzeugaufruf mit Inhalt)

Durch die ganze Kette: Client -> Caddy (127.0.0.1:8081) -> HaRP -> ExApp-Container -> Nextcloud 34.0.3
```

Der Release-Pfad (Runbook, Schritte 1 bis 8):

```
[1] fünf Versionsstellen -> [2] CHANGELOG-Block -> [3] sechs Gates lokal grün
                                                        |
                            (kein Tag existiert; Prüfschritt: git tag --list v0.1.9 leer)
                                                        v
                                          [OWNER-FREIGABE, menschliches Tor]
                                                        |
[4] git push origin main  ->  git tag v0.1.9  ->  git push origin v0.1.9   (irreversibel)
                                                        |
[5] release.yml: Version-Gleichheitsprüfung -> buildx amd64+arm64 -> ghcr.io push
                 -> build_store_release.sh -> Asset an GitHub-Release
                                                        |
[6] curl -sSLO <Asset>  ->  openssl dgst -sha512 -sign <key>  (NUR dieses Asset)
                                                        |
[7] POST /api/v1/apps/releases aus dem Seitenkontext der angemeldeten Store-Sitzung -> 201
                                                        |
[8] vier Nachweise: appapi_apps.json | curl -I Asset | ghcr-Manifest | ghcr-Tagliste
                                                        |
                                  Proof-Zeilen 4-8 in docs/store-submission.md
```

### Component Responsibilities

| Datei | Rolle in dieser Phase |
|-------|------------------------|
| `pyproject.toml:3` | `version = "0.1.8"` -> `0.1.9` [VERIFIED: grep] |
| `src/mcp_connector/__init__.py:7` | `__version__ = "0.1.8"` -> `0.1.9` [VERIFIED: grep] |
| `appinfo/info.xml:171` | `<version>0.1.8</version>` -> `0.1.9` [VERIFIED: grep] |
| `appinfo/info.xml:245` | `<image-tag>0.1.8</image-tag>` -> `0.1.9` [VERIFIED: grep] |
| `README.md:27`, `README.de.md:29`, `README.fr.md:31` | `Version 0.1.8.` / `Version 0.1.8. Die App ...` / `Version 0.1.8. L'application ...` -> `0.1.9`; die fünfte Stelle, ungegatet [VERIFIED: grep] |
| `CHANGELOG.md:12` | Neuer Block `## [0.1.9] - 2026-08-XX` oberhalb von `## [0.1.8] - 2026-08-25`; zwei Link-Referenzen am Dateiende ergänzen/umschreiben [VERIFIED: `grep "^## \["`, Tail der Datei] |
| `appinfo/info.xml` Beschreibungen (3x CDATA) | Enterprise-Absatz EN/DE/FR unter den Gate-Regeln |
| `README.md` / `.de.md` / `.fr.md` | Enterprise-Abschnitt; empfohlene Stelle nach `## Known limitations` (Zeile 481 / 495 / 511) und vor `## Development` |
| `docs/store-submission.md` | Proof-Zeilen; einzige Datei mit Vokabular-Gate-Ausnahme |
| `docs/oauth-setup.md` | dauerhafte CIMD-Proof-Zeile (Kapitel "Client ID Metadata Documents", Zeile 279 ff.) |

### Pattern 1: Der Versions-Bump als ein Plan, der keinen Tag erzeugt

**Was:** Alle fünf Stellen, der Changelog-Block, die Manifest-Beschreibungen und die
READMEs in EINEM Plan, `autonomous: true`, plus ein Prüfschritt, der behauptet, dass
`git tag --list v0.1.9` leer ist.
**Warum:** Genau so lief 11-09, und der Prüfschritt ist dort als Bedrohung T-11-62
begründet: ein Tag, der zu früh entsteht, löst ein Release aus.
**Beispiel (Prüfschritt-Form aus 11-09):**

```bash
# Alle fünf Stellen tragen dieselbe Zeichenkette
grep -c '0\.1\.9' pyproject.toml src/mcp_connector/__init__.py
grep -o '<version>[^<]*' appinfo/info.xml
grep -o '<image-tag>[^<]*' appinfo/info.xml
grep -n '^Version 0\.1\.9\.' README.md README.de.md README.fr.md
# Und kein Tag
test -z "$(git tag --list v0.1.9)" && echo "kein Tag, korrekt"
```

### Pattern 2: Der Release-Plan ist nicht autonom

**Was:** Der Plan, der Schritt 4 bis 8 ausführt, trägt `autonomous: false` und eine
must-have-Wahrheit "Der Tag v0.1.9 entsteht erst nach einer ausdrücklichen Owner-Freigabe".
**Warum:** Belegtes Muster aus 11-10 (Frontmatter wörtlich so). Zwei menschliche Tore:
Freigabe vor Schritt 4, angemeldete Store-Sitzung in Schritt 7.

### Pattern 3: Proof-Zeile nach dem Ereignis, nie davor

**Was:** Jede Zeile in der Nachweistabelle von `docs/store-submission.md` trägt Datum
(UTC), die Behauptung und den Befehl, mit dem sie geprüft wurde. Geschrieben wird sie erst,
nachdem das Ereignis eingetreten ist.
**Warum:** T-11-63 benennt genau diesen Missbrauch ("Eine Proof-Zeile wird vor ihrem
Ereignis geschrieben"); die Vokabular-Ausnahme für diese Datei ist damit begründet, dass ein
nachträgliches Umschreiben die Beweisrichtung umdrehen würde.
**Form (aus der bestehenden Tabelle):**

```markdown
| 2026-08-25 02:55Z | The download of 0.1.8 answers 200 with 45546 bytes, the size that was
signed ... | `curl -sSIL <URL>` gives 302 then 200; `openssl dgst -sha512 -verify` ...
Verified OK; `sha256sum` of both files |
```

### Pattern 4: Der Enterprise-Text als ehrlicher Plan, nicht als Feature

**Was:** Formulierung im Futur/als Vorhaben, ohne Preis, mit Kontaktadresse. Die
Manifest-Beschreibung bekommt die Kurzfassung (zwei bis drei Sätze), die READMEs die
Langfassung mit den drei Bausteinen (Audit-Log, Gruppen-Policies, SSO) und dem ausdrücklichen
Satz, dass heute keiner davon existiert.
**Warum:** D-05/D-08 verlangen es, und der Store hält die Aussage über Jahre sichtbar: eine
Zusage, die 2027 nicht eingelöst ist, steht dann als Versprechen im Katalog. `k.cherif@outlook.de`
steht bereits als `<author mail=...>` im Manifest (Zeile 173) [VERIFIED: grep], die Adresse
ist also nichts Neues im öffentlichen Artefakt.

### Anti-Patterns to Avoid

- **Eine Beschreibungsänderung ohne Release:** unsichtbar. Der Store liest das Manifest nur
  beim Release-Upload. Genau das kostete 0.1.5 und 0.1.6 [CITED: docs/store-submission.md,
  Abschnitt "The cache is not a bug" und Zeile 122].
- **Die Signatur aus `build_store_release.sh` einreichen:** das Skript sagt es selbst
  ("diagnosis only", seit `eb05a6f`), und die 0.1.8-Messung belegt die Differenz: 45710 Bytes
  lokal gegen 45546 veröffentlicht [VERIFIED: Skript-Kommentar Zeile 19-23].
- **Ein zweites Release, weil eine Änderung eine Minute nach dem Upload nicht sichtbar ist:**
  Detailseite, Katalog-Endpunkt und Suchindex laufen aus Caches, die Minuten auseinander
  liegen.
- **Einen Tag `v1.3` für den Milestone setzen:** `release.yml` triggert auf `v*` und würde
  bauen, dann an der Versions-Gleichheitsprüfung mit Exit 1 abbrechen. Milestone-Tags heißen
  `milestone-v1.3` [VERIFIED: `git tag` listet `milestone-v1.0/1.1/1.2` neben `v0.1.x`].
- **Die READMEs erst nach dem Tag bumpen:** `README.md` reist im signierten Archiv mit. Bei
  0.1.8 landete die Statuszeile 0.1.7 im veröffentlichten Tarball, weil der Fix `33cae32`
  nicht im Tag enthalten ist [VERIFIED: `git tag --contains 33cae32` nennt nur
  `milestone-v1.2`, nicht `v0.1.8`].
- **`bootstrap_exapp.sh` als Update-Weg missverstehen:** siehe Pitfall 3.

## Don't Hand-Roll

| Problem | Nicht selbst bauen | Stattdessen | Warum |
|---------|--------------------|-------------|-------|
| Store-Archiv zusammenstellen | eigenes `tar`-Kommando | `scripts/build_store_release.sh` | Erzeugt genau einen Top-Level-Ordner `mcp_connector/` mit `--numeric-owner --owner=0 --group=0`; ein Gate (`test_the_store_archive_carries_no_exempt_page`) liest die Mitgliederliste aus diesem Skript |
| Versions-Gleichheit prüfen | eigenes Skript | Gates: `tests/unit/test_exapp_env_setup.py:174-179` (Manifest gegen `__version__`, `image-tag` gegen `<version>`) plus die Prüfung in `release.yml` | Zwei unabhängige Halter existieren schon [VERIFIED: gelesen] |
| Vokabular prüfen | `grep -ri archiv` über das Repo | `uv run --no-sync pytest tests/unit/test_exapp_env_setup.py -k vocabulary` | Der Gate kennt seine Reichweite, seine zwei benannten Ausnahmen und zwei Gegenproben; ein Grep würde an der eigenen Doku und am AGPL-Text scheitern (genau der Fehler aus 12-03) |
| Nextcloud-Login im Messtreiber | eigene Login-Automatisierung | `scripts/oauth_flow_check.py:sign_in` | Existiert, ist als der eine Shortcut dokumentiert, und ein Gate (`test_no_module_under_src_automates_a_nextcloud_sign_in`) verbietet dasselbe unter `src/` |
| Werkzeug-Zahl in ein Dokument schreiben | Zahl in Prosa | Zahl aus `scripts/check_tool_budget.py`, oder Verweis auf `tests/contract/test_tool_surface.py` | Siehe Pitfall 5: ein Gate hält Zahlen in `docs/*.md` |
| Image in die Topologie bringen | `docker build` + manuelles Registrieren | `scripts/bootstrap_exapp.sh` (mit Unregister-Vorschritt, Pitfall 3) | Das Skript vergleicht den Registry-Digest gegen das gerade gebaute Image, bevor es registriert |

**Key insight:** Dieses Repository hat für fast jede Behauptung schon einen Halter. Die
Arbeit dieser Phase besteht nicht darin, Prüfungen zu erfinden, sondern die vorhandenen an
der richtigen Stelle laufen zu lassen und ihre Ergebnisse mit Datum aufzuschreiben.

## Runtime State Inventory

Diese Phase ändert Zeichenketten (Versionen) und veröffentlicht ein Artefakt. Damit hat sie
Laufzeitzustand ausserhalb des Repositories, und der ist hier vollständig benannt.

| Kategorie | Gefunden | Notwendige Handlung |
|-----------|----------|---------------------|
| Gespeicherte Daten | OAuth-Store der laufenden ExApp (`oauth.sqlite3` im Container-Volume): heute die Verbindungen der Fixture-Konten. Eine CIMD-Zeile aus dem Lauf trägt `client_secret_hash = NULL` und `cimd_fetched_at/expires_at` | Kein Migrationsbedarf. Nach der Messung die erzeugte Verbindung beenden (`/revoke` oder `occ mcp_connector:purge --force`), Fremdzustand nicht anfassen |
| Live-Service-Konfiguration | Nextcloud App Store: hält NUR die Download-URL und die einmal validierten Metadaten je Release. Die Enterprise-Beschreibung wird ausschließlich beim Upload gelesen | Beschreibungsänderung muss mit dem Release 0.1.9 hochgehen, sonst nie sichtbar (D-06) |
| Live-Service-Konfiguration | Laufende Topologie im Mischstand: `occ app_api:app:list` meldet `mcp_connector 0.1.7 [enabled]`, der Container läuft auf `ghcr.io/street1983nk/mcp_connector:0.1.6` mit `APP_VERSION=0.1.6`, Digest `sha256:5e455d73...`, `RestartCount 0`, healthy [VERIFIED: `docker inspect`, `occ app_api:app:list`] | Vor der Messung auf den 0.1.9-Kandidaten bringen und Version PLUS Image-Digest protokollieren (Konvention "Pitfall 6" aus 06-09) |
| OS-registrierter Zustand | Lokales Registry `127.0.0.1:5000` hält heute die Tags `0.1.1, 0.1.2, 0.1.3, 0.1.7` [VERIFIED: `curl /v2/mcp_connector/tags/list`] | Für Messweg A kommt `0.1.9` hinzu; alte Tags nicht löschen |
| OS-registrierter Zustand | `C:\Users\Student\.claude.json` hält die globalen MCP-Server des Owners (`firecrawl-mcp`, `obsidian`, `stitch`) und die claude.ai-Connectoren | Messweg mit echtem Client nur mit `claude mcp add ... -s local` aus einem Scratchpad-Projektverzeichnis; Datei vorher außerhalb des Repos sichern (Muster 06-09, Abschnitt 3.1) |
| Secrets / Env-Variablen | `~/.nextcloud/certificates/mcp_connector.key` + `.crt` (vorhanden), `.env.exapp` mit `HP_SHARED_KEY`, `NC_MCP_URL`, `NC_MCP_TEST_USER/PASSWORD` (gitignored, gesetzt), Store-Token nur in der Browser-Sitzung des Owners | Keine Umbenennung. Kein Credential in ein Proof-Dokument (T-05-39: auch kein Wegwerf-Credential, keine `code_challenge`, kein `state`) |
| Build-Artefakte | `dist/` hält 0.1.2, 0.1.3, 0.1.4, 0.1.7, 0.1.8 (gitignored) | Neues `dist/mcp_connector-0.1.9.tar.gz` beim Probelauf; nicht committen, nicht einreichen |
| Git-Zustand | Ein Commit auf `main` ist noch nicht gepusht (`c364a9a docs(13): gather context`) [VERIFIED: `git log origin/main..HEAD`], Arbeitsbaum sauber | Runbook Schritt 4 beginnt mit `git push origin main`, und das ist keine Formalie: bei 0.1.8 lagen an dieser Stelle 42 ungepushte Commits |
| Andere laufende Instanzen | `nc-mcp-test` (Up 10 Tage, healthy) und `findling-nextcloud` (Up 10 Tage) laufen parallel und gehören anderen Vorhaben [VERIFIED: `docker ps`] | Kein Kommando dieser Phase nennt sie. `compose.test.yml` wird nicht angefasst |

## Common Pitfalls

### Pitfall 1: Der geglückte CIMD-Abruf hinterlässt keine Logzeile
**Was schiefgeht:** Der Beweis wird im Containerlog gesucht und nicht gefunden, und die
Messung gilt als fehlgeschlagen, obwohl sie geklappt hat.
**Warum:** `oauth/cimd.py` protokolliert nur Absagen; ein erfolgreicher Abruf ist still
[CITED: 06-09-MEASUREMENTS.md Abschnitt 3.5, aus der Git-Historie rekonstruiert].
**Vermeidung:** Zwei Belege statt eines: (a) die Frische-Spalten der geschriebenen
`clients`-Zeile (`cimd_fetched_at`, `cimd_expires_at`, Fenster aus `Cache-Control`, gekappt
auf 300 bis 3600 s), (b) derselbe Abruf aus dem laufenden Container heraus ausgeführt
(`docker exec nc_app_mcp_connector python ...` mit `fetch_document_and_lifetime`).
**Frühwarnzeichen:** `/authorize` antwortet 302 und trotzdem steht nichts im Log. Das ist der
Normalfall.

### Pitfall 2: "Ohne Registrierung" muss negativ belegt werden
**Was schiefgeht:** Der Lauf gelingt, aber niemand hat gezeigt, dass `/register` nicht
gerufen wurde. Dann ist Erfolgskriterium 1 nicht belegt, sondern behauptet.
**Vermeidung:** Im Containerlog des Messfensters die Abwesenheit von `POST /register` zeigen
UND die geschriebene `clients`-Zeile mit `client_secret_hash = NULL` plus gesetztem
`cimd_fetched_at` vorlegen. Eine Registrierungszeile hat beides nicht.
**Frühwarnzeichen:** `client_id` in der `/authorize`-Zeile ist ein Zufallsstring statt der
prozentkodierten https-URL.

### Pitfall 3: `bootstrap_exapp.sh` aktualisiert nicht, es überspringt
**Was schiefgeht:** Nach dem Versions-Bump wird das Skript erneut laufen gelassen und meldet
`exapp mcp_connector: registered`, ohne das neue Image zu deployen. Gemessen würde dann
weiterhin 0.1.6/0.1.7.
**Warum:** `ensure_exapp()` prüft nur, ob die App-Id in `occ app_api:app:list` vorkommt, und
kehrt dann zurück [VERIFIED: Skript Zeile 1200-1205 gelesen].
**Vermeidung:** Vorher `occ app_api:app:unregister mcp_connector` **ohne** `--rm-data` (das
Volume und damit jede Autorisierung überlebt, belegt in `docs/store-submission.md`), dann
`bootstrap_exapp.sh` erneut; oder direkt `occ app_api:app:register` mit `--json-info` und der
neuen Version. Danach Version UND Image-Digest protokollieren.
**Frühwarnzeichen:** `docker inspect ... APP_VERSION` nennt nicht 0.1.9.

### Pitfall 4: Die Loopback-Rückadresse hat einen wechselnden Port
**Was schiefgeht:** Ein Messaufbau, der auf Port 3118 wartet, verpasst den Client.
**Warum:** Claude Code wählt aus dem Fenster 39152 bis 49151 (Windows) zufällig; der Default
3118 kommt erst zuletzt. Drei Läufe in drei Minuten ergaben 45157, 47608, 41977. Erzwingbar
ist er über `MCP_OAUTH_CALLBACK_PORT` [CITED: 06-09-MEASUREMENTS.md Abschnitt 4].
**Vermeidung:** Port aus der `/authorize`-Zeile lesen, nicht annehmen; oder
`MCP_OAUTH_CALLBACK_PORT` setzen und das im Protokoll als gesetzt kennzeichnen.

### Pitfall 5: Eine Werkzeug-Zahl in `docs/*.md` bricht ein Gate
**Was schiefgeht:** Das Messdokument schreibt "16 tools listed" (so wie 06-09 es tat) und
`tests/contract/test_tool_surface.py::test_a_documented_tool_count_is_the_current_one_or_says_which_run_it_is_from`
wird rot.
**Warum:** Der Gate liest `sorted(DOCS.glob("*.md"))` plus `README.md` und verlangt für jede
genannte Zahl entweder den aktuellen Wert (21) oder einen Verweis auf
`tests/contract/test_tool_surface.py` in derselben Datei [VERIFIED: Testquelle gelesen].
**Vermeidung:** Entweder die aktuelle Zahl nennen, oder den Halter-Pfad im Dokument
erwähnen. Achtung: dieser Gate ist **nicht** rekursiv (`glob`, nicht `rglob`), der
Vokabular-Gate ist es (`rglob`). Zwei verschiedene Reichweiten, eine Datei kann in der einen
liegen und in der anderen nicht.

### Pitfall 6: Der Vokabular-Gate erreicht jetzt CHANGELOG und ganz `docs/`
**Was schiefgeht:** Das Wort `archiv` (case-insensitiv, als Teilzeichenkette, in jeder
Sprache) landet im 0.1.9-Block oder im neuen Messdokument und wird erst beim Testlauf
gefunden. Auf Deutsch ist das besonders leicht ("Archivierung", "archiviert").
**Warum:** Seit Phase 12 deckt `test_no_public_markdown_page_carries_the_forbidden_vocabulary`
die drei READMEs, `CHANGELOG.md` und alle `docs/**/*.md` ab; einzige Ausnahme
`docs/store-submission.md`, plus `LICENSE` als wortwörtlicher AGPL-Text im Archiv-Inhalt
[VERIFIED: Testquelle gelesen].
**Vermeidung:** Den Gate früh laufen lassen, nicht am Ende:
`uv run --no-sync pytest tests/unit/test_exapp_env_setup.py -q`. Er nennt Datei und
Zeilennummer. Für ein deutsches Messdokument gilt: entweder unter `.planning/` (außer
Reichweite) oder Wortwahl beachten.

### Pitfall 7: Die fünfte Versionsstelle hat keinen Gate
**Was schiefgeht:** Der signierte Tarball trägt eine veraltete README-Statuszeile, und weil
das Asset unveränderlich ist, bleibt sie veröffentlicht.
**Warum:** Genau bei 0.1.8 passiert; der Fix `33cae32` liegt hinter dem Tag [VERIFIED].
**Vermeidung:** Die drei READMEs im selben Task wie die vier Codestellen bumpen und im
selben Prüfschritt behaupten. Nur `README.md` reist im Archiv mit, die anderen zwei sind für
den Leser des Repositories.

### Pitfall 8: Leeres `<default>` im Manifest antwortet mit 500
**Was schiefgeht:** Der Store-Upload stirbt mit HTTP 500 ohne verwertbare Meldung.
**Warum:** Ein leeres XML-Element wird zu `None`/`Array`; das Store-Feld ist
`CharField(blank=True)` ohne `null=True` [CITED: docs/store-submission.md, Pre-submission
checklist; und `variable_problems` in `test_exapp_env_setup.py`].
**Vermeidung:** Der Variablen-Gate hält es. Beim Editieren des Manifests keine
`<environment-variables>` anfassen; der Enterprise-Text liegt in `<description>`.

### Pitfall 9: Der Store-Cache sieht wie ein fehlgeschlagenes Release aus
**Was schiefgeht:** Ein zweites Release wird gebaut, um eine Änderung "durchzudrücken".
**Warum:** `appapi_apps.json`, Detailseite und Suchindex laufen aus getrennten Caches;
gemessen zwei bis zwölf Minuten Versatz. Instanzen liegen bis zu einer Stunde zurück
(`INVALIDATE_AFTER_SECONDS` 3600, `RETRY_AFTER_FAILURE_SECONDS` 300).
**Vermeidung:** 201 ist die Annahme. Danach warten und erneut fragen, niemals nachreleasen.

### Pitfall 10: Die Beschreibung rendert in zwei Pipelines unterschiedlich
**Was schiefgeht:** Der Enterprise-Absatz mit Backtick, Tabelle oder einzelnen Zeilenumbrüchen
verschwindet in der Instanz-Ansicht (nicht degradiert, verschwunden).
**Warum:** `marked` mit `breaks: false` plus `dompurify` mit Allowlist `h1..h6, strong, p, a,
ul, ol, li, em, del, blockquote`. Der Gate `description_problems` verbietet deshalb Backtick,
Tabellenzeichen `|`, Bild, horizontale Linie, HTML-Element und verlangt mindestens zwei
Absätze pro Sprache, `summary` unter 128 Zeichen [VERIFIED: Testquelle gelesen].
**Vermeidung:** Nur Fettschrift, Links, Listen, Überschriften; Absätze durch Leerzeilen. Und:
der Vokabular-Check läuft über den geparsten Baum ohne Kommentare, ein Manifest-Kommentar
darf das verbotene Wort also nennen, der Beschreibungstext nicht.

### Pitfall 11: Der Tag löst den Workflow aus, auch bei einem Tippfehler
**Was schiefgeht:** Ein Tag `v0.19` oder `v1.3` startet `release.yml`.
**Warum:** Der Trigger ist `tags: - "v*"`; die Version wird gegen `<version>` verglichen und
bei Ungleichheit bricht der Job mit Exit 1 ab [VERIFIED: Workflow gelesen].
**Vermeidung:** Tag exakt `v0.1.9`. Milestone-Tags heißen `milestone-v*` und triggern nichts.

### Pitfall 12: Signatur über das falsche Artefakt
**Was schiefgeht:** Der Store lehnt ab oder akzeptiert eine Signatur, die nicht zu den Bytes
passt, die Administratoren später herunterladen.
**Warum:** `tar.gz` ist nicht bytereproduzierbar. 0.1.8: 45710 lokal gegen 45546
veröffentlicht, unterschiedliche sha256 [CITED: docs/store-submission.md].
**Vermeidung:** Runbook Schritt 6 wörtlich: erst `curl -sSLO` vom Release, dann signieren.
Gegenprobe mit `openssl x509 -in mcp_connector.crt -pubkey -noout` und
`openssl dgst -sha512 -verify` vor der Einreichung.

### Pitfall 13: Ein Release-Asset löschen oder einen Tag umschreiben
**Was schiefgeht:** Jede spätere Installation bricht mit "Failed to get app info ... from the
Appstore", weil AppAPI von unserer URL installiert, nicht aus dem Store.
**Vermeidung:** Niemals löschen, niemals umschreiben. Eine Korrektur kostet eine neue
Patch-Version. Der `curl -I`-Nachweis aus Schritt 8 ist nicht optional.

### Pitfall 14: Der tote Verweis im CIMD-Kapitel
**Was schiefgeht:** Ein Leser von `docs/oauth-setup.md:315` folgt dem Link auf
`.planning/phases/06-h-rtung-eigennachweise-und-conference-reife/06-09-MEASUREMENTS.md` und
findet nichts; die Datei ist mit `02dd6e1` entfernt worden [VERIFIED].
**Vermeidung:** Die neue Proof-Zeile so schreiben, dass sie ohne Nachbardokument trägt
(Datum, Befehl, Ergebnis im Satz), und den alten Verweis im selben Zug schließen oder durch
eine selbsttragende Aussage ersetzen. Sonst erzeugt diese Phase denselben toten Link ein
zweites Mal, sobald v1.3 archiviert wird.

## Code Examples

### Die sechs Gates aus Runbook-Schritt 3

```bash
# Quelle: docs/store-submission.md, Schritt 3 (wörtlich)
uv run --no-sync pytest -q
uv run --no-sync ruff check .
uv run --no-sync ruff format --check .
uv run --no-sync pyright
uv run --no-sync vulture src scripts vulture_whitelist.py
uv run --no-sync python scripts/check_tool_budget.py
```

Aktueller Messwert dieser Sitzung: `tools/list: 15711 bytes, 21 tools, budget 18000`
[VERIFIED: in dieser Sitzung ausgeführt]. Die Zahl darf sich in dieser Phase nicht ändern,
weil kein Werkzeug und kein Docstring angefasst wird.

### Das Vokabular-Gate allein, für einen schnellen Zwischenlauf

```bash
uv run --no-sync pytest tests/unit/test_exapp_env_setup.py -q
# oder gezielt:
uv run --no-sync pytest tests/unit/test_exapp_env_setup.py -k "vocabulary or description" -q
```

### Topologie auf den 0.1.9-Kandidaten bringen (Messweg A)

```bash
export HP_SHARED_KEY="<aus .env.exapp>"
# Falls die Topologie steht, laeuft sie schon: docker ps zeigt caddy, harp, nc, registry
occ() { docker exec -u www-data nc-mcp-exapp-nc php occ "$@"; }

# 1. alte Registrierung loesen, Daten behalten (KEIN --rm-data)
occ app_api:app:unregister mcp_connector

# 2. Image bauen, in das Loopback-Registry pushen, App registrieren
bash scripts/bootstrap_exapp.sh

# 3. Topologie protokollieren: Version UND Digest, nie nur ein Docker-Tag
occ status | head -4
occ app_api:app:list
docker inspect nc_app_mcp_connector \
  --format '{{.Config.Image}} {{.RestartCount}} {{.State.Health.Status}}'
docker buildx imagetools inspect 127.0.0.1:5000/mcp_connector:0.1.9 \
  --format '{{.Manifest.Digest}}'
```

### Die zwei Felder, ohne die kein Client den CIMD-Weg wählt

```bash
curl -sS http://127.0.0.1:8081/exapps/mcp_connector/.well-known/oauth-authorization-server \
  | jq '{issuer, client_id_metadata_document_supported, token_endpoint_auth_methods_supported}'
```

Antwort der laufenden Instanz in dieser Sitzung [VERIFIED]:

```json
{
  "issuer": "http://127.0.0.1:8081/exapps/mcp_connector",
  "client_id_metadata_document_supported": true,
  "token_endpoint_auth_methods_supported": ["client_secret_post", "client_secret_basic", "none"]
}
```

Ohne beide Felder wählt Claude Code die dynamische Registrierung; die Entscheidung steht
wörtlich im Programmtext des Clients (`client_id_metadata_document_supported === !0` und
`clientMetadataUrl`) [CITED: 06-09-MEASUREMENTS.md Abschnitt 1].

### Der echte Client, ohne den Owner-Zustand anzufassen

```bash
# in einem Scratchpad-Projektverzeichnis, NICHT im Repo, NICHT global
claude mcp add --transport http ncmcp \
  http://127.0.0.1:8081/exapps/mcp_connector/mcp -s local
claude mcp list          # erzeugt den 401 und die zwei Discovery-Aufrufe
claude mcp logout ncmcp  # vor jedem Lauf, damit der Port neu gewaehlt wird
claude mcp login ncmcp   # verlangt ein Terminal (Pseudo-Konsole, siehe unten)
claude -p "Call the ncmcp tool files_list for the path / and then print, verbatim,
           the JSON the tool returned. Do nothing else." \
  --strict-mcp-config --mcp-config mcp.json --allowedTools "mcp__ncmcp__files_list"
```

`claude mcp login` ohne Terminal endet mit `Couldn't complete authentication for "ncmcp":
stdin isn't a terminal`. Der Vorlauf löste das über `CreatePseudoConsole` per `ctypes`
(Windows-Bordmittel, kein Paket-Install), weil `winpty` aus Git Bash ohne eigenes tty
ablehnt. Die Treiberskripte lagen bewusst im Scratchpad und nicht im Repository
[CITED: 06-09-MEASUREMENTS.md Abschnitt 3.1].

### Die vier Nachweise aus Runbook-Schritt 8

```bash
V=0.1.9
curl -sS https://apps.nextcloud.com/api/v1/appapi_apps.json \
  | jq '.[] | select(.id=="mcp_connector") | [.releases[].version]'
curl -I https://github.com/street1983nk/nextcloud-mcp-connector/releases/download/v$V/mcp_connector-$V.tar.gz
TOKEN=$(curl -sS "https://ghcr.io/token?scope=repository:street1983nk/mcp_connector:pull&service=ghcr.io" \
  | jq -r .token)
curl -sS -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/vnd.oci.image.index.v1+json" \
  https://ghcr.io/v2/street1983nk/mcp_connector/manifests/$V
curl -sS -H "Authorization: Bearer $TOKEN" \
  https://ghcr.io/v2/street1983nk/mcp_connector/tags/list
```

Erwartete Tagliste nach dem Release: die neun bisherigen plus `0.1.9` [VERIFIED: Store-API
listet heute 0.1.8 bis 0.1.0 für `mcp_connector`].

### Changelog-Vorlage für die Formatänderung

Die Übergabe aus 12-01 nennt die Vorlage ausdrücklich: der 0.1.8-Eintrag zu
`preview_truncated`. Wörtlich aus `CHANGELOG.md:68-74`:

```markdown
### Changed

- A change of the answer format, named here because a reader of the old key has to be
  updated: in an answer of `mail_browse` on the message level, the key `truncated` of a
  single entry is now called `preview_truncated`. The same word meant two things in the same
  answer, and only one of them was about the entry: on the answer level `truncated` says that
  the page of messages was cut and that there may be a next one, on a single entry it says
  that the preview text of that message was cut. The answer level keeps `truncated`
  unchanged, and no other tool is affected.
```

Für 0.1.9 tritt `talk_browse(level="messages")` und `message_truncated` an dieselbe Stelle,
plus der Hinweis, dass ein Client mit persistierter Werkzeugliste den neuen Docstring erst
nach seiner nächsten Auffrischung sieht.

## Die CIMD-Nachmessung: Ausgangslage, Wege, Empfehlung

### Was der Debt-Befund wörtlich verlangt

`.planning/milestones/v1.1-MILESTONE-AUDIT.md:20` [VERIFIED: gelesen]:

> "W-5 aus dem Integrations-Check: der einzige E2E-Live-Beleg der CIMD-Kette
> (06-09-MEASUREMENTS) ist aelter als die Review-Fixes a47bb57/bd75cd8; die geaenderten Pfade
> sind unit-gepinnt (auch an den Aufrufstellen, W-6-Pins), ein neuer Live-Rundlauf steht aus"

Die zwei Fixes:
- `a47bb57` "WR-01/WR-03 keep the CIMD refetch off the hot paths (may_fetch=False)", ändert
  `oauth/provider.py` und `oauth/verifier.py`
- `bd75cd8` "WR-02 ask the allowlist before the CIMD fetch, not after", ändert
  `oauth/provider.py`

Beide sind seit `v0.1.3` in jedem Tag enthalten [VERIFIED: `git tag --contains`]. Der letzte
Live-Beleg lief gegen 0.1.2, also davor. Das ist die ganze Lücke.

### Der Vorlauf, den die Nachmessung wiederholen muss

Aus `06-09-MEASUREMENTS.md` (aus `git show 02dd6e1^:...` rekonstruiert, liegt im Scratchpad
dieser Sitzung) [CITED: Git-Historie]:

| Element | Wert im Vorlauf (2026-08-20) |
|---------|------------------------------|
| Topologie | `compose.exapp.yml`, Projekt `nc-mcp-exapp`, `http://127.0.0.1:8081` (Caddy, nur Loopback) |
| Nextcloud | 34.0.3 (34.0.3.2) laut `occ status` |
| Connector | 0.1.2, Image `127.0.0.1:5000/mcp_connector:0.1.2`, Digest genannt, `RestartCount 0` |
| Client | Claude Code 2.1.233 (heute dieselbe Version installiert) |
| client_id | `https://claude.ai/oauth/claude-code-client-metadata`, wörtlich in der `/authorize`-Zeile prozentkodiert |
| Dokument | 317 Bytes, 200, `Cache-Control: public, max-age=300`, zwei portlose Loopback-Rückadressen |
| Geschriebene Zeile | `client_secret_hash None`, `cimd_fetched_at`/`cimd_expires_at` mit 300-s-Fenster, `metadata_json` mit `token_endpoint_auth_method none` |
| Werkzeugaufruf | `files_list` auf `/` mit echtem Inhalt (Fixture-Marker `mcp-private-...`, `mcp-share-...`) |
| Konto | `alice` (Fixture), nicht `jane` (Demo-Substanz, Passwort nirgends) |
| Gegenproben | drei Kontrollen mit gezählten ausgehenden Sockets (DCR aus, CIMD aus, Allowlist) plus vier Rückadressen-Varianten |

### Die drei Messwege

| Weg | Was gemessen wird | Kosten | Risiko |
|-----|-------------------|--------|--------|
| **A (empfohlen)** | 0.1.9-Kandidat aus dem Quellstand, gebaut und in `127.0.0.1:5000` gepusht, echter Client `claude mcp login` über Pseudo-Konsole | Unregister/Register plus Pseudo-Konsolen-Treiber (Muster existiert, Skript nicht mehr) | Mittel: der Treiber muss neu geschrieben werden, aber die Client-Version ist unverändert |
| B | Derselbe Kandidat, aber statt des echten Clients ein HTTP-Treiber, der `client_id` = `https://claude.ai/oauth/claude-code-client-metadata` sendet und den Browser-Schenkel über `oauth_flow_check.sign_in` fährt | Gering, ein Skript im Scratchpad | Die Aussage ist schwächer und muss ehrlich benannt werden: sie belegt die Serverseite, nicht die Client-Wahl. Muss als solche im Protokoll stehen |
| C | Die heute laufende Instanz (0.1.6-Image, AppAPI meldet 0.1.7) | Nahe null | Erfüllt W-5 buchstäblich (nach den Fixes), belegt aber NICHT die Fassung, die als 0.1.9 veröffentlicht wird. Der Roadmap-Wortlaut "gegen die laufende Topologie" wäre erfüllt, der Geist der Phase nicht |

**Empfehlung:** A, und wenn der Pseudo-Konsolen-Treiber im Ausführungsfenster nicht steht,
A-Topologie mit B-Treiber plus einer ausdrücklichen Zeile im Protokoll, was damit belegt ist
und was nicht. Beides läuft VOR dem Tag. C nur als Notausgang, dann mit klarer Benennung im
Protokoll.

**Warum vor dem Tag:** Der Tag hängt an einer Owner-Freigabe (D-01), die zeitlich offen ist.
Ein Beweis hinter dieser Freigabe macht Erfolgskriterium 1 von einem Menschen abhängig, der
gerade eine andere Frage beantwortet. Der Quellstand ist derselbe, das Image ist derselbe
Dockerfile-Bau, und der Unterschied zum veröffentlichten Artefakt (Registry-Adresse) berührt
den OAuth-Pfad nicht.

### Wo die Proof-Zeile hingehört

Erfolgskriterium 1 erlaubt "in der Doku oder im Messdokument der Phase". Empfehlung: beides,
mit klarer Arbeitsteilung.

1. **Dauerhaft:** eine datierte, selbsttragende Zeile im Kapitel "Client ID Metadata
   Documents" von `docs/oauth-setup.md` (heute beginnt es Zeile 279 mit "Measured live on
   2026-08-20 against Claude Code 2.1.233"). Diese Zeile überlebt die Archivierung des
   Phasenverzeichnisses. Sie fällt unter den Vokabular-Gate und unter den Werkzeugzahl-Gate,
   also Wortwahl und Zahlen beachten.
2. **Rohprotokoll:** `.planning/phases/13-cimd-nachmessung-und-release-0-1-9/13-MEASUREMENTS.md`,
   im Aufbau von 06-09: Topologie-Tabelle zuerst, dann eine Frage pro Abschnitt, Logzeilen
   wörtlich, Credentials als `<gekürzt>`. Außerhalb jeder Gate-Reichweite, dafür endlich.

## Der Changelog-Block 0.1.9: was hineingehört, was nicht

Die Phase-12-Zusammenfassungen legen das ungewöhnlich genau fest [VERIFIED: alle vier
SUMMARYs gelesen]:

| Änderung | In den Changelog? | Begründung (Quelle) |
|----------|-------------------|---------------------|
| `talk_browse(level="messages")`: Eintragsschlüssel `truncated` heißt `message_truncated`, Antwortebene behält `truncated` | **JA**, unter `### Changed`, als Formatänderung, mit dem Hinweis auf die persistierte Werkzeugliste | 12-01-SUMMARY.md:99 nennt Wortlaut und Vorlage (`preview_truncated` aus 0.1.8) |
| README-Beispiel für einen unbekannten Suchprovider: `spreed` -> `talk-conversations` | **JA**, als Doku-Korrektur | 12-04-SUMMARY.md:193 gibt sogar einen Formulierungsvorschlag |
| `_ID_KIND` durch `ids.encode_mail` ersetzt; `ids.parse` lehnt Whitespace-Reste in `url:`/`file:`/`note:`/`event:` ab | **NEIN** | 12-02-SUMMARY.md:94: Mail-Id byte-identisch, die neuen Absagen betreffen Formen, die dieser Server nie ausgegeben hat |
| `talk_tools._room` -> `talk_tools.one_room` | **NEIN** | 12-04-SUMMARY.md:100-102: rein intern, kein Werkzeugname, kein Antwortschlüssel, keine Id-Form; `tools/list` unverändert 15711 Bytes / 21 Werkzeuge |
| Neue Gates (`test_module_boundaries.py`, Vokabular-Reichweite, T-11-29-Regressionstest) | **NEIN** | Keine nutzersichtbare Wirkung |
| Enterprise-Abschnitt in READMEs und Store-Beschreibung | **Empfehlung: JA**, eine Zeile | Präzedenz: die Blöcke 0.1.5, 0.1.6 und 0.1.7 beschreiben Store-Text-Änderungen als eigene Einträge. Diese ist die sichtbarste Änderung des Releases für einen Store-Leser. Als Discretion markiert, weil keine Übergabe sie fordert |

Formales: kein `## [Unreleased]`-Abschnitt existiert (nur die Link-Referenz)
[VERIFIED: `grep "^## \["`]. Der Block kommt direkt über `## [0.1.8] - 2026-08-25`. Zwei
Link-Referenzen am Dateiende: `[Unreleased]` auf `compare/v0.1.9...HEAD` umschreiben,
`[0.1.9]` als `compare/v0.1.8...v0.1.9` ergänzen. Der Block braucht einen Einleitungsabsatz
im Ton der Vorgänger: dieses Release ist ein Pflege-Release, kein neues Werkzeug, ein
umbenannter Schlüssel, eine Doku-Korrektur, ein neuer Abschnitt im Store-Text.

## Der Enterprise-Fake-Door: Regeln, Präzedenz, Platzierung

### Was der Store duldet

Die Katalogabfrage dieser Sitzung über alle 409 für Nextcloud 34 gelisteten Apps findet
kommerzielle Hinweise in Beschreibungen mehrfach, unter anderem [VERIFIED: `apps.json` der
Store-API, Sprachvariante `en`]:

- `attendance`: "The mobile app is free for 30 days per Nextcloud instance, then one yearly
  subscription covers the whole ..."
- `signotecsignosignuniversal`: "Start today with a 30-day free trial, no payment details
  required and no subscription commitment."
- `ktec_talkbot`: "Bring your own model or your own subscription ... Use a CLI subscription
  instead of API tokens."

Unter den 27 ExApps findet sich kein Präzedenzfall für ein bezahltes Add-on
[VERIFIED: `appapi_apps.json`], aber der Store trennt an dieser Stelle nicht zwischen App-
Typen: die Annahme eines Releases ist automatisiert (Signatur, Ordnerstruktur,
`pre-info.xslt` plus `info.xsd`), es gibt keinen redaktionellen Text-Gate
[CITED: docs/store-submission.md, Schritt 7]. Das Risiko einer Ablehnung wegen des
Enterprise-Absatzes ist damit sehr gering. `[ASSUMED]` bleibt die Aussage, dass es keine
gesonderte Store-Richtlinie gegen Werbung für kommerzielle Add-ons gibt: geprüft wurde die
Praxis, nicht ein Regelwerk.

### Die harten Regeln für den Manifest-Text

Aus `description_problems` in `tests/unit/test_exapp_env_setup.py` [VERIFIED: gelesen]:

- kein Backtick
- kein `|` irgendwo (auch nicht in Prosa)
- kein Bild, keine horizontale Linie (`---` allein auf einer Zeile), kein HTML-Element
- mindestens zwei durch Leerzeilen getrennte Absätze pro Sprache
- `summary` maximal 128 Zeichen (die `summary`-Zeilen werden in dieser Phase nicht angefasst)
- das verbotene Wort `archiv` nirgends im Elementtext (Kommentare ausgenommen)
- erlaubt sind: Überschriften, Fettschrift, Kursiv, Links, Listen, Blockzitat

### Platzierungsempfehlung

| Datei | Stelle | Begründung |
|-------|--------|------------|
| `README.md` | neuer `## Enterprise`-Abschnitt nach `## Known limitations` (Zeile 481 ff.), vor `## Development` | Die Grenzen-Sektion ist der Ort, an dem ein IT-Verantwortlicher liest, was fehlt; der Enterprise-Absatz beantwortet dort die naheliegende nächste Frage |
| `README.de.md` | analog nach `## Bekannte Einschränkungen` (Zeile 495) | Struktur der drei READMEs ist deckungsgleich |
| `README.fr.md` | analog nach `## Limitations connues` (Zeile 511) | dito |
| `appinfo/info.xml` (3x) | neuer Abschnitt zwischen `### Under your control` / `### In Ihrer Hand` / `### Sous votre contrôle` und `### Resources` / `### Weiterführendes` / `### Pour aller plus loin` | Direkt nach dem Absatz über Kontrolle und Schalter, vor den Links; kurz halten, zwei bis drei Sätze |

Inhaltlich müssen alle vier Fassungen dasselbe sagen: die drei Bausteine (Audit-Log,
Gruppen-Policies, SSO/IdP-Anbindung), das Wort "geplant" beziehungsweise "planned"/"prévu",
die ausdrückliche Aussage, dass heute keiner davon existiert, und die Kontaktadresse
`k.cherif@outlook.de`. Kein Preis, kein Datum, keine Zusage.

### Der Issue-Entwurf (D-07)

Empfohlener Ort: `docs/contrib/enterprise-signals-issue.md`. Der Ordner existiert und hält
bereits genau so ein Artefakt (`docs/contrib/227-pr-body.md`, ein vorbereiteter PR-Text)
[VERIFIED: `ls docs/contrib`]. Achtung, zwei Kopplungen: (1) der Ordner liegt in der
`rglob`-Reichweite des Vokabular-Gates, (2) ein Gate behauptet ausdrücklich die Existenz von
`docs/contrib/227-pr-body.md` als Beweis, dass der Walk rekursiv ist, diese Datei darf also
nicht verschoben werden. Der Entwurf trägt Titel und Body und einen Satz, dass die
Veröffentlichung eine Owner-Entscheidung ist. Kein `gh issue create` in dieser Phase.

Titelvorgabe aus dem validation-plan: "Enterprise features: what would your org need before
allowing MCP access?" Go-Kriterium (gehört in den Entwurf, damit später messbar ist, wofür er
da war): mindestens fünf qualifizierte Org-Signale mit über 100 Nutzern in sechs Wochen, oder
ein Ankerkunde mit Pilotwunsch.

## Project Constraints (from CLAUDE.md)

| Direktive | Wirkung auf diese Phase |
|-----------|-------------------------|
| Code und README auf Englisch, Projektkommunikation Deutsch | Enterprise-Text EN/DE/FR wie die bestehenden READMEs; Planungsdokumente deutsch |
| Keine Em-Dashes, echte Umlaute in deutschen Texten | Gilt für `README.de.md`, die deutsche Manifest-Beschreibung, alle Planungsartefakte |
| `ruff check .` und `ruff format --check .` vor dem Push, über das ganze Repo | Gates 2 und 3 des Runbooks |
| Alle Pfade testen (Happy/Fehler/Edge/no_data) | Für diese Phase heißt das: die CIMD-Messung braucht mindestens eine Gegenprobe, nicht nur den geglückten Lauf |
| Repo public auf GitHub `street1983nk`, nicht Akara-GitLab | `gh` ist als `street1983nk` angemeldet [VERIFIED] |
| Keine destruktiven Writes, kein neues Werkzeug | Gilt: diese Phase ändert keinen Werkzeugcode |
| GSD-Workflow: keine direkten Repo-Edits außerhalb eines GSD-Kommandos | Alle Änderungen laufen über die Pläne dieser Phase |
| Commits nach jedem Edit, ohne Rückfrage; keine Claude-Attribution | `commit_docs: true` in der Config; Tag ist die eine Ausnahme (Owner-Freigabe) |

## State of the Art

| Früher | Heute | Seit | Wirkung |
|--------|-------|------|---------|
| Runbook Schritt 1 nennt vier Versionsstellen | Schritt 1 nennt vier plus die drei README-Statuszeilen | `eb05a6f` (25.08.) | Die fünfte Stelle ist dokumentiert, aber weiterhin ungegatet |
| `build_store_release.sh` gab eine Signatur aus, die einreichbar aussah | Das Skript sagt jetzt selbst "diagnosis only" und verweist auf Schritt 6 | `eb05a6f` | Eine Fehlerquelle geschlossen, die 0.1.2 fast gekostet hätte |
| Vokabular-Gate prüfte nur `appinfo/info.xml` | Gate prüft drei READMEs, `CHANGELOG.md` und `docs/**/*.md` rekursiv | Phase 12 (`a7ee8ee`, WR-05) | Der 0.1.9-Block entsteht unter der Regel statt nachträglich geprüft zu werden |
| Nur DCR (`/register`) | CIMD als zweiter Weg, in der Admin-Form abschaltbar | 0.1.3 | Der Weg, den die MCP-Spec 2026-07-28 vorzieht und den Claude Code nutzt |
| Store-Kategorie nur `integration` | `ai`, `integration`, `tools` | 0.1.7 | Nicht Gegenstand dieser Phase, aber die Kategorien werden beim Upload erneut validiert |

**Veraltet / nicht mehr benutzen:**
- Docker Socket Proxy als Deploy-Daemon (deprecated, Entfernung für NC 35 geplant): die
  Topologie fährt HaRP.
- Der Verweis auf `06-09-MEASUREMENTS.md` in `docs/oauth-setup.md`: Ziel existiert nicht mehr.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Es gibt keine gesonderte Store-Richtlinie, die Werbung für ein kommerzielles Add-on in der Beschreibung verbietet; geprüft ist nur die gelebte Praxis (drei Beispiele) und dass die Annahme automatisiert läuft | Enterprise-Fake-Door | Gering. Im schlechtesten Fall eine Rückfrage des Store-Teams nach dem Upload; das Release selbst ist dann schon gelistet. Eine Korrektur kostet eine neue Patch-Version |
| A2 | Claude Code 2.1.233 verhält sich beim CIMD-Weg identisch zum 2026-08-20-Lauf (dieselbe Version, kein Update dazwischen) | CIMD-Nachmessung | Gering; falls doch abweichend, ist genau das der Messbefund |
| A3 | Der Pseudo-Konsolen-Treiber aus 06-09 existiert nicht mehr (er lag bewusst im Scratchpad) und muss für Weg A neu geschrieben werden | Messwege | Mittel für die Aufwandsschätzung: wenn er neu entsteht, kostet Weg A deutlich mehr als Weg B. Der Plan sollte einen Fallback auf Weg B vorsehen |
| A4 | `occ app_api:app:unregister mcp_connector` ohne `--rm-data` erhält Volume und Autorisierungen auch beim Wechsel von einem ghcr-Image auf ein Registry-Image | Pitfall 3 | Mittel: im Fehlerfall sind die Fixture-Verbindungen weg und müssen neu erzeugt werden; kein Produktivdatenverlust. `docs/store-submission.md` belegt das Verhalten für `unregister` ohne `--rm-data`, aber nicht für einen Registry-Wechsel |
| A5 | Der Mischstand der laufenden Topologie (AppAPI 0.1.7, Container-Image 0.1.6) ist ein Restzustand eines früheren Update-Versuchs und kein Defekt | Runtime State Inventory | Gering: Weg A ersetzt beides ohnehin. Wenn es doch ein Defekt ist, fällt er beim Registrieren auf |
| A6 | Der Store nimmt die 0.1.9-Beschreibung mit dem Enterprise-Absatz ohne 500er an (keine leeren Elemente, kein neues Element) | Release-Pipeline | Gering: der Variablen-Gate hält die bekannte 500er-Ursache, und die Beschreibung ist ein bestehendes Element |

## Open Questions (RESOLVED)

1. RESOLVED (Plan 13-03 Task 2: Weg A mit benanntem Fallback B). **Wird Weg A mit echtem Client innerhalb der Phase machbar, oder fällt sie auf Weg B?**
   - Bekannt: Client-Version identisch, `claude mcp login` verlangt ein tty, der Vorlauf löste
     das mit `CreatePseudoConsole` per `ctypes`.
   - Unklar: ob der Treiber in vertretbarer Zeit wieder entsteht.
   - Empfehlung: Der Plan beginnt mit Weg A und trägt Weg B als benannten Fallback mit
     Pflicht zur ehrlichen Einordnung im Protokoll. Nicht beide Wege parallel bauen.

2. RESOLVED (Plan 13-02 Task 3: Zeile unter Added). **Gehört die Enterprise-Zeile in den Changelog?**
   - Bekannt: Präzedenz existiert (0.1.5 bis 0.1.7 beschreiben Store-Text-Änderungen), keine
     Übergabe fordert sie.
   - Empfehlung: ja, eine Zeile unter `### Added`, denn für einen Store-Leser ist es die
     sichtbarste Änderung dieses Releases. Discretion des Planers.

3. RESOLVED (Plan 13-03 Task 3: Verweis wird geschlossen). **Wird der tote Verweis in `docs/oauth-setup.md` in dieser Phase geschlossen?**
   - Bekannt: Der Link zeigt auf ein mit `02dd6e1` entferntes Phasenverzeichnis, und die neue
     Proof-Zeile entsteht genau in diesem Kapitel.
   - Empfehlung: ja, im selben Edit; sonst entsteht beim nächsten Milestone-Abschluss der
     zweite tote Link derselben Art. Kleiner Task, klar abgegrenzt.

4. RESOLVED (Plan 13-03 Task 3: genau eine Gegenprobe NC_MCP_OAUTH_CIMD=0). **Wie viel Gegenprobe braucht die Nachmessung?**
   - Bekannt: Der Vorlauf hatte drei Schalter-Kontrollen mit gezählten ausgehenden Sockets und
     vier Rückadressen-Varianten. Erfolgskriterium 1 verlangt nur den geglückten Rundlauf.
   - Empfehlung: eine Gegenprobe genügt und ist Pflicht (globale Regel "alle Pfade"):
     `NC_MCP_OAUTH_CIMD=0` refused, ohne dass ein Paket nach außen geht. Die zwei
     Schalter-Wege sind seit 0.1.3 Admin-Werte, für `NC_MCP_OAUTH_CIMD` ist die
     Admin-Form der Weg (`occ app_api:app:config:set` plus disable/enable), nicht eine
     Neuregistrierung.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Docker Engine | Topologie, `occ`, Image-Bau | ja | 29.5.2 | keiner |
| Laufende Topologie `nc-mcp-exapp` (Caddy, HaRP, Nextcloud, Registry, GreenMail) | CIMD-Messung | ja, alle up | NC 34.0.3.2, HaRP release | Neu starten per `compose.exapp.yml` |
| ExApp-Container | Messung | ja, healthy, 0 Restarts | Image 0.1.6, AppAPI meldet 0.1.7 | muss auf 0.1.9 gehoben werden |
| Lokales Registry `127.0.0.1:5000` | Messweg A | ja, hält 0.1.1/0.1.2/0.1.3/0.1.7 | registry:2 | Messweg C |
| `claude` CLI | Messweg A | ja | 2.1.233 | Messweg B |
| Pseudo-Konsolen-Treiber | `claude mcp login` ohne tty | nein (lag im Scratchpad von Phase 6) | - | Messweg B (HTTP-Treiber mit `sign_in`) |
| `uv` | alle sechs Gates | ja | 0.11.7 | keiner |
| `gh`, angemeldet | Runbook Schritt 5, Issue (nur nach Freigabe) | ja | 2.92.0, `street1983nk`, Scopes `repo`, `workflow` | Workflow-Seite im Browser |
| `openssl` | Signatur, Gegenprobe | ja | 3.5.6 | keiner |
| Signierschlüssel + Zertifikat | Runbook Schritt 6 | ja | `~/.nextcloud/certificates/mcp_connector.{key,crt}` | keiner, harter Blocker |
| `curl`, `jq` | Nachweise Schritt 8 | ja | 8.19.0, jq-1.8.1 | Python |
| Angemeldete Store-Sitzung (Browser) | Runbook Schritt 7 | Owner-seitig, nicht prüfbar von hier | - | Formular unter `/developer/apps/releases/new`, oder `curl` mit `NC_STORE_TOKEN` |
| Owner-Freigabe für den Tag | Runbook Schritt 4 | offen | - | keiner, per D-01 ein hartes Tor |
| `.env.exapp` mit `HP_SHARED_KEY` und Testkonto | Messung, `oauth_flow_check.py` | ja, gesetzt (gitignored) | - | keiner |

**Fehlende Abhängigkeiten ohne Fallback:**
- Owner-Freigabe für den Tag (D-01) und die angemeldete Store-Sitzung (Schritt 7). Beide
  gehören in einen `autonomous: false`-Plan; die Phase muss ohne sie bis Schritt 3
  vollständig abschließbar sein.

**Fehlende Abhängigkeiten mit Fallback:**
- Pseudo-Konsolen-Treiber: Fallback Messweg B mit ausdrücklicher Einordnung im Protokoll.

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | ja (gemessen, nicht geändert) | OAuth 2.1 mit PKCE S256; CIMD-Client ist per Definition public, kein Secret. Keine Codeänderung in dieser Phase |
| V3 Session Management | nein | Kein Session-Zustand wird angefasst |
| V4 Access Control | ja (gemessen) | Allowlist wird VOR dem ausgehenden Fetch gefragt (`bd75cd8`); `NC_MCP_OAUTH_DCR=0` schließt den CIMD-Weg mit |
| V5 Input Validation | ja (indirekt) | `cimd.is_cimd_client_id` plus `validate_document`; Dokument-Limit 5120 Bytes, Timeout 5 s, TLS-Pin auf die aufgelöste Adresse |
| V6 Cryptography | ja | Signatur des Release-Assets: RSA-4096-Schlüssel, SHA-512, `openssl` nur mit den Runbook-Kommandos. Nichts selbst bauen |
| V14 Configuration / Supply Chain | ja, Schwerpunkt | Tag-Integrität, unveränderliche Assets, Multi-Arch-Image aus dem Workflow, Signatur über die veröffentlichten Bytes |

### Known Threat Patterns für diese Phase

| Muster | STRIDE | Standard-Gegenmaßnahme |
|--------|--------|------------------------|
| Eine der fünf Versionsstellen bleibt auf 0.1.8 | Tampering | Prüfschritt über alle fünf plus Manifest-Gate plus Versions-Gleichheitsprüfung in `release.yml` (Muster T-11-57) |
| Ein Tag entsteht ohne Owner-Freigabe | Denial of Service | Der Bump-Plan behauptet ausdrücklich `git tag --list v0.1.9` leer; der Tag liegt in einem `autonomous: false`-Plan (Muster T-11-62) |
| Eine Proof-Zeile wird vor ihrem Ereignis geschrieben | Repudiation | Nur Zeilen für eingetretene Ereignisse; Form ist Datum plus Befehl plus Ergebnis (Muster T-11-63) |
| Das lokal gebaute Archiv wird für das signierte Artefakt gehalten | Tampering | Probelauf ausdrücklich als Strukturprüfung markieren; signiert wird nur das heruntergeladene Asset, mit `sha256sum`-Vergleich als Beleg |
| Ein Credential landet im Messprotokoll | Information Disclosure | Konvention aus 06-09/T-05-39: kein Token, kein Code, keine `code_challenge`, kein `state`, kein App-Passwort, auch kein Wegwerf-Wert; gekürzt als `<gekürzt>` |
| Der Enterprise-Text verspricht mehr, als es gibt | Spoofing | Jede Aussage als Plan formuliert, mit dem ausdrücklichen Satz, dass heute keiner der drei Bausteine existiert (Muster T-11-60) |
| Der Messlauf greift fremde Instanzen oder den Owner-MCP-Zustand an | Tampering | Nur die Topologie `nc-mcp-exapp` ansprechen; `claude mcp add ... -s local` aus einem Scratchpad-Verzeichnis; `.claude.json` vorher außerhalb des Repos sichern |
| Paketinstallation schleicht sich ein | Supply Chain | Kein `uv add`, kein `pip install`, kein `npm install`; `uv.lock` bleibt unangetastet (Muster T-11-SC) |
| Das Release-Asset wird gelöscht oder ein Tag umgeschrieben | Denial of Service | `curl -I` in Schritt 8 als Pflichtnachweis; Regel dauerhaft im Runbook |

## Sources

### Primary (HIGH confidence)
- `docs/store-submission.md` (in dieser Sitzung vollständig gelesen): Runbook Schritte 1 bis 8, Nachweistabelle aller neun Releases, Signatur-Falle, 500er-Falle, Cache-Verhalten, Store-Suchmessungen
- `tests/unit/test_exapp_env_setup.py` (Zeilen 143-180, 1686-1800, 1955-2120): Manifest-Gate, `description_problems`, `variable_problems`, Vokabular-Gate mit Reichweite und Ausnahmen
- `tests/contract/test_tool_surface.py` (Zeilen 736-782): README-Werkzeugtabelle und der Werkzeugzahl-Gate über `docs/*.md`
- `.github/workflows/release.yml`, `scripts/build_store_release.sh`, `scripts/bootstrap_exapp.sh`, `scripts/oauth_flow_check.py` (gelesen)
- `.planning/phases/12-.../12-VERIFICATION.md` und die vier 12-0x-SUMMARY.md: Changelog-Übergaben wörtlich
- `.planning/milestones/v1.1-MILESTONE-AUDIT.md`: Debt-Befund W-5 im Wortlaut
- `06-09-MEASUREMENTS.md`, rekonstruiert per `git show 02dd6e1^:...`: Topologie, Client-Programmtext, Rundlauf, Portspalte, Gegenproben
- `git show 568346c:.planning/phases/11-.../11-09-PLAN.md` und `11-10-PLAN.md`: bewährte Plan-Struktur für Bump und Release, inklusive Bedrohungstabelle
- Laufende Topologie, in dieser Sitzung gemessen: `docker ps`, `docker inspect`, `occ status`, `occ app_api:app:list`, AS-Metadaten-Abruf, Registry-Tagliste, `check_tool_budget.py`
- Store-API: `https://apps.nextcloud.com/api/v1/appapi_apps.json` (27 ExApps, `mcp_connector` mit 0.1.8 bis 0.1.0) und `https://apps.nextcloud.com/api/v1/platform/34.0.0/apps.json` (409 Apps, kommerzielle Formulierungen)

### Secondary (MEDIUM confidence)
- `C:/Users/Student/scripts/docs/specs/ideation-isv-monetarisierung-2026-08-25/validation-plan.md` und `concept-brief-1-connector-enterprise.md`: Fake-Door-Methode, Go/No-Go, die drei Bausteine
- `.planning/STATE.md` (Entscheidungen zu Phase 6, insbesondere zur Admin-Form und zu `NC_MCP_OAUTH_CIMD`)
- `NEXT.md` (ISV-Stand 25.08., Call 14.09., offene Fake-Door-Punkte)

### Tertiary (LOW confidence)
- keine. Es wurde keine Websuche gebraucht: alle Fragen dieser Phase sind am Repo, an der
  laufenden Topologie oder an der Store-API entscheidbar.

## Metadata

**Confidence breakdown:**
- Release-Weg und Gates: HIGH. Runbook, Workflow und Gate-Quellen gelesen; neun
  Vorgänger-Releases als Belegtabelle; Werkzeuge und Schlüssel in dieser Sitzung geprüft.
- Die fünf Versionsstellen und der Changelog-Inhalt: HIGH. Datei und Zeile je Stelle
  gemessen; die Changelog-Übergaben stehen wörtlich in den Phase-12-Zusammenfassungen.
- CIMD-Ausgangslage: HIGH. Der Debt-Befund, die zwei Fix-Commits und ihre Tag-Zugehörigkeit
  sind verifiziert; die laufende Topologie ist inventarisiert; die AS-Metadaten wurden live
  abgefragt.
- CIMD-Messweg-Aufwand: MEDIUM. Ob der Pseudo-Konsolen-Treiber schnell wieder entsteht, ist
  offen (A3); deshalb ist der Fallback benannt.
- Enterprise-Fake-Door: MEDIUM-HIGH. Die Gate-Regeln sind verifiziert, die Store-Praxis
  belegt; die Abwesenheit einer gegenteiligen Richtlinie ist eine Annahme (A1).

**Research date:** 2026-08-25
**Valid until:** 2026-09-08 (14 Tage; Store-Verhalten und Client-Version sind die zwei
beweglichen Teile, beide heute gemessen)
