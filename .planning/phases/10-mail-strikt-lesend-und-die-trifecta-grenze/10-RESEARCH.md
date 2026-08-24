# Phase 10: Mail strikt lesend und die Trifecta-Grenze, Recherche

**Recherchiert:** 2026-08-24
**Domäne:** Nextcloud Mail 5.11.1 als lesende MCP-Werkzeugfamilie, App-Erkennung ohne Capabilities-Eintrag, Benennung der Exfiltrationskette
**Confidence:** HIGH für die API-Fakten (gegen die installierte App-Fassung und live gegen die laufende Instanz gemessen), MEDIUM für die Feldformen mit echten IMAP-Daten (kein IMAP-Server in der Topologie), HIGH für die Codebasis-Anknüpfungspunkte

---

## Zusammenfassung

Der wichtigste Befund zuerst, und er verschiebt den Schnitt dieser Phase nach oben statt nach
unten: **Mail 5.11.1 hat für alle drei Leseebenen deklarierte OCS-Routen.** Die Übergabe aus
Phase 8 sagt, das Rückgrat sei die eine OCS-Volltextroute und die drei Listen-Wege trügen
`SCOPE_IGNORE`. Das gilt für die internen Frontend-Routen `/apps/mail/api/...`, die der Spike
gemessen hat. Daneben existiert aber ein zweiter, vollständiger Satz Routen im `ocs`-Block und
als `#[ApiRoute]`, und der steht in der `openapi.json` der App, die mit ihr ausgeliefert wird:
`GET /ocs/v2.php/apps/mail/account/list`, `GET /ocs/v2.php/apps/mail/ocs/mailboxes`,
`GET /ocs/v2.php/apps/mail/ocs/mailboxes/{mailboxId}/messages` und
`GET /ocs/v2.php/apps/mail/message/{id}`. Alle vier sind live unter reiner
AppAPI-Impersonation gemessen und antworten aus App-Code. Damit braucht diese Phase **keine
einzige SCOPE_IGNORE-Route**, das Ersetzbarkeitsrisiko der Übergabe schrumpft von "das
Rückgrat der Familie" auf "gar nicht benutzt", und das Gate wird schärfer, weil die vier
erlaubten Pfadformen abzählbar sind.

Der zweite Befund betrifft SRV-06 und ist ebenfalls gemessen statt geraten: Mail veröffentlicht
keinen Capabilities-Abschnitt (die Liste der Abschnitte auf der laufenden 34.0.3 enthält
`spreed`, `tables`, `notes`, `deck`, aber kein `mail`), und
`GET /ocs/v2.php/core/navigation/apps` beantwortet die Frage stattdessen: mit aktivierter
Mail-App steht dort ein Eintrag mit `id: "mail"`, nach `occ app:disable mail` **und einem
Neustart der Nextcloud** ist er weg, und die Mail-OCS-Routen antworten dann mit 404 im
OCS-Envelope (`statuscode` 998), nicht mit einer Loginseite. Der Neustart ist kein Detail: ohne
ihn bleibt die abgeschaltete App sowohl in der Navigation als auch auf ihren Routen sichtbar,
genau wie es Phase 1 für die Capabilities schon festgehalten hat.

Der dritte Befund ist eine Kostenstelle, die den Plan strukturiert: das Token-Budget hat
**642 Bytes Luft** (gemessen 14358 von 15000 bei 20 Werkzeugen), und das nächstliegende
Vorbild `talk_browse` kostet allein 886 Bytes. `mail_browse` passt konstruktiv nicht in den
Rest. Diese Phase muss das Budget-Gate mit einer eigenen, datierten Messung anheben, obwohl
die Roadmap die Neu-Verankerung (TOOL-15) in Phase 11 führt. Sonst ist der Phasenabschluss rot.

**Primäre Empfehlung:** Ein Client `clients/mail.py`, der ausschliesslich die vier deklarierten
OCS-Routen baut, ein Werkzeug `mail_browse` mit `level`-Enum (`accounts`, `mailboxes`,
`messages`) nach dem Muster von `talk_browse`, ein `mail:<databaseId>`-Zweig in `fetch`, die
Mail-Erkennung als lazy gefülltes Feld im **bestehenden** Capabilities-Cache (kein dritter
Modul-Zustand), ein Gate mit Positiv-Allowlist der vier Pfadformen plus Nadel auf
`/message/send`, und die HTML-zu-Text-Wandlung mit dem schon deklarierten `lxml` statt einer
neuen Abhängigkeit.

---

## User Constraints

Es gibt **keine** `10-CONTEXT.md` (`has_context: false`). Die folgenden Punkte sind trotzdem
gesetzt und nicht neu zu verhandeln: sie stammen aus dem Owner-Entscheid zum Phase-8-Spike und
aus der Roadmap und wurden dem Rechercheauftrag ausdrücklich mitgegeben.

### Gesetzte Entscheidungen (Owner, Phase-8-Übergabe und Roadmap)

- `mail_browse` als Browse-Werkzeug, Volltext über das **bestehende** `fetch` mit Präfix
  `mail:<id>`. **Kein eigenes Volltext-Werkzeug.**
- Mail ist **strikt lesend**: kein Senden, kein Entwurf, kein Verschieben, kein Markieren,
  kein Löschen.
- Der SCOPE_IGNORE-Hinweis gehört in den Modul-Docstring von `clients/mail.py` (wörtliche
  Übergabe aus Plan 08-01 und aus `docs/spike-mail.md`, Abschnitt "Replaceability").
- Die Mail-Erreichbarkeit unter AppAPI-Impersonation ist bewiesen; der Schnitt der Phase
  bleibt unverändert.
- Die lethal-trifecta-Frage ist entschieden: `talk_send` liegt hinter dem Admin-Schalter
  `NC_MCP_TALK_SEND` (TALK-04). Das wird in dieser Phase nicht wieder aufgemacht, nur benannt.
- SEC-01 liegt in dieser Phase und nicht in der Release-Phase: die Phase, die die Kette
  schliesst, liefert auch ihre Benennung.

### Claude's Discretion (nicht vom Owner festgelegt, hier zu empfehlen)

- Welche Routen der Mail-App benutzt werden (intern gegen OCS): siehe Korrektur K1, hier fällt
  eine echte Entscheidung.
- Wie die HTML-zu-Text-Wandlung entsteht (eigene Abhängigkeit gegen `lxml`).
- Wie der zweite Erkennungskanal in `capabilities.py` eingehängt wird.
- Wie die Kappungsmarkierung für eine gekappte Mail heisst (die bestehenden zwei Marker sind
  beide unwahr für diesen Fall, siehe Falle 6).

### Zurückgestellt (nicht in dieser Phase)

- `prepare_context`-Bündelung inklusive Mail-Ungelesen-Zähler (CTX-02, Phase 11).
- Auflösbarkeit der Mail-Suchtreffer aus `unified_search` (TOOL-16, Phase 11).
- Neu-Verankerung des Budget-Gates auf die Endmessung (TOOL-15, Phase 11). Diese Phase braucht
  eine **Zwischenanhebung**, nicht die Endverankerung.
- Anhänge herunterladen. Die Route existiert
  (`/ocs/v2.php/apps/mail/message/{id}/attachment/{attachmentId}`, liefert Base64-Inhalt),
  ist aber weder in MAIL-01 bis MAIL-03 verlangt noch vom bestehenden Gate erlaubt: die
  Talk-Nadel `/attachment` verbietet sie schon heute.

---

## Phase Requirements

| ID | Beschreibung | Recherche-Stütze |
|----|--------------|------------------|
| MAIL-01 | Konten, Postfächer und Envelopes über `mail_browse(level=...)`, strikt lesend, `previewText` statt Body, Default 20 / Max 50, Postfächer mit `specialRole` und Ungelesen-Zähler, kein Schreibpfad im Client (Gate erweitert) | Drei deklarierte OCS-Routen (K1), Feldlisten aus `Mailbox::jsonSerialize` und `Message::jsonSerialize` (beide verifiziert), Gate-Entwurf mit Allowlist (Abschnitt "Das erweiterte Gate") |
| MAIL-02 | Einzelne Mail im Volltext über `fetch` mit `mail:<databaseId>`, HTML zu Text, Byte-Kappe markiert, Vertrauens-Signale als Datenfelder | `MessageApiResponse`-Schema plus `MessageApiController::get` (verifiziert): `isSenderTrusted`, `dkimValid`, `hasDkimSignature`, `phishingDetails`, `smime`; HTML-zu-Text mit `lxml`; Marker-Frage in Falle 6; `metadata` ist `dict[str, str]`, siehe Falle 7 |
| MAIL-03 | Filtergrammatik (`is:unread`, `from:`, `subject:`, `start:`, `tags:`) als `filter`-Parameter dokumentiert und getestet | `FilterStringParser` vollständig gelesen, Grammatiktabelle im Abschnitt "Die Filtergrammatik", inklusive der drei Regeln, die eine naive Dokumentation falsch machen (Leerzeichen, Doppelpunkt, stilles Verwerfen) |
| SRV-06 | Alle drei Familien degradieren sauber, Mail über den zweiten Erkennungskanal, gecacht wie bisher | `core/navigation/apps` live gemessen, mit und ohne aktivierte App, inklusive der Neustart-Falle; Cache-Entwurf ohne dritten Modul-Zustand |
| SEC-01 | Exfiltrationskette benannt, Admin-Schalter als Gegenmassnahme, Store-Beschreibung EN/DE/FR sagt den Mail-ist-strikt-lesend-Satz | Ablageorte und die bestehenden Textgates im Abschnitt "SEC-01: wohin der Text gehört"; kanonische Quelle der Trifecta zitiert |

---

## Projekt-Constraints (aus CLAUDE.md und den globalen Regeln)

`./CLAUDE.md` existiert und ist GSD-generiert (Projekt, Stack, Workflow). Es gibt kein
`.claude/skills/` und kein `.agents/skills/`. Die harten Vorgaben, die diese Phase berühren:

| Vorgabe | Herkunft | Wirkung auf diese Phase |
|---------|----------|--------------------------|
| Code und README auf Englisch, Projektkommunikation Deutsch | CLAUDE.md Constraints | Docstrings und Doku-Texte Englisch, dieses Dokument Deutsch |
| Keine Em-Dashes, echte Umlaute | CLAUDE.md Constraints, globale Regel | Gilt für Store-Text, README, Doku und dieses Dokument |
| Keine destruktiven Writes in v1, der MCP sieht nie mehr als der angemeldete Nutzer | CLAUDE.md Security | MAIL-01 SC4, das Gate, und die Zwei-Konten-Gegenprobe |
| Solo-Betrieb, kuratiert schlank schlägt breit | CLAUDE.md Constraints | Ein Werkzeug für drei Ebenen, kein zweites Volltext-Werkzeug |
| `uv` als Toolchain, System-Python defekt | CLAUDE.md Tech stack | Jeder Testlauf über `uv run` |
| `ruff check .` und `ruff format --check .` über das ganze Repo vor Push | globale Regel | Teil jeder Task-Abnahme |
| Python: `ruff` plus `vulture`, Whitelist nur mit Wirkung | globale Regel, Phase-08-Entscheid | Neue Namen wandern vorübergehend in `vulture_whitelist.py` und wieder heraus, sobald sie registriert sind |
| Nach API- oder Verhaltensänderung Doku-Seite und `openapi.json` nachziehen | globale Regel | Betrifft hier README-Werkzeugtabelle (Contract-Test) und `appinfo/info.xml`; das Projekt hat keine eigene openapi-Datei für MCP |
| Store-Beschreibung bei neuen Werkzeugfamilien in EN/DE/FR ergänzen, Element-Reihenfolge in `info.xml` ist schemabindend | globale Regel (NC-MCP-spezifisch) | SEC-01, plus das bestehende Textgate |
| README dreisprachig pflegen | globale Regel (NC-MCP-spezifisch) | Gilt für `appinfo/info.xml`; das README selbst ist einsprachig Englisch, die Dreisprachigkeit liegt im Manifest |
| Nach jedem Edit committen, keine Claude-Attribution | globale Regeln | Ausführungsdetail |
| Verbotenes Vokabular in öffentlichen Artefakten | globale Regel | Gilt für Store-Text und Changelog |
| Changelog-Pflege für nutzerrelevante Änderungen | globale Regel | Eine neue Werkzeugfamilie ist nutzerrelevant |

---

## Architektonische Verantwortungs-Zuordnung

| Fähigkeit | Primäre Schicht | Sekundäre Schicht | Begründung |
|-----------|-----------------|-------------------|------------|
| Mail-Konten, Postfächer, Envelopes lesen | Nextcloud Mail App (OCS-API) | `clients/mail.py` als Transport | Die App hält IMAP-Sitzung, Cache und Rechteprüfung; dieser Server ist Aufrufer, nie Mail-Client |
| Envelope-Projektion, Kappung, Cursor | `tools/mail.py` | - | Dieselbe Grenze wie bei Talk und Tables: der Client transportiert, das Werkzeug entscheidet über Form und Menge |
| Volltext einer Mail | Nextcloud Mail App (`message/{id}`) | `tools/chatgpt.py` Zweig `mail` | MAIL-02 verlangt ausdrücklich das bestehende `fetch`, nicht ein zweites Werkzeug |
| HTML zu Text | `tools/mail.py` oder ein neues Hilfsmodul | `lxml` als Parser | Die App liefert immer HTML (Korrektur K3); der Parser ist gekauft, die Absatzpolitik ist eigene Entscheidung |
| App-Erkennung Mail | `nextcloud/capabilities.py` | OCS-Kern-Route `core/navigation/apps` | Der Erkennungsweg gehört dorthin, wo die anderen drei Familien ihn schon haben, damit es einen Cache gibt und nicht zwei |
| Schreibverbot durchsetzen | `tests/contract/test_no_destructive_calls.py` | `clients/mail.py` (schreibt keinen Schreibpfad) | Ein Gate ist eine Aussage über den nächsten Commit, ein Docstring nur über diesen |
| Benennung der Exfiltrationskette | `docs/privacy.md`, README, `appinfo/info.xml` | - | Textarbeit, kein Code; die Gegenmassnahme steht schon (TALK-04) |
| Gegenmassnahme Ausgangskanal | `exapp/config_values.py` (`NC_MCP_TALK_SEND`) | - | Existiert seit Phase 9, wird hier nur zitiert |

### Systemarchitektur, Datenfluss dieser Phase

```
MCP-Client (Claude, ChatGPT, eigener Agent)
   |
   |  tools/list  ->  21 Werkzeuge, statisch, unabhaengig von installierten Apps
   |
   +--> mail_browse(level, account_id, mailbox_id, filter, limit, cursor)
   |        |
   |        v
   |   server/reg_mail.py    Literal-Enum, Feldbeschreibungen, graceful, compact
   |        |
   |        v
   |   tools/mail.py         Ebenen-Dispatch, Vorpruefung, Projektion, Kappung, Cursor
   |        |
   |        +--> capabilities.require_app(clients, "mail")
   |        |         |
   |        |         +--> [Cache-Treffer 60 s]  -> weiter
   |        |         +--> GET /ocs/v2.php/core/navigation/apps
   |        |                   |
   |        |                   +-- Eintrag id/app == "mail" fehlt -> AppMissingError
   |        |                       ("Die Mail-App ist nicht ..." + naechster Schritt)
   |        |
   |        v
   |   clients/mail.py       genau vier Pfadformen, nur GET, keine Retries
   |        |
   |        +-- level=accounts   GET /ocs/v2.php/apps/mail/account/list
   |        +-- level=mailboxes  GET /ocs/v2.php/apps/mail/ocs/mailboxes?accountId=..
   |        +-- level=messages   GET /ocs/v2.php/apps/mail/ocs/mailboxes/{id}/messages
   |                                 ?limit=..&filter=..&view=singleton[&cursor=..]
   |
   +--> fetch(id="mail:<databaseId>")
            |
            v
       tools/chatgpt.py  _fetch_mail
            |
            +--> ids.parse -> kind "mail", Ziffernwaechter
            +--> capabilities.require_app(clients, "mail")
            +--> clients/mail.py  GET /ocs/v2.php/apps/mail/message/{id}
            |         |
            |         +-- HTTP 200 -> Vollnachricht mit body
            |         +-- HTTP 206 -> Vollnachricht OHNE body (nicht entschluesselbar)
            |         +-- HTTP 404 -> gehoert diesem Konto nicht, oder Mail-App weg
            |         +-- HTTP 500 -> IMAP nicht erreichbar
            |
            +--> marks.without_marks(fremder Text)
            +--> HTML -> Text (lxml, Blockelemente werden Zeilenumbrueche)
            +--> Byte-Kappe + eigene Markierung + metadata (alles Strings)
            v
       FetchResult(id, title, text, url, metadata)
```

Die zwei Wege treffen sich nie im selben Aufruf, und das ist Absicht: `mail_browse` liefert
`previewText` und niemals einen Body, `fetch` liefert einen Body und niemals eine Liste. Eine
Ebene, die beides täte, wäre der Ort, an dem 20 Mails mit vollem HTML in eine MCP-Antwort
geraten.

### Empfohlene Projektstruktur, nur die Deltas

```
src/mcp_connector/
├── nextcloud/
│   ├── capabilities.py          # GEAENDERT: mail_available, lazy, gleicher Cache
│   └── clients/
│       └── mail.py              # NEU: vier GET-Formen, SCOPE_IGNORE-Docstring
├── tools/
│   ├── mail.py                  # NEU: browse() mit drei Ebenen, Projektionen
│   ├── html_text.py             # NEU (optional): HTML zu Text, eine Funktion
│   ├── marks.py                 # GEAENDERT: dritter Marker plus Filtermuster
│   └── chatgpt.py               # GEAENDERT: Zweig "mail" in fetch()
├── ids.py                       # GEAENDERT: encode_mail, kind "mail", Hint
└── server/
    └── reg_mail.py              # NEU: ein Werkzeug, Literal-Enum

tests/
├── unit/test_mail_client.py     # NEU
├── unit/test_mail_tools.py      # NEU
├── unit/test_html_text.py       # NEU
├── unit/test_ids.py             # GEAENDERT: Roundtrip mail
├── unit/test_chatgpt_fetch.py   # GEAENDERT: mail-Zweig
├── unit/test_ocs_capabilities.py# GEAENDERT: Navigationsweg
├── unit/test_exapp_env_setup.py # GEAENDERT: Store-Marker Mail und Trifecta
├── contract/test_tool_surface.py# GEAENDERT: 21 Werkzeuge
├── contract/test_no_destructive_calls.py # GEAENDERT: Mail-Nadeln plus Allowlist
└── integration/test_mail_read.py# NEU: Live-Lauf, braucht GreenMail

scripts/
├── check_tool_budget.py         # GEAENDERT: Zwischenanhebung mit Messzeile
├── acceptance_all_tools.py      # GEAENDERT: EXPECTED_TOOLS 21
└── bootstrap_exapp.sh           # GEAENDERT: GreenMail-Konto statt imap.invalid

docs/
├── privacy.md                   # GEAENDERT: Exfiltrationskette in "What leaves your control"
├── spike-mail.md                # GEAENDERT: Korrektur K1 nachtragen
└── faq.md                       # GEAENDERT (optional): eine Frage zu Mail
appinfo/info.xml                 # GEAENDERT: Beschreibung EN/DE/FR
README.md                        # GEAENDERT: Werkzeugtabelle, Mail-Abschnitt, Grenzen
```

---

## Standard Stack

### Kern

| Baustein | Version | Zweck | Warum genau der |
|----------|---------|-------|-----------------|
| Nextcloud Mail | 5.11.1 (installiert und gemessen) | Datenquelle | Die App der Instanz; auf beiden Topologien per Bootstrap installiert `[VERIFIED: occ app:list auf nc-mcp-exapp-nc, 2026-08-24]` |
| Deklarierte OCS-Routen der Mail-App | in `openapi.json` der App 5.11.1 | Konten, Postfächer, Nachrichten, Volltext | Kein `SCOPE_IGNORE`, im mitgelieferten Schema deklariert, live unter Impersonation gemessen (Korrektur K1) |
| `ocs.ocs_get` / `ocs.parse_ocs` | vorhanden | Transport plus Envelope | Setzt beide Pflichtheader aus D-18, kennt schon `998` und die HTML-Loginseite |
| `lxml` | `>=6.1,<7`, installiert 6.1.1 | HTML-Parser für die Volltext-Wandlung | Bereits deklarierte Abhängigkeit, echter HTML-Parser (libxml2), verträgt kaputtes Mail-HTML `[VERIFIED: uv run gegen den Arbeitsbaum, 2026-08-24]` |
| `paging` | vorhanden | Cursor-Handle | `read_offset` nimmt jede nicht negative Ganzzahl, ein `sent_at`-Zeitstempel passt hinein |
| `marks` | vorhanden, wird erweitert | Kappungsmarkierung plus Filter gegen gefälschte Marker | ME-03 gilt für Mail stärker als für alles andere: fremder Text von aussen |
| `capabilities` | vorhanden, wird erweitert | App-Erkennung mit Cache | Ein Cache, ein TTL, ein erlaubter Modulzustand |

### Alternativen, geprüft und verworfen

| Statt | Möglich wäre | Abwägung |
|-------|--------------|----------|
| Deklarierte OCS-Routen | Die internen `/apps/mail/api/...`-Routen aus dem Spike | Sie tragen `#[OpenAPI(scope: SCOPE_IGNORE)]`, dürfen ohne Ankündigung verschwinden, und ihre Pfade kollidieren mit Schreibrouten: `'messages' => ['url' => '/api/messages']` ist eine Resource-Route, also POST create, PUT update und DELETE destroy auf demselben Pfad `[VERIFIED: appinfo/routes.php 5.11.1]`. Das Gate müsste dann verb-basiert werden statt pfad-basiert. Nur nehmen, wenn eine deklarierte Route ein Feld nicht liefert, das MAIL-01 wörtlich verlangt |
| `lxml` für HTML zu Text | `html2text`, `beautifulsoup4`, `inscriptis`, `markdownify` | Alle vier wären eine neue Laufzeit-Abhängigkeit mit eigenem Audit (`docs/dependency-audit.md`), für einen Anteil, den `lxml` schon kann. Der schwierige Teil ist das Parsen von kaputtem Mail-HTML, und den kauft `lxml` ein; die Absatzpolitik ist in jeder dieser Bibliotheken anders und in keiner richtig |
| `lxml` | `html.parser` aus der Standardbibliothek | Funktioniert, aber ein toleranter HTML-Parser ist genau die Sorte Rad, die man nicht selbst dreht. `lxml` ist schon da, also kostet es nichts |
| Mail-Erkennung über `core/navigation/apps` | Erkennung über die Suchprovider-Liste (`/ocs/v2.php/search/providers`, enthält `mail` genau dann, wenn die App aktiv ist) | Gemessen funktioniert beides. Die Navigation ist die kleinere Antwort und heisst wörtlich so wie das, was gefragt ist; die Providerliste wird von `unified_search` ohnehin bei jedem Aufruf frisch gelesen und ist damit ein zweiter Ort mit demselben Wissen. Die Providerliste bleibt die Gegenprobe im Test |
| Mail-Erkennung | `occ app:list` oder die Provisioning-API | `occ` ist im ExApp-Container nicht vorhanden, die Provisioning-API-App-Liste ist Admin-Recht; beide brechen den Berechtigungs-Durchgriff |
| `view=singleton` | Der App-Default `threaded` | Die Anforderung spricht von Envelopes, nicht von Threads. Der Controller wählt `threaded`, sobald `view` nicht `singleton` ist `[VERIFIED: MailboxesApiController::listMessages]`; ein Thread-Root ist etwas anderes als eine Nachricht, und die Vermischung wäre in der Antwort nicht sichtbar |

**Installation:** keine. Diese Phase installiert **kein** neues Paket. `lxml` steht seit Phase 1
in `pyproject.toml` (`lxml>=6.1,<7`) und ist im Lock.

---

## Package Legitimacy Audit

Diese Phase installiert keine externen Pakete, daher ist die Legitimitätsprüfung
gegenstandslos und `slopcheck` wurde nicht aufgerufen.

| Paket | Registry | Status | Disposition |
|-------|----------|--------|-------------|
| `lxml` | PyPI | bereits deklariert (`lxml>=6.1,<7`), installiert 6.1.1, in `docs/dependency-audit.md` geführt | Kein Neuzugang, keine Prüfung nötig |

**Wegen slopcheck entfernte Pakete:** keine.
**Als verdächtig markierte Pakete:** keine.

Sollte die Planung sich gegen `lxml` und für eine HTML-zu-Text-Bibliothek entscheiden, ist der
Package-Legitimacy-Gate **vor** dem Install nachzuholen, plus ein Eintrag in
`docs/dependency-audit.md`. Der Punkt ist bewusst hier festgehalten, damit die Abweichung nicht
unbemerkt bleibt.

---

## Korrekturen an der Übergabe aus Phase 8 und an der Roadmap

Sieben Korrekturen. Die erste ist die wichtigste des Dokuments.

### K1: Mail hat deklarierte OCS-Routen für alle drei Leseebenen, nicht nur für den Volltext

`docs/spike-mail.md` und die Roadmap gehen davon aus, dass die drei Listen-Wege nur als
`SCOPE_IGNORE`-Interna existieren und dass die einzige deklarierte Route der Volltext ist. Das
ist für die gemessenen `/apps/mail/api/...`-Pfade richtig und für die Familie insgesamt falsch.

Die mit Mail 5.11.1 ausgelieferte `openapi.json` (80 KB, im App-Verzeichnis der laufenden
Instanz) deklariert genau sieben Routen `[VERIFIED: /var/www/html/custom_apps/mail/openapi.json, Mail 5.11.1]`:

| Verb | Pfad | operationId | Für uns |
|------|------|-------------|---------|
| GET | `/ocs/v2.php/apps/mail/account/list` | `account_api-list` | Ebene `accounts` |
| GET | `/ocs/v2.php/apps/mail/ocs/mailboxes` | `mailboxes_api-list` | Ebene `mailboxes` |
| GET | `/ocs/v2.php/apps/mail/ocs/mailboxes/{mailboxId}/messages` | `mailboxes_api-list-messages` | Ebene `messages`, inklusive `filter` und `cursor` |
| GET | `/ocs/v2.php/apps/mail/message/{id}` | `message_api-get` | `fetch`-Zweig `mail:` |
| GET | `/ocs/v2.php/apps/mail/message/{id}/raw` | `message_api-get-raw` | nicht benutzt |
| GET | `/ocs/v2.php/apps/mail/message/{id}/attachment/{attachmentId}` | `message_api-get-attachment` | nicht benutzt, vom Gate verboten |
| POST | `/ocs/v2.php/apps/mail/message/send` | `message_api-send` | **die Route, gegen die das Gate die Gegenprobe braucht** |

Alle vier Leseformen sind am 2026-08-24 unter reiner AppAPI-Impersonation gegen Nextcloud
34.0.3 und Mail 5.11.1 gemessen `[VERIFIED: Live-Messung, Protokoll unten]`. Die drei
Controller tragen `#[NoAdminRequired]` und `#[NoCSRFRequired]`
`[VERIFIED: MailboxesApiController.php, MessageApiController.php]`, was die
CSRF-Frage des Spikes für diese Routen gegenstandslos macht.

**Folge für die Planung:** Der Client baut nur diese vier Formen. Die Übergabe "der
SCOPE_IGNORE-Hinweis gehört in den Modul-Docstring" bleibt trotzdem gültig und wird sogar
stärker: der Docstring hält fest, dass es einen zweiten, internen Routensatz gibt, warum er
nicht benutzt wird, und dass ein Rückfall auf ihn eine Verschlechterung wäre. Der Hinweis
wandert damit von "unser Rückgrat ist unsicher" zu "die unsichere Variante ist bewusst nicht
genommen". `docs/spike-mail.md` ist entsprechend zu korrigieren, denn das Dokument wird sonst
als Beleg für eine falsche Prämisse zitiert.

### K2: Der `body` einer Mail ist immer HTML, auch bei einer reinen Textmail

`getFullMessage` setzt `body` bei einer HTML-Mail auf `getHtmlBody()` (HTMLPurifier). Bei einer
reinen Textmail läuft der Text **trotzdem** durch `Html::convertLinks`, und diese Methode ruft
`UrlLinker::linkUrlsAndEscapeHtml` plus `HTMLPurifier::purify`
`[VERIFIED: lib/Model/IMAPMessage.php und lib/Service/Html.php, Mail 5.11.1]`. Der Text ist
danach HTML-escaped und trägt `<a href="...">`-Elemente.

**Folge:** Die HTML-zu-Text-Wandlung ist **unbedingt**, nicht abhängig von `hasHtmlBody`. Eine
Implementierung, die nur bei `hasHtmlBody: true` wandelt, liefert bei jeder Textmail
`Gr&uuml;&szlig;e` an das Modell.

### K3: Ein `limit` ohne Wert bedeutet eine Nachricht, nicht alle

Die OpenAPI-Beschreibung sagt "can be left empty to get all messages". Der Code sagt
`$limit = min(100, max(1, $limit));` `[VERIFIED: MailboxesApiController::listMessages]`, und
`max(1, null)` ist in PHP 8 gleich 1. Ohne `limit` kommt genau eine Nachricht. Das steht als
Korrektur K6 schon im Spike-Test für die interne Route und gilt für die OCS-Route wörtlich
gleich. Serverseitige Obergrenze ist 100, unsere ist 50.

### K4: `start:` und `end:` erwarten Unix-Sekunden, kein ISO-Datum

`SearchQuery::setStart` nimmt einen String, und der wird in `MessageMapper` gegen die
Spalte `m.sent_at` verglichen, einen Integer-Zeitstempel
`[VERIFIED: lib/Db/MessageMapper.php Zeilen 939 und 1096, Mail 5.11.1]`. Ein `start:2026-08-01`
filtert damit auf "Zeitstempel grösser gleich 2026" und liefert praktisch alles. Zusätzlich
zerlegt der Filterparser den Token am ersten Doppelpunkt und wirft den Rest weg, also wäre
`start:2026-08-01T10:00:00Z` ohnehin auf `2026-08-01T10` verkürzt. Die Dokumentation von
MAIL-03 muss Unix-Sekunden sagen, und das Werkzeug sollte einen ISO-Wert **ablehnen** statt ihn
weiterzugeben (ein stiller Filter, der nichts filtert, ist die schlechtere Antwort).

### K5: Die Brute-Force-Sorge aus Phase 8 ist in Mail 5.11.1 wirkungslos

`MessageApiController::get` trägt `#[BruteForceProtection('mailGetMessage')]`, aber im ganzen
`lib/`-Baum der App gibt es keinen einzigen `throttle()`-Aufruf
`[VERIFIED: grep über /var/www/html/custom_apps/mail/lib, 0 Treffer]`. Ohne diesen Aufruf
registriert die Middleware keinen Versuch, der Zähler bleibt leer und die Verzögerung ist null.

**Folge:** Das Memo-Muster aus dem Spike (genau ein Request pro Lauf) muss nicht in
Produktionscode wandern, um einen Zähler zu schonen, der nicht zählt. Die Regel "kein Loop über
`message/{id}`" bleibt trotzdem richtig, aber aus einem anderen Grund: jeder dieser Aufrufe
öffnet eine IMAP-Sitzung (`clientFactory->getClient`, `logout` im `finally`), also ist er teuer,
nicht gefährlich. Und der Ziffernwächter auf der Id bleibt richtig, weil ein Modellwert sonst
direkt in einen URL-Pfad geht (T-01-63-Muster).

### K6: Der 500er der Postfachliste ist der Normalfall eines unerreichbaren Mailservers

Die Roadmap sieht "bei 404 oder HTML degradiert antworten" vor. Gemessen ist der häufigste
Fehlerfall ein anderer: `GET /apps/mail/ocs/mailboxes?accountId=1` antwortet HTTP 500 mit
`ocs.meta.statuscode` 996 und `message: "Internal Server Error\n"`, wenn der IMAP-Server nicht
erreichbar ist `[VERIFIED: Live-Messung 2026-08-24]`. `ocs._check_transport` fängt jeden Status
ab 500 vor dem Envelope ab und antwortet "Nextcloud reported a server error (500) ... This is a
problem on the Nextcloud side" `[VERIFIED: src/mcp_connector/nextcloud/clients/ocs.py]`. Für
Mail ist das der falsche nächste Schritt: die häufigste Ursache ist ein falsches
IMAP-Passwort oder ein nicht erreichbarer Mailserver **des Nutzers**, und der nächste Schritt
heisst "das Konto in der Mail-App prüfen", nicht "das Nextcloud-Log lesen". Dieser 500er
gehört im Mail-Client abgefangen, nach dem Vorbild der 304 in Phase 9 (dort im Talk-Client,
weil 304 nur auf dieser einen Route eine Bedeutung hat).

Zusätzlich: `MailSearch::findMessages` wirft `MailboxNotCachedException`, wenn das Postfach noch
nie synchronisiert wurde `[VERIFIED: lib/Service/Search/MailSearch.php]`, und `listMessages`
trägt kein `#[TrapError]`, also wird auch das ein 500er. Derselbe Satz, dieselbe Stelle.

### K7: Der Volltext-Status 206 ist kein Fehler

`MessageApiController::get` antwortet HTTP 206 (`STATUS_PARTIAL_CONTENT`), wenn die Nachricht
nicht entschlüsselt werden konnte; die Antwort ist dann vollständig **ausser** `body`
`[VERIFIED: MessageApiController::get]`. `ocs._OK_STATUS` ist
`frozenset({100, 200, 201})`, also würde `parse_ocs` daraus einen Fehler machen
`[VERIFIED: ocs.py Zeile 57]`. 206 gehört im Mail-Client behandelt, nicht global in
`_OK_STATUS`: global wäre 206 für jede andere Familie eine stillschweigende Erweiterung, und
in Phase 9 wurde die 304 aus demselben Grund lokal gehalten.

---

## Die Mail-API-Referenz (verifiziert gegen Mail 5.11.1)

### Das Live-Protokoll dieser Recherche

Gemessen am 2026-08-24 gegen die laufende HaRP-Topologie: Nextcloud 34.0.3 (Build 34.0.3.2),
AppAPI 34.0.0, Mail 5.11.1, `spreed` 24.0.4, `tables` 2.2.2. Credential war ausschliesslich
`APP_SECRET` plus `AUTHORIZATION-APP-API` (Modus `appapi`), kein App-Passwort im Prozess. Es
wurden nur Statuscodes, Content-Types und **Feldnamen** protokolliert, nie Feldwerte: die
Kontoantwort trägt eine echte Mailadresse (T-08-01).

| Weg | Status | Content-Type | Form |
|-----|--------|--------------|------|
| `GET /ocs/v2.php/cloud/capabilities` | 200 | json | Abschnitte: `activity, app_api, bruteforce, circles, core, dav, deck, downloadlimit, files, files_sharing, notes, notifications, ocm, password_policy, provisioning_api, recommendations, spreed, systemtags, theming, user_status, weather_status`. **Kein `mail`** |
| `GET /ocs/v2.php/core/navigation/apps` | 200 | json | Liste mit `id, app, type, name, order, href, icon, active, default, classes, unread`; enthält `mail` |
| `GET /ocs/v2.php/apps/mail/account/list` | 200 | json | `[{aliases: [], email: str, id: int, isDelegated: bool}]` |
| `GET /ocs/v2.php/apps/mail/ocs/mailboxes?accountId=1` | 500 | json | `meta.statuscode` 996, `message` "Internal Server Error\n" (IMAP zeigt auf `imap.invalid`) |
| `GET /ocs/v2.php/apps/mail/ocs/mailboxes/1/messages?limit=5` | 403 | json | leere Daten (Postfach 1 existiert nicht) |
| dieselbe Route mit `filter=is:unread` | 403 | json | identisch, der Filter ändert am Routing nichts |
| `GET /ocs/v2.php/search/providers` | 200 | json | Provider-Ids enthalten `mail` |
| `GET /ocs/v2.php/apps/mail/message/999999` (Konto bob) | 404 | json | `ocs.data` ist der **String** `"Account not found."`, `meta.message` ist leer |
| `GET /ocs/v2.php/apps/mail/message/notanumber` | 404 | json | identisch; PHP castet auf 0, es gibt keinen Routing-Fehler |
| `GET /ocs/v2.php/apps/mail/account/list` (Konto bob, kein Mail-Konto) | 200 | json | `data` ist `[]` |

Und der Erkennungsteil, der SRV-06 beantwortet, in drei Zuständen:

| Zustand | `navigation/apps` enthält `mail` | `search/providers` enthält `mail` | `account/list` |
|---------|--------------------------------|-----------------------------------|----------------|
| App aktiviert | ja | ja | 200 |
| `occ app:disable mail`, **ohne** Neustart | **ja** (falsch positiv) | **ja** (falsch positiv) | **200** (die Route antwortet weiter) |
| `occ app:disable mail`, **nach** Neustart | nein | nein | 404, `meta.statuscode` 998, JSON-Envelope |
| nach `occ app:enable mail` und Neustart | ja | ja | 200 |

Der Zustand in der Mitte ist derselbe Effekt, den Phase 1 für die Capabilities festgehalten
hat, und er ist die wichtigste Falle des SRV-06-Nachweises. Die Instanz wurde nach der Messung
wieder in den Ausgangszustand gebracht (Mail aktiviert, Neustart, Nachmessung grün).

### Ebene `accounts`

`GET /ocs/v2.php/apps/mail/account/list`, keine Parameter.

`AccountListResponse` (deklariert und gemessen): `id` (int), `email` (str), `isDelegated`
(bool), `aliases` (Liste mit `id`, `email`, `name`). Das ist alles, insbesondere **kein**
`name` des Kontos und **kein** IMAP-Host. Für die Antwort dieses Servers ist das genau richtig:
Hostnamen sind Infrastruktur des Nutzers und gehören nicht in einen Modellkontext.

Ein Konto ohne jedes Mail-Konto antwortet 200 mit `[]` und nicht mit einem Fehler
`[VERIFIED: Live-Messung mit bob]`. Der Unterschied zu "die Mail-App fehlt" muss in der
Antwort sichtbar sein, siehe Muster 3.

### Ebene `mailboxes`

`GET /ocs/v2.php/apps/mail/ocs/mailboxes?accountId=<int>`, `accountId` ist Pflicht.

Der Controller gibt `MailManager::getMailboxes($account)` unverändert zurück; das Schema sagt
nur `object`, die Felder stehen also in `Mailbox::jsonSerialize`
`[VERIFIED: lib/Db/Mailbox.php, Mail 5.11.1]`:

| Feld | Typ | Für MAIL-01 |
|------|-----|-------------|
| `databaseId` | int | die Id, mit der die Nachrichtenebene aufgerufen wird |
| `name` | str | IMAP-Name, mit Trennzeichen, zum Beispiel `INBOX.Archive` |
| `displayName` | str | in 5.11.1 identisch mit `name` |
| `specialRole` | int oder str | **wörtlich von MAIL-01 verlangt**; entsteht aus `getSpecialUseParsed()[0] ?? 0`, also der erste Special-Use-Eintrag oder die Zahl 0 |
| `specialUse` | Liste | die vollständige Liste, aus der `specialRole` das erste Element nimmt |
| `unread` | int | **der Ungelesen-Zähler aus MAIL-01** (`$this->unseen`) |
| `delimiter` | str | IMAP-Trennzeichen, nötig, um `name` als Pfad zu lesen |
| `attributes` | Liste | IMAP-Attribute |
| `myAcls`, `shared` | - | Freigabezustand eines geteilten Postfachs |
| `syncInBackground`, `cacheBuster`, `mailboxes` | - | Interna des Frontends, gehören nicht in die Antwort |
| `id` | str | base64 des Namens, ein Frontend-Detail. Nicht verwechseln mit `databaseId` |

Die Verwechslung von `id` und `databaseId` ist die teuerste in dieser Familie: `id` ist
base64, `databaseId` ist die Zahl, die jede andere Route erwartet.

`specialRole` ist der Grund, warum ein Modell die Inbox findet, ohne Namen zu raten. Der Wert
ist der IMAP-Special-Use in Kleinschreibung ohne Backslash (`inbox`, `sent`, `drafts`,
`trash`, `junk`, `archive`, `flagged`) oder die Zahl 0, wenn keiner gesetzt ist
`[ASSUMED: die Wertemenge stammt aus Horde_Imap_Client::SPECIALUSE_*, gegen echte IMAP-Daten nicht gemessen]`.

### Ebene `messages`

`GET /ocs/v2.php/apps/mail/ocs/mailboxes/{mailboxId}/messages`

| Parameter | Typ | Verhalten |
|-----------|-----|-----------|
| `mailboxId` | int, Pfad | `databaseId` des Postfachs |
| `limit` | int, optional | `min(100, max(1, limit))`, ein fehlender Wert ergibt **1** (K3). Immer explizit senden |
| `cursor` | int, optional | `sent_at <` (strikt kleiner), also der `dateInt` der ältesten Nachricht der laufenden Seite `[VERIFIED: MessageMapper Zeile 963 bis 971]` |
| `filter` | str, optional | die Grammatik unten; leerer String wird zu `null` |
| `view` | str, optional | `singleton` oder alles andere, das dann `threaded` bedeutet. **Immer `singleton` senden** |
| `OCS-APIRequest` | header, Pflicht | setzt `ocs.ocs_get` schon |

Sortierung ist fest `ORDER_NEWEST_FIRST`, ein Sortierparameter existiert nicht. Zwei Filter
setzt der Server selbst, unabhängig vom `filter`-Parameter: in einem Flagged-Postfach nur
markierte Nachrichten, und ausserhalb des Papierkorbs keine gelöschten
`[VERIFIED: MailSearch::findMessages]`.

Die Elemente sind `Message`-Entities, Felder aus `Message::jsonSerialize`
`[VERIFIED: lib/Db/Message.php, Mail 5.11.1]`:

| Feld | Für die Antwort dieses Servers |
|------|-------------------------------|
| `databaseId` | **die Id für `fetch("mail:<databaseId>")`** |
| `subject` | Titel |
| `previewText` | **wörtlich von MAIL-01 verlangt**, statt des Bodys. Kann `null` sein |
| `dateInt` | Unix-Sekunden, gleichzeitig der Wert für den nächsten `cursor` |
| `flags` | Objekt mit `seen`, `flagged`, `answered`, `deleted`, `draft`, `forwarded`, `hasAttachments`, `important`, `$junk`, `$notjunk`, `$mdnsent`. Achtung: drei Schlüssel beginnen mit `$` |
| `from`, `to`, `cc`, `bcc` | Listen mit `label` und `email` |
| `tags` | Objekt, Schlüssel ist das IMAP-Label |
| `mailboxId` | zur Rückbindung |
| `threadRootId`, `inReplyTo`, `references`, `messageId` | Threading; für eine Envelope-Liste Ballast |
| `summary`, `mentionsMe`, `encrypted`, `imipMessage` | Zusatzsignale, `summary` kann KI-erzeugt sein |
| `avatar`, `fetchAvatarFromClient`, `remoteId`, `uid`, `attachments` | für ein Modell wertlos oder gefährlich gross |

Die Feldauswahl ist eine echte Entscheidung, weil `flags` allein elf Booleans hat. Empfehlung
für die Projektion: `id` (als `mail:<databaseId>`), `subject`, `from` (nur der erste Eintrag,
als `label <email>`), `date` (ISO aus `dateInt`), `preview` (aus `previewText`, gekappt),
`unread` (`not flags.seen`), und `has_attachments` nur wenn wahr. Alles andere weglassen; das
Budget dieser Antwort ist der Kontext des Nutzers.

### Volltext: `GET /ocs/v2.php/apps/mail/message/{id}`

`id` ist die `databaseId`, `MessageApiResponse` ist deklariert und setzt sich aus
`IMAPFullMessage` plus fünf Feldern zusammen `[VERIFIED: openapi.json plus MessageApiController::get]`.

Die Felder, die MAIL-02 wörtlich verlangt:

| Feld | Typ | Bedeutung |
|------|-----|-----------|
| `isSenderTrusted` | bool | der Nutzer hat diesen Absender in der Mail-App als vertrauenswürdig markiert |
| `hasDkimSignature` | bool | eine DKIM-Signatur ist vorhanden |
| `dkimValid` | bool, **optional** | nur vorhanden, wenn ein gecachtes Prüfergebnis existiert (`dkimService->getCached`). Fehlt es, ist das "nicht geprüft" und nicht "ungültig" |
| `phishingDetails` | Objekt | `warning` (bool) plus `checks` (Liste mit `type`, `isPhishing`, `message`, `additionalData`) |
| `smime` | Objekt | `isSigned`, `signatureIsValid` (nullable), `isEncrypted` |

Weitere Felder mit Substanz: `body` (siehe K2), `hasHtmlBody`, `subject`, `from`/`to`/`cc`/`bcc`/`replyTo`,
`dateInt`, `flags`, `signature` (nur bei Textmails abgetrennt), `itineraries` (nur bei
gecachtem Ergebnis), `attachments` und `inlineAttachments` (Metadaten plus `downloadUrl`),
`unsubscribeUrl`, `isOneClickUnsubscribe`, `scheduling`, `rawUrl`, `dispositionNotificationTo`,
`messageId`, `uid`, `id`.

Drei Eigenschaften dieser Route, die den Unterschied machen:

1. **Lesen setzt kein `\Seen`.** Jeder IMAP-Fetch der App läuft mit `'peek' => true`
   `[VERIFIED: lib/IMAP/ImapMessageFetcher.php Zeilen 128, 183, 227, 475, 478; lib/IMAP/MessageMapper.php mehrfach]`.
   Das ist die Mail-Entsprechung der Talk-Lesemarker-Falle, und die App hat sie bereits gelöst.
   Trotzdem ist es eine Eigenschaft der Fassung und nicht des Protokolls, also gehört sie in
   den Live-Nachweis (Flag vorher und nachher vergleichen, das Talk-Muster aus 09-05).
2. **`itineraries` und `dkimValid` kommen nur aus dem Cache.** Beide Dienste heissen `getCached`,
   berechnen also nichts nach `[VERIFIED: MessageApiController::get]`. Ein fehlendes Feld ist
   kein Fehler.
3. **Der Fehlertext lebt in `ocs.data`, nicht in `meta.message`.** Gemessen: `data` ist der
   String `"Account not found."`, `meta.message` ist leer. `ocs._status_error` liest
   `meta.message`, also geht die Erklärung der App verloren. Für Mail ist das kein Verlust,
   sondern ein Gewinn: `"Account not found."` für eine fremde Nachrichten-Id gibt deren
   Existenz nicht preis, genau wie der 404 von Tables. Der eigene Satz ist besser als der
   durchgereichte.

### Die Filtergrammatik (MAIL-03)

Vollständig aus `FilterStringParser::parse` und `parseFilterToken` gelesen
`[VERIFIED: lib/Service/Search/FilterStringParser.php, Mail 5.11.1]`.

**Die drei Regeln, die jede naive Dokumentation falsch machen:**

1. Der Filter wird an **Leerzeichen** in Tokens zerlegt. Ein Wert mit Leerzeichen ist damit
   unmöglich, ausser er ist URL-kodiert: der Parser ruft `urldecode` auf den Wert, also ist
   `subject:Rechnung%20Mai` der einzige Weg, und `subject:Rechnung Mai` filtert auf
   `subject:Rechnung` und verwirft `Mai` stillschweigend.
2. Ein Token wird am **ersten** Doppelpunkt zerlegt, und alles nach dem zweiten Teil fällt weg
   (`[$type, $encodedParam] = explode(':', $token)`). Ein Doppelpunkt im Wert muss `%3A` sein.
3. Ein Token ohne Doppelpunkt und ein unbekannter Typ werden **stillschweigend verworfen**, der
   Parser gibt `false` zurück und niemand liest es. Ein Tippfehler liefert also die
   **ungefilterte** Liste, nicht einen Fehler. Das ist der stärkste Grund, den Filter im
   Werkzeug **vorher** zu validieren.

| Token | Wirkung | In MAIL-03 |
|-------|---------|------------|
| `is:unread` / `not:unread` | `\Seen` nicht gesetzt, bzw. invertiert | **ja** |
| `is:read`, `is:answered`, `is:starred`, `is:important` | die entsprechenden Flags | Zugabe |
| `is:is_important`, `is:pi-important`, `is:pi-other` | Sonderformen der Wichtigkeits-Klassifikation | nicht dokumentieren |
| `from:<wert>` | Absender enthält | **ja** |
| `to:`, `cc:`, `bcc:` | Empfängerfelder | Zugabe |
| `subject:<wert>` | Betreff enthält | **ja** |
| `body:<wert>` | **löst eine IMAP-Suche aus** statt einer Datenbankabfrage `[VERIFIED: MailSearch::getIdsLocally]` | **nicht** aufnehmen: eine Netzrunde zum Mailserver pro Aufruf |
| `tags:<label1,label2>` | IMAP-Labels, komma-getrennt | **ja** |
| `start:<unix-sekunden>` | `sent_at >=` | **ja**, mit K4 |
| `end:<unix-sekunden>` | `sent_at <=` | Zugabe, gehört wegen der Symmetrie dazu |
| `match:<wert>` | freier Treffer | undokumentiert lassen |
| `mentions:true` | erwähnt mich, nur bei exakt `true` | Zugabe |
| `flags:<a,b>` | mehrere Flags auf einmal, plus der Sonderwert `attachments` | undokumentiert lassen, `is:` deckt es ab |

**Empfehlung für die Werkzeug-Ebene:** Den `filter`-Parameter durchreichen, aber vorher gegen
eine Positivliste der dokumentierten Typen prüfen und einen unbekannten Typ mit einem Satz
ablehnen, der die erlaubten nennt. Der Grund ist Regel 3: die stille Verwerfung erzeugt eine
Antwort, die richtig aussieht und falsch ist, und das ist der Fehlerfall, den das Modell nicht
erkennen kann. Dasselbe Prinzip trägt schon `paging.check_scope`.

---

## Der zweite Erkennungskanal (SRV-06)

### Was steht, was fehlt

Steht: `capabilities.py` mit `Capabilities`-Dataclass, `_cache` (60 s, Schlüssel
`(base_url, user)`, ein von zwei erlaubten Modulzuständen), `require_app`, `app_missing` und
`_MISSING` mit vier Einträgen (`notes`, `deck`, `tables`, `spreed`). `has()` wirft für einen
unbekannten Namen einen `ValueError` `[VERIFIED: src/mcp_connector/nextcloud/capabilities.py]`.
Talk und Tables sind damit für SRV-06 fertig; der Nachweis ist eine Messung, keine Änderung.

Fehlt: Mail. Und Mail passt nicht in `parse()`, weil es keinen Capabilities-Abschnitt gibt.

### Die Entscheidung: wie der Navigationsweg in den bestehenden Cache kommt

`test_no_destructive_calls.py` hält `ALLOWED_MODULE_STATE` bei genau zwei Einträgen
(`http._clients` und `capabilities._cache`). Ein dritter Cache für die Navigation wäre eine
Erweiterung dieser Liste, also eine Aufweichung von D-20. Drei Wege:

**Weg A, empfohlen: ein lazy gefülltes Feld in derselben Cache-Zeile.**
`Capabilities` bekommt `mail_available: bool | None = None`, `None` bedeutet "noch nicht
gefragt". `require_app(clients, "mail")` ruft `load()`, sieht `None`, holt
`GET /ocs/v2.php/core/navigation/apps`, baut mit `dataclasses.replace` eine neue
`Capabilities` und schreibt sie unter demselben Schlüssel und mit dem **ursprünglichen**
Zeitstempel zurück. Kosten: ein zusätzlicher Request pro Cache-Fenster, und nur für Nutzer,
die Mail-Werkzeuge benutzen. `ALLOWED_MODULE_STATE` bleibt bei zwei. Die Dataclass ist
`frozen=True, slots=True`, `replace` funktioniert damit.

**Weg B: `load()` holt immer beides.** Einfacher zu lesen, aber jeder Deck-, Notes-, Talk- und
Tables-Aufruf zahlt einen zweiten Request für eine Auskunft, die er nicht braucht. Bei einem
Werkzeug-Burst ist das messbar.

**Weg C: eigene Funktion mit eigenem Cache.** Verletzt D-20 beziehungsweise verlangt einen
dritten Eintrag in `ALLOWED_MODULE_STATE`. Nicht nehmen.

Ausserdem nötig:
- `has()` bekommt `"mail"`, gemappt auf `bool(self.mail_available)`. Wichtig: `None` wie
  `False` behandeln wäre falsch, denn `require_app` ruft ja vorher den Nachfüllpfad. Der
  `ValueError`-Zweig für unbekannte Namen bleibt.
- `_MISSING` bekommt `"mail"`. Vorschlag für den Wortlaut, im Stil der vier bestehenden:
  Meldung `"The Mail app is not available on this Nextcloud."`, Hinweis
  `"Ask an administrator to enable the Mail app for this account."`
- Der Weg heisst in der Antwort nirgends "Navigation". Das ist ein Implementierungsdetail; die
  Meldung sagt, was fehlt und was zu tun ist.

### Die Erkennungsregel

Ein Eintrag zählt, wenn `entry.get("app") == "mail"` oder `entry.get("id") == "mail"`. Beide
Felder tragen in 5.11.1 den Wert `mail` `[VERIFIED: Live-Messung]`; eine App mit mehreren
Navigationseinträgen kann abweichende `id`s haben, deshalb die Oder-Verknüpfung. Kein Filter
auf `type`: gemessen ist `type: "link"` für alle Einträge, und ein Filter darauf wäre eine
Annahme über eine Antwortform, die keinen Gewinn bringt.

Eine leere Liste ist ein Fehler und nicht "Mail fehlt": jede Instanz hat Navigation. Ein
Nicht-Listen-Ergebnis ebenso. Das Muster steht in `unified_search` schon so ("null Provider ist
ein Fehler mit Ausweg, weil eine leere Trefferliste dort eine Lüge wäre").

### Was der SRV-06-Nachweis messen muss

Sechs Zeilen, drei Familien mal zwei Zustände, plus die Neustart-Falle:

| Familie | Weg | Fehlt-Nachweis |
|---------|-----|----------------|
| Talk | `spreed`-Abschnitt der Capabilities | `occ app:disable spreed` **plus Neustart**, dann `talk_browse` |
| Tables | `tables.enabled` | `occ app:disable tables` **plus Neustart**, dann `tables_browse` |
| Mail | `navigation/apps` | `occ app:disable mail` **plus Neustart**, dann `mail_browse` und `fetch("mail:1")` |

Der Neustart ist Pflicht, sonst ist der Test grün, ohne etwas zu belegen: gemessen antwortet
eine abgeschaltete Mail-App ohne Neustart weiter mit 200. Der Phase-1-Befund
("eine per occ deaktivierte App bleibt sichtbar, bis die Nextcloud neu startet") gilt
für die Navigation genauso wie für die Capabilities, und diese Recherche hat es für die
Navigation eigens gemessen.

Und in jeder der sechs Zeilen gehört behauptet, was **nicht** passiert: kein Stacktrace, kein
`<`-Zeichen am Anfang des Körpers, keine `/login`-Weiterleitung. Der Fehlersatz muss den
nächsten Schritt tragen. Ohne Vorprüfung wäre die Antwort für Mail übrigens nicht katastrophal
aber falsch: `statuscode` 998 landet in `_status_error` im 404-Zweig, und der schickt das
Modell zu "search for it first", also zum Suchen einer Nachricht in einer App, die es nicht
gibt.

---

## Das erweiterte Gate (MAIL-01 SC4)

### Wie das bestehende Gate arbeitet

`tests/contract/test_no_destructive_calls.py` parst jede Produktionsdatei, blendet Kommentare
und Docstrings per AST und `tokenize` aus, behält String-Literale, und sucht in den
verbleibenden Zeilen nach 22 Nadeln. Vier davon sind HTTP-Verben (`DELETE`, `MOVE`, `COPY`,
`PROPPATCH`), die übrigen benennen Pfadsegmente, weil `PUT` und `POST` in diesem Projekt
erlaubt sind. Jede Pfad-Nadel hat eine Gegenprobe-Zeile (`TABLES_ROUTES`, `TALK_ROUTES`), und
für Talk steht zusätzlich eine Positivliste `ALLOWED_TALK_ROUTES` mit den genau drei Formen,
die der Client baut `[VERIFIED: die Datei, gelesen 2026-08-24]`.

### Warum Mail die Positivliste braucht und nicht nur Nadeln

Die Schreibrouten der Mail-App sind 59 an der Zahl, und die meisten liegen unter
`/api/...`-Pfaden, die dieser Server nie baut. Aber zwei Kollisionen machen eine reine
Nadelliste unbrauchbar:

1. `'messages' => ['url' => '/api/messages']` ist eine Resource-Route
   `[VERIFIED: appinfo/routes.php 5.11.1]`. POST auf denselben Pfad legt an, PUT ändert, DELETE
   löscht. Eine Nadel auf `/api/messages` verbietet damit auch das Lesen, was hier sogar
   gewünscht ist, aber eine Nadel kann nicht zwischen den Verben unterscheiden.
2. Die einzige deklarierte Schreibroute, `POST /ocs/v2.php/apps/mail/message/send`, liegt
   direkt neben der Leseroute `GET /ocs/v2.php/apps/mail/message/{id}`. Das Segment `/message/`
   trägt beide. Nur `send` unterscheidet sie.

Der Vorschlag, im Stil der Talk-Erweiterung aus Phase 9:

**Neue Nadeln in `FORBIDDEN`** (jede mit Gegenprobe-Zeile in einem neuen `MAIL_ROUTES`-Dict):

| Nadel | Begründung im Test |
|-------|--------------------|
| `/message/send` | die eine deklarierte Sende-Route der Mail-App; die Gegenprobe ist der Beweis, dass die Nadel greift, obwohl das Lesen auf `/message/` liegt |
| `/api/messages` | interne Resource-Route: POST legt einen Entwurf an, PUT ändert, DELETE löscht, und alle drei tragen denselben Pfad wie das Lesen |
| `/api/mailboxes` | interne Resource-Route plus `/sync`, `/clear`, `/read`, `/repair` |
| `/api/accounts` | interne Resource-Route plus `/draft`, `/signature` |
| `/api/drafts` | Entwürfe anlegen und verschieben |
| `/api/outbox` | die zweite Sendemöglichkeit der App, ohne das Wort "send" im Pfad |
| `/api/thread` | Thread verschieben und löschen |
| `/api/tags` | Tags anlegen, ändern, löschen |
| `/api/trustedsenders` | Absender-Vertrauen setzen und entziehen, also eine Sicherheitsentscheidung des Nutzers |

Kollisionsprüfung gegen den bestehenden Code, geprüft: die vier erlaubten Mail-Pfadformen
enthalten keine dieser Nadeln, und keine dieser Nadeln trifft eine bestehende Zeile in
`clients/tables.py`, `clients/deck.py` oder `clients/notes.py` (Tables baut
`/apps/tables/api/1/...`, Deck `/apps/deck/api/v1.0/boards`, Notes `/apps/notes/api/v1`).
Umgekehrt greift eine **bestehende** Nadel bereits in die Mail-Familie: `/attachment` verbietet
die Mail-Anhangsroute, ohne dass etwas dazu getan werden muss, und `/read` verbietet
`/api/mailboxes/{id}/read` doppelt.

**Neue Positivliste `ALLOWED_MAIL_ROUTES`** mit den genau vier Formen, die
`clients/mail.py` baut, wörtlich in der f-String-Schreibweise dieses Projekts. Das ist die
Hälfte des Beweises, die eine Nadel nicht liefern kann, und für diese Familie ist sie
wichtiger als für Talk, weil hier eine Leseroute und eine Schreibroute ein Pfadpräfix teilen.

**Die Gegenprobe, die MAIL-01 SC4 wörtlich verlangt** ("mit Gegenprobe, obwohl die Mail-App
selbst eine Sende-Route anbietet"): ein Test, der die Zeile
`await ocs.ocs_post(client, creds, "/apps/mail/message/send", body)` durch den **echten**
Prüfpfad `_violations` schickt und behauptet, dass sie gemeldet wird. Nicht eine Nachbildung
der Prüfung, sondern dieselbe Funktion, wie es die Datei für Tables und Talk schon macht.

**Zusätzlich, weil eine Nadel nur einen Pfad kennt:** ein Quelltext-Test, der behauptet, dass
`clients/mail.py` **kein** `ocs_post`, kein `client.post`, kein `client.put`, kein
`client.request` und kein `.patch(` enthält. Die Familie ist die erste ohne jeden Schreibpfad,
und "es gibt nur GETs in dieser Datei" ist eine prüfbare, wörtliche Aussage. Das Muster
existiert schon (`contacts.py` wird per Grep freigehalten von Schreibmethoden, D-07).

---

## HTML zu Text

### Es gibt heute keinen Helfer

Gesucht und nicht gefunden: im ganzen `src/`-Baum gibt es keine HTML-zu-Text-Funktion. `import
html` in `exapp/ui/layout.py` ist `html.escape` für die Zustimmungsseiten, also die
Gegenrichtung `[VERIFIED: grep über src/, 2026-08-24]`. `files.read` liefert Bytes, dekodiert,
aber wandelt nichts um. Diese Phase baut den ersten.

### Der Vorschlag, mit `lxml`

Am Arbeitsbaum gemessen `[VERIFIED: uv run python, lxml 6.1.1, 2026-08-24]`:

| Eingabe | Ergebnis von `lxml.html` |
|---------|--------------------------|
| `<p>Hallo &amp; tschüss</p><div>Zeile2<br>Zeile3</div><a href="http://x">http://x</a>` | `text_content()` gibt `'Hallo & tschüssZeile2Zeile3http://x'`: Entities aufgelöst, **aber alle Blockgrenzen weg** |
| `<p>unclosed <b>bold` | `'unclosed bold'`, kaputtes HTML wird verkraftet |
| `<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>...&xxe;` | `']>&xxe;'`: die externe Entity wird **nicht** aufgelöst, aber der Rest des internen Subsets (`]>`) landet im Text |
| Billion Laughs mit verschachtelten Entities | Länge 5, **keine Expansion** |
| `"   "` (nur Leerraum) | `lxml.etree.ParserError("Document is empty")`, also eine **Exception** |

Daraus folgen vier Anforderungen an die Funktion, und alle vier sind gemessen und nicht geraten:

1. **Leeren oder nur aus Leerraum bestehenden Input vor dem Parsen abfangen.** Eine Mail ohne
   Body ist häufig (nur Anhänge), und bei HTTP 206 fehlt `body` ganz. Ein `ParserError` im
   Volltextpfad wäre ein Absturz für einen völlig normalen Fall.
2. **`<script>` und `<style>` per `drop_tree()` entfernen, bevor Text extrahiert wird.**
   HTMLPurifier entfernt Skripte und extrahiert Style-Blöcke schon, aber diese Funktion darf
   sich nicht darauf verlassen: sie bekommt fremden Text, und die Verteidigung gehört an die
   Stelle, die den Text verarbeitet.
3. **Blockelemente werden Zeilenumbrüche.** `text_content()` allein macht aus einer Mail eine
   Wortkette. Nötig ist ein Durchlauf über `p, div, br, li, tr, h1..h6, blockquote, table` mit
   einem `\n` davor beziehungsweise dahinter, danach Zusammenfassen von mehr als zwei
   aufeinanderfolgenden Leerzeilen. Das ist die Absatzpolitik, und die ist in jeder externen
   Bibliothek anders und in keiner richtig; sie selbst zu schreiben ist keine Doppelarbeit,
   sondern die eigentliche Entscheidung.
4. **Den Parser mit `no_network=True` bauen.** `lxml.html.HTMLParser(no_network=True)`. Die
   Messung zeigt, dass ohne diese Option keine Entity aufgelöst wurde, aber die Option kostet
   nichts und die Datei bekommt fremdes HTML.

Der Docstring dieser Funktion sagt, was sie **nicht** ist: kein Sanitizer und kein Renderer.
Sie erzeugt Text für ein Modell, sie erzeugt nichts, was je in einen Browser geht. `lxml_html_clean`
(der Nachfolger von `lxml.html.clean` seit lxml 5) wird ausdrücklich **nicht** gebraucht und
ist auch nicht installiert.

---

## Das Token-Budget (die harte Grenze dieser Phase)

Gemessen am 2026-08-24 mit `uv run python scripts/check_tool_budget.py`
`[VERIFIED: Lauf gegen den Arbeitsbaum]`:

```
tools/list: 14358 bytes, 20 tools, budget 15000
  calendar_create_event: 1351 bytes
  calendar_list_events:   951 bytes
  search:                 924 bytes
  talk_browse:            886 bytes
  deck_create_card:       877 bytes
```

`BUDGET_BYTES = 15_000`, `MAX_TOOL_BYTES = 1400` `[VERIFIED: scripts/check_tool_budget.py]`.

**642 Bytes frei. `talk_browse`, das nächstliegende Vorbild, kostet 886.** `mail_browse` hat
mindestens so viele Parameter wie `talk_browse` (Ebene, zwei Ids, Limit, Cursor, Filter), also
eher mehr. Der Gate-Lauf wird rot, und zwar nicht am Ende der Phase, sondern in dem Plan, der
das Werkzeug registriert.

**Empfehlung:** Die Phase hebt `BUDGET_BYTES` **einmal** auf die eigene neue Messung plus 15
Prozent, aufgerundet auf die nächsten 500, mit einer datierten Messzeile im Skript, genau nach
der Regel, die schon zweimal angewandt wurde (Phase 1: 10643 auf 12500; Phase 8: 12801 auf
15000). Bei geschätzten 15300 Bytes wären das 18000; die Zahl entsteht aus der Messung, nicht
aus dieser Schätzung. `MAX_TOOL_BYTES` bleibt bei 1400 und ist der eigentliche Wächter:
`mail_browse` muss darunter bleiben, was mit `talk_browse` als Vorbild machbar ist.

Der Phase-9-Grundsatz ("eine Anhebung erfolgt nur gegen eine Messung, die sie braucht") ist
damit erfüllt, und TOOL-15 in Phase 11 verankert danach auf die Endmessung mit 21 plus
Werkzeugen. Der Plan sollte das in der Messzeile ausdrücklich als Zwischenstand markieren,
damit Phase 11 nicht eine bereits grosszügige Zahl noch einmal grosszügig anhebt.

**Zwei weitere eingefrorene Zahlen** (Falle "die eingefrorenen Literale" aus Phase 9):
`tests/contract/test_tool_surface.py` behauptet `len(tools) == 20` und pflegt `EXPECTED_TOOLS`
als Menge; `scripts/acceptance_all_tools.py` hält `EXPECTED_TOOLS = 20`. Beide müssen auf 21
und um den Namen `mail_browse` erweitert werden, sonst ist der Contract-Test rot
`[VERIFIED: beide Dateien gelesen]`. Die README-Werkzeugtabelle wird gegen die laufende
Registry geprüft, ist also kein zweiter Pflegeort, aber sie muss stimmen.

---

## SEC-01: wohin der Text gehört

Die Kette in einem Satz, wie sie in der Doku stehen kann: dieser Server liest fremde Inhalte
(Mail und Talk sind von Dritten geschrieben), er hat Zugang zu privaten Daten (Dateien,
Kalender, Notizen, Mail), und er hat genau einen Ausgangskanal (`talk_send`). Drei Dinge
zusammen sind die Kette, die Simon Willison "lethal trifecta" nennt
`[CITED: simonwillison.net/2025/Jun/16/the-lethal-trifecta/]`: private Daten, fremder Inhalt,
Kommunikation nach draussen. Ein Sprachmodell trennt Daten und Anweisungen nicht zuverlässig,
also kann eine Mail eine Anweisung tragen, das Modell kann ihr folgen, und die Antwort kann
den Weg nach draussen nehmen.

Was das Projekt dagegen schon hat und was der Text benennen muss:

| Gegenmassnahme | Wo sie steht |
|----------------|--------------|
| `talk_send` hinter `NC_MCP_TALK_SEND`, ein Admin-Schalter | Phase 9, TALK-04, `exapp/config_values.py`, `CONFIG_KEYS` sechster Eintrag |
| Mail ist strikt lesend, es gibt keinen zweiten Ausgangskanal | diese Phase |
| Keine destruktiven Schreibpfade überhaupt | TOOL-09 plus das Gate |
| Der Assistent sieht nie mehr als der angemeldete Nutzer | Impersonation, Zwei-Konten-Beweise |
| Marker in fremdem Text werden entfernt, bevor der Server eigene schreibt | `tools/marks.py`, ME-03 |

Die Ablageorte, mit den Gates, die sie schon prüfen:

| Ort | Was hin muss | Bestehendes Gate |
|-----|--------------|------------------|
| `docs/privacy.md`, Abschnitt "What leaves your control" | die Kette, benannt, mit dem Schalter als Gegenmassnahme | keins; Prosa |
| `README.md`, nach "What this server cannot do" | derselbe Inhalt kürzer, plus eine Zeile in "Known limitations" für die Mail-Familie | Werkzeugtabelle wird gegen die Registry geprüft |
| `appinfo/info.xml`, drei `<description>` (kein `lang`, `de`, `fr`) | ein Mail-Aufzählungspunkt bei den Fähigkeiten, der Satz "Mail is read only" in der Liste "What it will not do", und der Ausgangskanal-Satz | `description_problems` in `tests/unit/test_exapp_env_setup.py`: kein Backtick, keine Tabelle, kein Bild, keine horizontale Linie, kein HTML-Element, Absätze durch Leerzeilen getrennt, `summary` maximal 128 Zeichen. Element-Reihenfolge ist schemabindend |
| dasselbe, als prüfbare Behauptung | ein Marker pro Sprache, nach dem Muster von `test_every_description_carries_the_answer_of_the_faq` (heute: `background`/`Hintergrund`/`arrière-plan`, `switch`/`Schalter`/`interrupteur`, `disconnect`/`trenn`/`déconnect`) | derselbe Test, erweitert |
| `docs/faq.md` | optional eine Frage "Kann der Assistent Mails senden" mit der Antwort nein | keins |
| `changelog` beziehungsweise Release-Notizen | eine neue Werkzeugfamilie ist nutzerrelevant | globale Regel |

Empfehlung für die drei Marker-Tripel, die den Mail-Satz prüfbar machen: EN `read only`, DE
`nur lesen`, FR `lecture seule`. Das Gegenprobe-Muster der Datei
(`test_the_text_gate_rejects_a_backtick_and_a_table`) bleibt unverändert nutzbar.

Ein Hinweis zum Ton, weil der Store-Text das einzige ist, was die meisten lesen: der Satz
"Mail ist strikt lesend" ist eine Fähigkeitsaussage und kein Sicherheitsversprechen. Das
Versprechen ist "es gibt in dieser App keinen Weg, eine Mail zu senden", und das ist
prüfbar, weil das Gate es prüft.

**Eine Falle im Store-Text, die genau bei Mail zuschlägt:** `FORBIDDEN_VOCABULARY = "archiv"`
in `tests/unit/test_exapp_env_setup.py` prüft den **Manifest-Text** (Summary und die drei
Beschreibungen) gegen dieses Wort, in Kleinschreibung und als Teilzeichenkette
`[VERIFIED: tests/unit/test_exapp_env_setup.py Zeilen 1675 und 1777]`. Eine
Mail-Aufzählungszeile, die die Postfächer benennt ("Inbox, Sent, Archive, Trash"), macht den
Test rot, und zwar in allen drei Sprachen (englisch `Archive`, deutsch `Archiv`, französisch
`Archives`). Die Beschreibung nennt also Ebenen statt Postfachnamen. Für README und Doku gilt
das Gate nicht, dort ist das Wort erlaubt, und im Testcode steht es ohnehin schon (die
Talk-Nadel `/archive`).

---

## Don't Hand-Roll

| Problem | Nicht selbst bauen | Stattdessen | Warum |
|---------|--------------------|-------------|-------|
| HTML parsen | eigener Tag-Scanner, Regex auf `<[^>]*>` | `lxml.html` mit `no_network=True` | Mail-HTML ist kaputt, verschachtelt, in fremden Zeichensätzen. Der Parser ist das Schwere, die Absatzpolitik das Leichte |
| IMAP sprechen | ein IMAP-Client im Connector | die OCS-Routen der Mail-App | Die App hält Sitzung, Cache, Rechte und Entschlüsselung. Ein zweiter IMAP-Client wäre ein zweites Rechtemodell |
| Volltextsuche in Mails | eigener Index | `filter` der App, ohne `body:` | Der Index gehört der App; `body:` kostet eine IMAP-Runde und ist deshalb bewusst draussen |
| Phishing bewerten | eigene Heuristik | `phishingDetails` und `isSenderTrusted` durchreichen | MAIL-02 verlangt es wörtlich als Datenfelder statt als Filter. Eine eigene Bewertung wäre eine zweite, schlechtere Meinung über fremden Text |
| DKIM prüfen | eigene Kryptoprüfung | `hasDkimSignature` plus `dkimValid` durchreichen | V6 der ASVS: Kryptografie nie selbst bauen; und die App hat das Ergebnis schon |
| Cursor-Zustand halten | Tabelle, Session, Ablauf | `paging.encode_cursor`/`decode_cursor` mit dem `sent_at` in `o` | SRV-05, stateless, überlebt einen Neustart |
| Kappungsmarkierung | Marker frei im Text formulieren | `marks`-Konstante plus Filtermuster | Ein Marker ohne Filter ist ein Angriffsweg (ME-03), und eine fremde Mail ist der billigste Ort dafür |
| App-Erkennung | try/except um jeden Aufruf | `capabilities.require_app` | SRV-04, ein Cache, ein Fehlersatz, eine Stelle |
| Fehlermeldungen | pro Aufrufstelle formulieren | `_MISSING` plus `_status_error` | Ein Satz, den der Nutzer liest, gehört an eine Stelle |

**Kernaussage:** In dieser Familie ist fast alles schon gebaut, in der Mail-App. Der Anteil
dieses Servers ist Transport, Menge, Form und ein Verbot. Jede Zeile, die mehr tut, ist eine
zweite Wahrheit über fremde Daten.

---

## Häufige Fallen in dieser Phase

### Falle 1: Der Erkennungstest ist grün, ohne etwas zu belegen

Nach `occ app:disable mail` antwortet die Navigation weiter mit einem `mail`-Eintrag und die
Mail-Routen antworten weiter 200. **Erst nach einem Neustart der Nextcloud** verschwindet
beides `[VERIFIED: Live-Messung 2026-08-24]`. Ein SRV-06-Test ohne Neustart behauptet, die
Degradation funktioniere, und hat sie nie gesehen.
**Warnzeichen:** Der Fehlt-Zweig eines Tests wird nie erreicht, aber der Test ist grün.

### Falle 2: Ohne `limit` kommt eine Nachricht, nicht alle

`min(100, max(1, null))` ist 1. Die OpenAPI-Beschreibung sagt das Gegenteil. Ein Werkzeug, das
`limit` nur "wenn gesetzt" mitsendet, liefert bei Default genau eine Mail und sieht wie ein
leeres Postfach aus.
**Vermeidung:** `limit` ist im Client ein Keyword **ohne** Default und wird auf 1 bis 50
gekappt, genau wie es Phase 8 für den Tables-Client entschieden hat. Eine URL ohne `limit`
kann konstruktiv nicht entstehen.

### Falle 3: Der Filter filtert nichts und sagt es nicht

`subject:Rechnung Mai` filtert auf `Rechnung`, `start:2026-08-01T10:00:00Z` filtert auf
`2026-08-01T10` (also praktisch auf nichts), `is:ungelesen` filtert überhaupt nicht, und keiner
der drei Fälle erzeugt einen Fehler. Der Parser verwirft still
`[VERIFIED: FilterStringParser::parseFilterToken, Rückgabe false]`.
**Vermeidung:** Positivliste im Werkzeug, Ablehnung mit der Liste der erlaubten Typen, und
`start:`/`end:` nur als Ziffernfolge annehmen. Eine Antwort, die richtig aussieht und falsch
ist, ist teurer als ein Fehler.

### Falle 4: Reine Textmails kommen als HTML an

Auch ohne HTML-Teil läuft der Body durch `convertLinks` und damit durch `htmlspecialchars` und
HTMLPurifier (K2). Ein Wandler, der auf `hasHtmlBody` schaut, liefert bei jeder Textmail
`Gr&uuml;&szlig;e` und `<a href=...>`.
**Warnzeichen:** `&amp;`, `&uuml;` oder `<a ` im Antworttext eines Tests mit einer Textmail.

### Falle 5: Der Volltext-Pfad stürzt an einer leeren Mail ab

`lxml.html.document_fromstring("")` und `("   ")` werfen `ParserError("Document is empty")`
`[VERIFIED: gemessen]`. Eine Mail ohne Body ist normal (nur Anhänge), und bei HTTP 206 fehlt
`body` per Design.
**Vermeidung:** Vor dem Parsen auf leer prüfen und leeren Text zurückgeben. Und der 206-Zweig
antwortet mit einem Satz, der sagt, warum kein Text da ist ("die Nachricht ist verschlüsselt
und konnte nicht entschlüsselt werden"), nicht mit einer leeren Erfolgsantwort. Ein
Erfolgsergebnis ohne Inhalt ist die Form, die zum Erfinden einlädt (T-01-75).

### Falle 6: Die zwei bestehenden Kappungsmarkierungen sind für Mail beide unwahr

`TRUNCATION_NOTE` sagt "call files_read with offset N to continue", was es für eine Mail nicht
gibt. `EXCERPT_TRUNCATION` sagt "call fetch with this id for the full text", und `fetch` **ist**
der Aufruf, der gerade gekappt hat. Beide würden das Modell in eine Schleife oder in eine
nicht existierende API schicken.
**Vermeidung:** Ein dritter Marker in `marks.py`, der sagt, dass hier Schluss ist und keine
Fortsetzung existiert, plus sein Muster in `_PATTERNS`, damit fremder Text ihn nicht fälschen
kann. Ein Marker ohne Filter ist genau der Angriffsweg, den das Modul beschreibt, und eine Mail
ist der billigste Ort dafür: jeder Fremde darf hineinschreiben.

### Falle 7: `metadata` von `fetch` nimmt keine Objekte

`FetchResult.metadata` ist `dict[str, str] | None` `[VERIFIED: src/mcp_connector/models.py]`.
`phishingDetails` ist ein Objekt mit einer Liste, `smime` ein Objekt mit drei Feldern. Beide
lassen sich dort nicht ablegen, und `search`/`fetch` sind die einzigen zwei Werkzeuge **mit**
Output-Schema, also ist eine Schemaänderung eine Änderung am ChatGPT-Kontrakt.
**Vermeidung:** Flache Projektion mit Stringwerten, wie es der Datei-Zweig für `truncated` und
`next_offset` schon macht: `sender_trusted: "true"`, `dkim: "valid" | "invalid" | "unchecked"`,
`phishing_warning: "true"`, `phishing_checks: "spf, dmarc"` (die auslösenden `type`-Werte,
komma-getrennt), `encrypted: "true"`, `signature: "valid" | "invalid" | "unsigned"`. Die
Signale bleiben damit Datenfelder und nicht Prosa, ohne dass das Schema wächst. Der
Alternativweg wäre, die Signale in den `text` zu schreiben, und das ist die schlechtere Wahl:
dann stehen sie neben fremdem Text, der genauso aussehen darf.

### Falle 8: Der 500er wird als Nextcloud-Problem gemeldet

`_check_transport` fängt jeden Status ab 500 ab, bevor der Envelope gelesen wird, und sagt
"This is a problem on the Nextcloud side. Retry later or check its log." Für die Postfachliste
ist die häufigste Ursache aber der Mailserver **des Nutzers** oder ein noch nie
synchronisiertes Postfach (K6).
**Vermeidung:** Im Mail-Client abfangen, mit einem Satz, der auf die Mail-App und das Konto
zeigt. Nach dem Vorbild der 304 in `clients/talk.py`: lokal, mit Begründung, weil der Status
nur an dieser Stelle diese Bedeutung hat.

### Falle 9: 206 ist ein Fehler, obwohl er einer nicht ist

`_OK_STATUS` kennt 100, 200 und 201. Eine S/MIME-verschlüsselte Mail antwortet 206 mit voller
Metadatenlage und ohne Body, und `parse_ocs` macht daraus einen Fehler (K7).
**Vermeidung:** Lokal im Mail-Client behandeln, nicht global in `_OK_STATUS`.

### Falle 10: `id` gegen `databaseId`

Ein Postfach hat beides: `id` ist base64 des IMAP-Namens, `databaseId` ist die Zahl. Eine
Nachricht hat `databaseId`, `uid`, `remoteId`, `messageId` und `id` (nur im Volltext). Der
Präfix aus MAIL-02 heisst `mail:<databaseId>`, und alle anderen vier sind falsch.
**Vermeidung:** Die Projektion nennt nur `databaseId` und die Feldnamen der Antwort tragen
nirgends `id` ohne Erklärung. Ein Roundtrip-Test in `test_ids.py`.

### Falle 11: Der Ziffernwächter fehlt

`GET /apps/mail/message/notanumber` antwortet 404 statt eines Routing-Fehlers, weil PHP auf 0
castet `[VERIFIED: Live-Messung]`. Der Server hat also keinen Schutz, der fehlt, aber ein
Modellwert wäre ohne Prüfung direkt in einem URL-Pfad.
**Vermeidung:** Der Wächter der Tables-Familie, wörtlich übertragen: nur Ziffern, sonst
ablehnen, bevor ein Request entsteht. Er kostet nichts und hält den teuersten Aufruf der
Familie (jeder Volltext-Abruf öffnet eine IMAP-Sitzung) von einem sicher falschen Wert fern.

### Falle 12: Threads statt Nachrichten

Ohne `view=singleton` liefert der Controller die Thread-Ansicht
`[VERIFIED: MailboxesApiController::listMessages]`. Ein Thread-Root ist keine Nachricht, und
der Unterschied ist in der Antwort nicht sichtbar: die Felder sind dieselben.
**Vermeidung:** `view=singleton` ist im Client eine Konstante und kein Parameter, mit
Begründung im Kommentar. Dasselbe Prinzip wie `READ_ONLY_PARAMS` bei Talk: was ein Aufrufer
falsch machen kann, ist kein Argument.

### Falle 13: Die Cursor-Grenze verschluckt Nachrichten

Der Cursor filtert `sent_at <` (strikt). Zwei Mails mit derselben Sekunde an einer
Seitengrenze: die zweite fällt aus, für immer.
**Vermeidung:** Benennen, nicht heimlich reparieren. Das Projekt hat dieselbe Entscheidung
beim halboffenen Kalenderfenster schon getroffen ("das Zeitfenster wird nie korrigiert"), und
die honest limit gehört in den Docstring und in die README-Grenzentabelle. Eine eigene
Korrektur (Cursor plus eins, dann clientseitig entdoppeln) wäre eine zweite Wahrheit über die
Reihenfolge der App.

### Falle 14: Das Budget-Gate wird zur Dekoration

Zwei Wege, es falsch zu machen: die Anhebung ohne Messung (dann schützt es nichts), oder die
Anhebung so gross, dass Phase 11 nichts mehr messen kann. Beide sind schon passiert, der erste
in Phase 1.
**Vermeidung:** Messung plus 15 Prozent, aufgerundet auf 500, mit Datum und Werkzeugzahl in
der Messzeile, und der Vermerk, dass TOOL-15 in Phase 11 neu verankert.

### Falle 15: Der Zwei-Konten-Beweis wird an der falschen Naht geführt

Für Talk und Tables läuft er auf der Impersonation-Naht mit zwei Credential-Objekten. Für Mail
ist die Vorbedingung eine andere: bob hat **kein** Mail-Konto, und `account/list` antwortet ihm
200 mit `[]` `[VERIFIED: Live-Messung]`. Ein Test, der bob eine fremde `mailboxId` lesen lässt,
braucht deshalb ein Mail-Konto für alice **und** die Erwartung, dass bob 403 oder 404 sieht,
und nicht die Erwartung, dass bob einen Fehler wegen fehlenden Kontos bekommt. Die zwei Fälle
sehen im Testprotokoll gleich aus und beweisen Verschiedenes.

---

## Mechanische Checkliste (exakte Anknüpfungspunkte)

### Produktionscode

| Datei | Änderung |
|-------|----------|
| `src/mcp_connector/nextcloud/clients/mail.py` | NEU. Vier Pfadkonstanten, `get_accounts`, `get_mailboxes`, `get_messages`, `get_message`. Nur GET. `view=singleton` als Konstante. `limit` Keyword ohne Default, gekappt. Behandlung von 206 und 500 lokal. Modul-Docstring mit dem SCOPE_IGNORE-Absatz aus `docs/spike-mail.md` plus Korrektur K1 |
| `src/mcp_connector/tools/mail.py` | NEU. `DEFAULT_LIMIT = 20`, `MAX_LIMIT = 50`, `MAX_PREVIEW_BYTES` (Vorbild `MAX_MESSAGE_BYTES = 800`), `browse()` mit drei Ebenen, Filter-Positivliste, Projektionen, `_envelope`, Cursor mit `sent_at` in `o` und `mailbox_id` als Scope-Schlüssel |
| `src/mcp_connector/tools/html_text.py` | NEU (oder als privater Teil von `tools/mail.py`). Eine Funktion, `lxml`, Leer-Schutz, `script`/`style` weg, Blockelemente zu Zeilenumbrüchen |
| `src/mcp_connector/tools/marks.py` | Dritter Marker plus Muster in `_PATTERNS` |
| `src/mcp_connector/tools/chatgpt.py` | `case "mail"` in `fetch`, `_fetch_mail`, Import von `mail`-Client und `mail`-Tools, `_UNFETCHABLE`-Zweig bleibt |
| `src/mcp_connector/ids.py` | `encode_mail`, `"mail"` in `parse` (einteilig wie `file`/`note`), Ziffernwächter, `_HINT` erweitert (der Hinweistext ist Teil des Kontrakts) |
| `src/mcp_connector/nextcloud/capabilities.py` | `mail_available: bool | None`, `"mail"` in `has()`, `"mail"` in `_MISSING`, Navigationspfad-Konstante, Nachfüllfunktion mit `dataclasses.replace` in derselben Cache-Zeile |
| `src/mcp_connector/server/reg_mail.py` | NEU. Ein Werkzeug, `READ_ONLY`, `structured_output=False`, `graceful`, `compact`, `Literal`-Enum für `level`, leere Strings als Defaults statt `None` |
| `src/mcp_connector/vulture_whitelist.py` | Neue Namen vorübergehend hinein, mit der Registrierung wieder heraus (Phase-08-Muster: das Gate ist am Ende ohne Eintrag grün) |

### Tests

| Datei | Änderung |
|-------|----------|
| `tests/unit/test_mail_client.py` | NEU. Alle Pfade: 200, leere Liste, 206, 403, 404 mit String-`data`, 500 mit 996, HTML-Loginseite, `limit`-Kappung, `view`-Konstante, Ziffernwächter |
| `tests/unit/test_mail_tools.py` | NEU. Drei Ebenen, Filter-Positivliste inklusive Ablehnung, Cursor-Roundtrip und Scope-Ablehnung, Kappung, `previewText: null` |
| `tests/unit/test_html_text.py` | NEU. Leer, nur Leerraum, kaputtes HTML, Entities, Blockumbrüche, `script`/`style`, DOCTYPE-Rest, sehr lange Eingabe |
| `tests/unit/test_ids.py` | `mail`-Roundtrip, Ablehnung von `mail:abc` und `mail:` |
| `tests/unit/test_chatgpt_fetch.py` | `mail`-Zweig, Marker-Filter auf fremdem Text, `metadata`-Werte alle `str` |
| `tests/unit/test_ocs_capabilities.py` | Navigationsweg: vorhanden, fehlend, leere Liste als Fehler, Cache-Treffer ohne zweiten Request, `has("mail")` |
| `tests/contract/test_tool_surface.py` | `EXPECTED_TOOLS` plus `mail_browse`, `len(tools) == 21`, Annotationen (`READ_ONLY`) |
| `tests/contract/test_no_destructive_calls.py` | Neue Nadeln, `MAIL_ROUTES` als Gegenproben, `ALLOWED_MAIL_ROUTES` als Positivliste, plus der Nur-GET-Test für `clients/mail.py` |
| `tests/unit/test_exapp_env_setup.py` | Marker-Tripel für den Mail-read-only-Satz in allen drei Sprachen |
| `tests/integration/test_mail_read.py` | NEU. Braucht GreenMail: Konten, Postfächer mit `specialRole` und `unread`, Envelopes mit `previewText`, Volltext mit HTML zu Text, Filter, `\Seen` vorher und nachher, Zwei-Konten-Negativbeweis |
| `tests/integration/test_srv06_degradation.py` | NEU oder Erweiterung. Drei Familien, jeweils mit Neustart |

### Skripte, Doku, Topologie

| Datei | Änderung |
|-------|----------|
| `scripts/check_tool_budget.py` | `BUDGET_BYTES` einmal angehoben, mit datierter Messzeile und dem Vermerk "Zwischenstand, TOOL-15 verankert neu" |
| `scripts/acceptance_all_tools.py` | `EXPECTED_TOOLS = 21`, Aufruf für `mail_browse` |
| `scripts/bootstrap_exapp.sh` | GreenMail als vierter Dienst plus Konto auf `greenmail:3143`, `imapSslMode none`, Testmail über SMTP 3025, `occ mail:account:sync <id> -f`. Die Vorlage steht wörtlich in `docs/spike-mail.md` |
| `compose.exapp.yml` | GreenMail-Dienst, kein veröffentlichter Port (T-08-05) |
| `docs/spike-mail.md` | Korrektur K1 als eigener Abschnitt: die deklarierten OCS-Routen, damit das Dokument nicht als Beleg für eine falsche Prämisse zitiert wird |
| `docs/privacy.md` | Exfiltrationskette in "What leaves your control" |
| `README.md` | Werkzeugtabelle, ein Mail-Abschnitt (Filtergrammatik, Ebenen, Grenzen), Zeilen in "Known limitations" (Cursor-Sekundengrenze, `body:` fehlt bewusst, Mail ist optional), Trifecta-Absatz |
| `appinfo/info.xml` | Beschreibung EN/DE/FR, Reihenfolge der Elemente unverändert, Version nicht anfassen |

---

## Codebeispiele

### Der Client, mit den vier Formen und den zwei Sonderstatus

```python
# src/mcp_connector/nextcloud/clients/mail.py

#: The declared OCS routes of the Mail app. All four are GET, all four stand in the
#: ``openapi.json`` the app ships, and none of them carries
#: ``#[OpenAPI(scope: SCOPE_IGNORE)]``. That is the whole reason this module exists in this
#: shape: Mail also has an internal route set below ``/apps/mail/api/`` which the phase 8
#: spike measured, and those three listing routes ARE ``SCOPE_IGNORE``, so a Mail release may
#: change or drop them without a deprecation. They are deliberately not used here. Falling
#: back to them would trade a declared API for the internals of Mail's own frontend, and it
#: would make the write gate weaker as well: ``/api/messages`` is a resource route, so POST
#: creates, PUT changes and DELETE removes on exactly the path a read would use.
ACCOUNTS_PATH = "/apps/mail/account/list"
MAILBOXES_PATH = "/apps/mail/ocs/mailboxes"
MESSAGES_PATH = "/apps/mail/ocs/mailboxes/{mailbox}/messages"
MESSAGE_PATH = "/apps/mail/message/{message}"

#: Not a parameter. Without ``singleton`` the controller answers the threaded view, a thread
#: root is not a message, and the two are indistinguishable in the payload.
VIEW = "singleton"

#: Upper bound of one window. The app caps at 100 and answers exactly ONE message when
#: ``limit`` is absent, because ``min(100, max(1, null))`` is 1 in PHP 8. So ``limit`` is a
#: keyword without a default here: a URL without it cannot be built by construction.
MAX_MESSAGES = 50

#: HTTP 206 is not a failure: the message was found and everything but ``body`` is there,
#: because it could not be decrypted. ``ocs.parse_ocs`` only accepts 100, 200 and 201, so it
#: is handled here and not by widening ``_OK_STATUS``: 206 means this on exactly one route,
#: the same reason Talk's 304 is caught in the Talk client.
PARTIAL = 206
```

### Der zweite Erkennungskanal, im bestehenden Cache

```python
# src/mcp_connector/nextcloud/capabilities.py

#: Mail publishes no capabilities section. Measured on Nextcloud 34.0.3 with Mail 5.11.1:
#: the sections are activity, app_api, bruteforce, circles, core, dav, deck, downloadlimit,
#: files, files_sharing, notes, notifications, ocm, password_policy, provisioning_api,
#: recommendations, spreed, systemtags, theming, user_status and weather_status. No mail.
#: The navigation of the signed in user answers the question instead, and it is a core OCS
#: route, so it needs no app of its own to ask.
NAVIGATION_PATH = "/core/navigation/apps"

#: Filled on first demand and stored in the SAME cache entry, with the original timestamp,
#: so the TTL of the snapshot is not extended by asking a second question about it. A cache
#: of its own would be a third piece of module level state, and ALLOWED_MODULE_STATE in
#: tests/contract/test_no_destructive_calls.py names exactly two (D-20).
async def load_mail(clients: NcClients) -> Capabilities:
    ...
```

### Die flache Projektion der Vertrauens-Signale

```python
# src/mcp_connector/tools/chatgpt.py, _fetch_mail

# FetchResult.metadata is dict[str, str], and search plus fetch are the only two tools WITH
# an output schema, so a nested object here would be a change to the ChatGPT contract. The
# signals stay data fields, flattened, exactly the way the file branch writes "truncated"
# and "next_offset". They are never merged into ``text``: next to foreign content, a sentence
# written by this server is indistinguishable from a sentence written by the sender.
metadata = {"kind": "mail", "sender_trusted": "true" if trusted else "false"}
if isinstance(dkim, bool):
    metadata["dkim"] = "valid" if dkim else "invalid"
else:
    metadata["dkim"] = "unchecked"   # dkimService.getCached returned nothing, not "bad"
```

### Der Filter, auf einer Positivliste

```python
# src/mcp_connector/tools/mail.py

#: The filter grammar this server documents, and nothing else. The app's parser drops an
#: unknown token silently (``parseFilterToken`` returns false and nobody reads it), so a
#: typo would answer the UNFILTERED list and the model could not tell. ``body:`` exists in
#: the app and is deliberately absent here: it is the one filter that leaves the database
#: and searches over IMAP (``MailSearch::getIdsLocally``).
#:
#: Two properties of the app's parser are part of the documented grammar, because a caller
#: cannot get them right by guessing: the filter is split on SPACES, and a token is split at
#: its FIRST colon with the rest thrown away. So a value with a space or a colon has to be
#: percent encoded, and ``start:``/``end:`` take unix seconds and not an ISO timestamp,
#: because the value is compared against the integer column ``sent_at``.
FILTER_TYPES = frozenset({"is", "not", "from", "subject", "tags", "start", "end"})
```

---

## Stand der Technik

| Alt | Aktuell | Wann geändert | Bedeutung |
|-----|---------|---------------|-----------|
| Mail hat nur interne `SCOPE_IGNORE`-Routen und eine deklarierte Volltextroute | Mail 5.11.1 hat sieben deklarierte OCS-Routen, davon vier lesende, die diese Phase vollständig abdecken | die `ocs`-Einträge und die `#[ApiRoute]`-Attribute existieren in 5.11.1; wann sie kamen, ist hier nicht datiert | Der Kern der Phase steht auf einer zugesagten API. Das Ersetzbarkeitsrisiko der Übergabe entfällt für den benutzten Weg |
| Volltext lesen könnte den Brute-Force-Zähler treiben | in 5.11.1 registriert die Mail-App keinen einzigen Versuch, weil `throttle()` nirgends aufgerufen wird | - | Das Memo-Muster aus dem Spike muss nicht in Produktionscode; der Grund gegen Schleifen ist die IMAP-Sitzung, nicht der Zähler |
| `lxml.html.clean` als Teil von lxml | seit lxml 5 ausgelagert in `lxml_html_clean` | lxml 5.x | Irrelevant für diese Phase, weil nur Text extrahiert wird. Wichtig, damit niemand den Import versucht |
| Lethal trifecta als Begriff | etabliert und zitierbar | Juni 2025 | Der SEC-01-Text kann den Begriff benutzen und muss ihn nicht erfinden |

**Veraltet oder falsch in bestehenden Projektdokumenten:**

- `docs/spike-mail.md`, Abschnitt "Replaceability": beschreibt die internen Routen als das
  Rückgrat und die OCS-Volltextroute als "die einzige der vier, die eine deklarierte Route
  ist". Für die vier gemessenen Wege stimmt das; für die Familie nicht. Zu korrigieren.
- `docs/spike-mail.md`, letzter Abschnitt: die Brute-Force-Regel ist für 5.11.1 wirkungslos
  (K5). Der Satz kann bleiben, braucht aber die Messung daneben.
- ROADMAP, Recherche-Hinweis zu Phase 10 ("Die Antwortform des Navigations-Erkennungswegs ist
  nie gegen eine laufende Instanz geprüft"): jetzt geprüft, in vier Zuständen.

---

## Assumptions Log

| # | Annahme | Abschnitt | Risiko, wenn falsch |
|---|---------|-----------|---------------------|
| A1 | Die Wertemenge von `specialRole` ist die Horde-Special-Use-Liste in Kleinschreibung (`inbox`, `sent`, `drafts`, `trash`, `junk`, `archive`, `flagged`) oder die Zahl 0 | Ebene `mailboxes` | Eine Doku, die falsche Werte nennt, und ein Modell, das die Inbox nicht findet. Stufe 2 mit GreenMail klärt es in einem Lauf |
| A2 | `previewText` ist bei echten Daten gesetzt und kurz (die App füllt es über `PreviewEnhancer`) | Ebene `messages` | Wenn es oft `null` ist, ist die Envelope-Antwort inhaltsarm und die Kappung sinnlos. Nur mit echten Daten messbar |
| A3 | Der Volltext einer echten HTML-Mail wird nach der Wandlung nicht regelmässig grösser als die Kappe, sodass fast jede Antwort gekappt wäre | HTML zu Text, Falle 6 | Wenn doch, ist die Kappe zu klein gewählt und die Familie unbrauchbar. Mit GreenMail und zwei realistischen Mails entschieden |
| A4 | `filter` und `cursor` verhalten sich auf der OCS-Route genauso wie im Frontend, weil derselbe `IMailSearch` dahinter liegt | Filtergrammatik | Der Filter ist nur mit echten Daten prüfbar; die Grammatik selbst ist aus dem Parser gelesen und damit sicher |
| A5 | Der Aufwand von `mail_browse` liegt bei 850 bis 1000 Bytes, also unter `MAX_TOOL_BYTES` 1400 | Budget | Wenn darüber, muss die Beschreibung kürzer, nicht die Grenze höher |
| A6 | Der Navigationsweg funktioniert auch dort, wo ein Admin die Mail-App aus dem Navigationsmenü entfernt hat | zweiter Erkennungskanal | Dann meldet der Server "Mail fehlt", obwohl die App läuft. Nextcloud kennt eine Sortierung und ein Verstecken von Navigationseinträgen; ob ein verstecktes Element in dieser Antwort fehlt, ist **nicht** gemessen. Die Gegenprobe wäre die Suchprovider-Liste als zweite Meinung, und genau deshalb bleibt sie im Test |
| A7 | Zwei zusätzliche Requests pro Aufruf (Navigation plus Konten) sind für die Ebene `mailboxes` akzeptabel, weil `accountId` Pflicht ist und ein Modell die Kontonummer nicht raten soll | Architektur | Wenn nicht, muss `mail_browse(level="mailboxes")` ohne `account_id` einen Fehler geben statt das erste Konto zu nehmen. Empfehlung: Fehler mit Verweis auf `level="accounts"`, so wie Talk das Token verlangt |

---

## Offene Fragen

1. **Braucht diese Phase Stufe 2 des Spikes (GreenMail), oder reicht Unit-Ebene plus die
   Feldlisten aus dem Quelltext?**
   - Was wir wissen: Die Erreichbarkeit ist bewiesen, die Feldnamen sind aus dem Quelltext der
     installierten Fassung gelesen, die Grammatik ist aus dem Parser gelesen. Die Vorlage für
     GreenMail steht fertig in `docs/spike-mail.md`.
   - Was unklar ist: A1 bis A4 sind ohne echte Daten nicht entscheidbar, und die
     Erfolgskriterien 1 bis 3 sind Nutzeraussagen ("Nutzer kann seine Mail lesen"), die ein
     Unit-Test mit erfundenen Antworten nicht belegt. MAIL-03 verlangt wörtlich "dokumentiert
     wie getestet".
   - Empfehlung: **GreenMail als erster, blockierender Plan der Phase.** Er ist billig (ein
     Compose-Dienst, ein Konto, eine Testmail, ein Sync-Kommando, alles schon aufgeschrieben)
     und er macht aus vier Annahmen vier Messwerte. Ohne ihn ist der Phasenabschluss eine
     Behauptung.

2. **Wird der interne Routensatz irgendwo doch gebraucht?**
   - Was wir wissen: Für MAIL-01 bis MAIL-03 nicht. Alle verlangten Felder stehen in den
     Antworten der deklarierten Routen.
   - Was unklar ist: Ob Phase 11 (CTX-02, Mail-Ungelesen-Zähler pro Konto und Inbox) mit den
     deklarierten Routen auskommt. Die Postfachliste trägt `unread` pro Postfach, also
     wahrscheinlich ja, zum Preis von einem Request pro Konto. Der Navigationseintrag trägt
     ebenfalls ein `unread`-Feld, das in dieser Messung 0 war und dessen Bedeutung nicht
     geklärt ist.
   - Empfehlung: Nicht in dieser Phase klären, aber den Befund an Phase 11 übergeben, damit
     die 1+N-Kosten von CTX-02 aus der Postfachliste gerechnet werden und nicht neu erforscht.

3. **Wie eng darf die Byte-Kappe des Volltexts sein?**
   - Was wir wissen: `fetch` nutzt heute 512 KiB (die Datei-Grenze), Talk 800 Bytes pro
     Nachricht. Beide Zahlen sind für eine Mail falsch: 512 KiB Text ist ein
     Kontext-Totalschaden, 800 Bytes ist eine halbe Mail.
   - Was unklar ist: Die realistische Länge einer gewandelten HTML-Mail (A3).
   - Empfehlung: Nach der GreenMail-Messung entscheiden, Startwert in der Grössenordnung von
     16 KiB, mit dem Argument im Docstring. Wichtig ist nicht die Zahl, sondern dass die
     Kappung markiert ist und dass der Marker wahr ist (Falle 6).

4. **Bekommt `mail_browse` einen `account_id`-Default?**
   - Was wir wissen: Die Postfachroute verlangt `accountId`, die Nachrichtenroute `mailboxId`.
   - Empfehlung: Kein Default und kein automatisches "erstes Konto". Das ist dieselbe
     Entscheidung wie bei Talk (`messages` braucht ein Token) und bei Tables. Ein geratenes
     Konto ist die Sorte Antwort, die richtig aussieht.

---

## Environment Availability

| Abhängigkeit | Gebraucht für | Verfügbar | Version | Rückfall |
|--------------|---------------|-----------|---------|----------|
| Docker Desktop, HaRP-Topologie `nc-mcp-exapp` | Integrationsläufe, SRV-06-Nachweis | ja | Nextcloud 34.0.3.2, AppAPI 34.0.0 | keiner; ohne die Topologie skippen die Integrationstests mit dem Namen der fehlenden Variable |
| Nextcloud-App `mail` | die ganze Phase | ja, aktiviert | 5.11.1 | keiner |
| Nextcloud-App `spreed` | SRV-06 Talk-Zweig | ja | 24.0.4 | keiner |
| Nextcloud-App `tables` | SRV-06 Tables-Zweig | ja | 2.2.2 | keiner |
| ExApp-Container `nc_app_mcp_connector` | Live-Läufe durch den Proxy | ja, healthy | Image-Tag 0.1.6 | Messungen können auch direkt gegen Nextcloud laufen, wie in dieser Recherche |
| `lxml` | HTML zu Text | ja | 6.1.1 | keiner nötig |
| **Erreichbarer IMAP-Server** | echte Envelope- und Volltextformen, `specialRole`, `previewText`, Filterverhalten, `\Seen`-Nachweis | **nein** | - | **GreenMail als Compose-Dienst**, Vorlage steht in `docs/spike-mail.md`; das Spike-Konto zeigt heute auf `imap.invalid` |
| `occ` im Nextcloud-Container | Bootstrap, App aus- und einschalten | ja | - | keiner. Unter Git Bash `MSYS_NO_PATHCONV=1` voranstellen, sonst wandelt die Shell `/var/www/html/occ` in einen Windows-Pfad und `php` meldet "Could not open input file" |
| Neustart der Nextcloud | SRV-06-Nachweis | ja, `docker restart nc-mcp-exapp-nc`, danach in einer Runde wieder `installed: true` | - | keiner. Ohne Neustart ist der Nachweis wertlos (Falle 1) |

**Fehlende Abhängigkeiten ohne Rückfall:** keine.
**Fehlende Abhängigkeiten mit Rückfall:** IMAP-Server. Der Rückfall ist kein Rückfall, sondern
ein Plan: GreenMail. Siehe offene Frage 1.

Zustand der Topologie nach dieser Recherche: unverändert. Für die SRV-06-Messung wurde
`mail` ab- und wieder angeschaltet und die Nextcloud zweimal neu gestartet; der
Endzustand ist gemessen (`mail` aktiviert, Navigation und Routen antworten wie vorher), der
Arbeitsbaum ist unberührt (`git status` leer), und der ExApp-Container läuft.

---

## Security Domain

### Anwendbare ASVS-Kategorien

| Kategorie | Anwendbar | Kontrolle in dieser Phase |
|-----------|-----------|---------------------------|
| V2 Authentication | ja, unverändert | AppAPI-Impersonation beziehungsweise OAuth aus Phase 3; diese Phase baut keinen Auth-Pfad |
| V3 Session Management | nein | Der Server ist stateless, der Cursor trägt keine Autorität (`paging`-Docstring) |
| V4 Access Control | **ja** | Jeder Mail-Zugriff läuft als der angemeldete Nutzer; der Zwei-Konten-Negativbeweis ist der Nachweis (Falle 15). Nextcloud antwortet auf eine fremde Nachrichten-Id mit 404 und gibt ihre Existenz nicht preis |
| V5 Input Validation | **ja** | Ziffernwächter auf jeder Id (Falle 11), Filter-Positivliste (Falle 3), Cursor als hostiler Text (`paging`), `limit` gekappt, HTML-Parser mit `no_network=True` und Leer-Schutz |
| V6 Cryptography | ja, indirekt | DKIM und S/MIME werden **durchgereicht**, nie selbst geprüft. Das ist die Kontrolle: keine eigene Kryptografie |
| V7 Error Handling und Logging | **ja** | Kein Antwortkörper und kein Headerwert mit `APP_SECRET` in einem Log oder einer Fehlermeldung; die 120-Zeichen-Regel des Spikes gilt für jeden neuen Messcode (T-08-01). Fehlersätze nennen den nächsten Schritt und nie einen Stacktrace |
| V8 Data Protection | **ja** | Mailinhalte sind die sensibelsten Daten, die dieser Server je transportiert. Kein Cache, keine Ablage, kein Modulzustand mit Mailinhalt (D-20). Der Capabilities-Cache hält nur ein Boolean |
| V12 Files und Resources | ja | Anhänge werden nicht heruntergeladen; die Route ist vom Gate verboten |
| V13 API und Web Service | ja | Nur GET, nur vier Pfadformen, Allowlist im Gate |

### Bekannte Bedrohungsmuster für diese Familie

| Muster | STRIDE | Standard-Gegenmassnahme |
|--------|--------|--------------------------|
| Prompt Injection in einem Mailinhalt | Tampering, Elevation | Fremder Text wird nie als Anweisung behandelt; Marker aus fremdem Text entfernen (`marks`); der Ausgangskanal liegt hinter einem Admin-Schalter |
| Exfiltration Mail-Lesen plus Talk-Senden (lethal trifecta) | Information Disclosure | SEC-01: benennen; `NC_MCP_TALK_SEND` als Gegenmassnahme; Mail hat keinen eigenen Ausgangskanal |
| Gefälschte Kappungsmarkierung in einer Mail | Spoofing | Dritter Marker plus Filtermuster (Falle 6, ME-03) |
| Signal-Wäsche: eine Mail schreibt "DKIM: valid" in ihren Text | Spoofing | Signale stehen in `metadata` und nie im `text` (Falle 7) |
| Confused Deputy über eine fremde Nachrichten-Id | Elevation | Impersonation plus der 404 der Instanz; der Ziffernwächter davor |
| SSRF über eine URL aus einer Mail (`unsubscribeUrl`, `rawUrl`, `downloadUrl`) | Tampering | Dieser Server ruft **keine** URL aus fremdem Inhalt auf. `fetch` verweigert schon heute eine `url:`-Id (T-01-75); die drei Felder werden bestenfalls als Text durchgereicht, nie verfolgt |
| Kontextflut über eine sehr grosse Mail | Denial of Service | Byte-Kappe plus Markierung; `limit` gekappt; kein Body auf der Listenebene |
| XXE oder Entity-Expansion im Mail-HTML | Tampering, DoS | Gemessen: der HTML-Parser von libxml2 löst keine Entity auf; zusätzlich `no_network=True` |
| Ein Loop über die Volltextroute | DoS gegen die eigene Instanz | Jeder Aufruf öffnet eine IMAP-Sitzung; ein Werkzeug, das nur eine Nachricht liest, kann keinen Loop bauen |

---

## Quellen

### Primär (HIGH confidence, gegen die installierte Fassung und die laufende Instanz)

- `/var/www/html/custom_apps/mail/openapi.json` (Mail 5.11.1, im Container gelesen): die
  sieben deklarierten Routen, `AccountListResponse`, `MessageApiResponse`, `IMAPFullMessage`,
  `MessageApiAttachment`
- `/var/www/html/custom_apps/mail/appinfo/routes.php`: 108 Routen, davon 59 schreibend, der
  `ocs`-Block, der `resources`-Block
- `lib/Controller/MailboxesApiController.php`, `MessageApiController.php`,
  `AccountApiController.php`: Parameter, Grenzen, Statuscodes, `NoCSRFRequired`,
  `BruteForceProtection`, `UserRateLimit`
- `lib/Db/Mailbox.php`, `lib/Db/Message.php`: die Feldlisten von `jsonSerialize`
- `lib/Model/IMAPMessage.php`, `lib/Service/Html.php`: `getFullMessage`, `convertLinks`,
  `parseMailBody`, `sanitizeHtmlMailBody`
- `lib/Service/Search/FilterStringParser.php`, `MailSearch.php`, `lib/Db/MessageMapper.php`:
  die vollständige Filtergrammatik, `cursor`-Semantik, `start`/`end` gegen `sent_at`,
  `body:` als IMAP-Runde
- `lib/IMAP/ImapMessageFetcher.php`, `lib/IMAP/MessageMapper.php`: `peek => true` in jedem
  Fetch
- Live-Messung 2026-08-24 gegen die HaRP-Topologie unter reiner AppAPI-Impersonation:
  Capabilities-Abschnitte, `core/navigation/apps` in vier Zuständen, `account/list` für zwei
  Konten, `ocs/mailboxes`, `ocs/mailboxes/{id}/messages` mit und ohne Filter,
  `message/{id}` mit gültiger und ungültiger Id, `search/providers`
- Messung `uv run python scripts/check_tool_budget.py`: 14358 Bytes bei 20 Werkzeugen
- Messung `uv run python -c ...` mit lxml 6.1.1: `text_content`-Verhalten, XXE, Billion
  Laughs, kaputtes HTML, leerer Input
- Eigene Codebasis, gelesen 2026-08-24: `nextcloud/capabilities.py`, `nextcloud/clients/ocs.py`,
  `nextcloud/clients/talk.py`, `nextcloud/credentials.py`, `tools/chatgpt.py`, `tools/marks.py`,
  `tools/talk.py`, `models.py`, `ids.py`, `paging.py`, `server/reg_talk.py`,
  `tests/contract/test_no_destructive_calls.py`, `tests/contract/test_tool_surface.py`,
  `tests/unit/test_exapp_env_setup.py`, `scripts/check_tool_budget.py`,
  `scripts/acceptance_all_tools.py`, `appinfo/info.xml`, `pyproject.toml`, `README.md`,
  `docs/privacy.md`, `docs/spike-mail.md`

### Sekundär (MEDIUM confidence)

- `.planning/phases/08-erreichbarkeits-spike-und-tables/08-01-SUMMARY.md` und
  `docs/spike-mail.md`: die Vier-Wege-Messung aus Phase 8, plus die Korrekturen K1 und K5
  dieses Dokuments dazu
- `.planning/phases/09-talk/09-RESEARCH.md` und die Phase-9-Entscheidungen in `STATE.md`:
  die Muster, die diese Phase überträgt (Sicherheitsparameter im Client, lokale
  Statusbehandlung, Byte-Kappe ausserhalb des Textes, eingefrorene Literale, Budget-Regel)
- `https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/`: die kanonische Definition der
  Kette, für den SEC-01-Text

### Tertiär (LOW confidence, nicht verifiziert)

- Die Wertemenge von `specialRole` (A1) und das Füllverhalten von `previewText` (A2): aus dem
  Umfeld des Codes erschlossen, ohne echte IMAP-Daten nicht prüfbar
- Die Bedeutung des `unread`-Feldes im Navigationseintrag (in der Messung 0 bei aktivem
  Mail-Konto): nicht geklärt, für Phase 11 notiert
- Verhalten bei einem administrativ versteckten Navigationseintrag (A6)

---

## Metadata

**Confidence im Detail:**

- Mail-API-Routen, Parameter und Statuscodes: **HIGH**. Aus der `openapi.json` und den
  Controllern der installierten Fassung gelesen und live gemessen.
- Feldlisten: **HIGH** für die Namen (aus `jsonSerialize` und den Schemata), **MEDIUM** für
  die Werte (kein IMAP-Server).
- Filtergrammatik: **HIGH** für die Syntax und die drei Verwerfungsregeln (Parser vollständig
  gelesen), **MEDIUM** für das Ergebnisverhalten mit echten Daten.
- Zweiter Erkennungskanal: **HIGH**. In vier Zuständen gemessen, inklusive der Neustart-Falle.
- Codebasis-Anknüpfungspunkte, Budget, Gate-Entwurf: **HIGH**. Zahlen gemessen, Dateien
  gelesen.
- HTML zu Text: **HIGH** für das Parserverhalten (gemessen), **MEDIUM** für die richtige
  Kappengrösse (A3).
- SEC-01-Ablageorte und Textgates: **HIGH**. Tests gelesen.

**Recherchedatum:** 2026-08-24
**Gültig bis:** rund 30 Tage für die Codebasis-Aussagen. Die Mail-API-Aussagen gelten für
Mail 5.11.1; sie sind an eine Fassung gebunden und nicht an ein Datum. Eine andere
Mail-Fassung ist eine neue Messung, und die vier benutzten Routen sind deklariert, also ist
eine stille Änderung unwahrscheinlicher als beim internen Routensatz.
