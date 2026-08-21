# Project Research Summary

**Project:** MCP Connector fuer Nextcloud -- Milestone v1.2 "Kuratierte Breite"
**Domain:** Erweiterung einer ausgelieferten MCP-only-ExApp (Groupware-Anbindung: Chat, Tabellen, E-Mail) fuer KI-Assistenten
**Researched:** 2026-08-21
**Confidence:** HIGH insgesamt, mit zwei benannten MEDIUM-Flecken (Mail-Mindestversion, Mail-App-Erkennung live)

> Diese Datei ersetzt die v1.0-SUMMARY vom 2026-08-14 vollstaendig. Sie fasst ausschliesslich
> die vier v1.2-Recherchedateien zusammen (STACK.md, FEATURES.md, ARCHITECTURE.md,
> PITFALLS.md, alle datiert 2026-08-21). Die v1.0-Gesamtrecherche bleibt in der Git-Historie
> erreichbar (Commit `29c5940`).

## Executive Summary

v1.2 fuegt einer bereits im Store ausgelieferten, bewusst schlanken Nextcloud-MCP-ExApp drei
neue App-Familien hinzu: Talk (Chat), Tables (Tabellen) und Mail. Alle vier Recherchen kommen
unabhaengig zum selben Bild: **das ist keine neue Architektur, sondern eine dritte
Wiederholung eines etablierten Musters** (Client-Modul, Tool-Modul mit `level`-Enum,
`reg_*`-Registrierung, Capability-Gate) -- mit drei Ausnahmen, die die Roadmap explizit
adressieren muss. Erstens schreibt ein naiver Talk-"Lese"-Aufruf tatsaechlich in den
Nutzerzustand (Leseeintrag, Benachrichtigungs-Quittierung, Online-Status), unwiderruflich,
weil `DELETE` per Gate verboten ist. Zweitens hat Tables seine Zeilen-Lese-API nur in der
aelteren, nicht-OCS-Generation (v1), waehrend das Zeile-Anlegen in der neueren OCS-Generation
(v2) liegt -- ein gemischter Client ist zwingend. Drittens veroeffentlicht Mail keine
Capability, hat kein `openapi.json`, und sein einziges dokumentiert zugesagtes API-Stueck sind
vier OCS-Routen (lesen, senden, roh, Anhang); alles andere ist interne, ungetypte
Frontend-Route, die laut CSRF-Ausweg (`OCS-APIRequest`-Header) trotzdem erreichbar ist, aber
nicht zugesagt.

Der empfohlene Ansatz ist radikal minimal: **keine neue Python-Abhaengigkeit**, fuenf bis
sechs neue Tools statt der 24+ Tools, die beide direkten Wettbewerber pro Familien-Trio
anbieten, strikt lesendes Mail (keine Sende-, Verschiebe- oder Markier-Operation), Talk nur
mit einem risikoarmen Senden-Write, Tables nur mit einem risikoarmen Zeile-Anlegen-Write.
Kein Update, kein Delete, keine Schema-Aenderung irgendwo. Das haelt den Meilenstein nah an
der bestehenden Positionierung ("kuratiert schlank" gegen 100+ Tools bei der Konkurrenz) und
laesst das AST-Grep-Schreibgate im Kern unangetastet erweitern.

Das groesste, projektuebergreifende Risiko ist nicht technisch, sondern eine Sicherheits- und
Produktentscheidung: **Mail-Lesen plus Talk-Senden schliesst im selben Server zum ersten Mal
die "lethal trifecta"** (private Daten, ungefilterter fremder Inhalt, Ausgangskanal) -- die
exakte Form des EchoLeak-Vorfalls (CVE-2025-32711, CVSS 9.3) in Microsoft 365 Copilot. Alle
vier Recherchedateien flaggen das unabhaengig; PITFALLS.md und STACK.md empfehlen
uebereinstimmend, `talk_send_message` entweder auf v1.3 zu verschieben oder hinter einen
default-aus Admin-Schalter zu legen, und diese Entscheidung muss **vor** der ersten
Familienphase fallen, nicht am Ende nachgezogen werden -- sie praegt Tool-Schnitt, Store-Text
und Budget.

## Key Findings

### Recommended Stack

Der Stack aendert sich nicht: `pyproject.toml` bleibt komplett unveraendert, kein `uv add`,
kein Lock-Update. Alle drei Familien sind durchgaengig JSON ueber HTTP, laufen unter der
bestehenden AppAPI-Impersonation ohne neuen Auth-Pfad, ohne Scope-Deklaration (API-Scopes
wurden in AppAPI 3.2.0 komplett entfernt) und ohne `info.xml`-Aenderung an Routen oder
Environment-Variablen.

**Kerntechnologien (alle bereits im Projekt):**
- `httpx` (bestehend) -- einziger HTTP-Client fuer alle neun neuen Endpunkte; kein XML, kein DAV, kein IMAP direkt
- `lxml.html.fromstring(...).text_content()` (bestehend, neuer Verwendungszweck) -- HTML-Mail-Bodies zu Text reduzieren, ohne neue Abhaengigkeit (`lxml.html.clean` bewusst vermeiden, seit lxml 5.2 ausgelagert)
- `mcp[cli]` (bestehend) -- Tool-Registrierung folgt dem Deck/Notes-Muster 1:1
- neu nur in der Client-Schicht: `ocs_post` neben dem vorhandenen `ocs_get` (Talk-Senden und Tables-Create sind die ersten OCS-Schreibaufrufe des Projekts)
- Integrationstest-Ebene: GreenMail als zweiter Compose-Service fuer einen echten IMAP-Server (kein Python-Paket, nur Testinfrastruktur)

**Explizit abgelehnt:** `html2text`/`beautifulsoup4`/`markdownify` (lxml reicht), `imapclient`/`imaplib` (wuerde die Mail-App und ihre Berechtigungen umgehen), `nc_py_api` (unnoetig, neun HTTP-Aufrufe reichen), Talk-Bot-API (eigene Identitaet statt Nutzer-Impersonation, bricht das Kernversprechen).

### Expected Features

**Must have (Table Stakes):** Talk-Konversationen und -Nachrichten lesen mit garantiert
nebenwirkungsfreien Parametern (`setReadMarker=0`, `markNotificationsAsRead=0`,
`noStatusUpdate=1`, `lookIntoFuture=0`), Talk-Nachricht senden mit Vorpruefung von
`readOnly`/Permission-Bit; Tables-Tabellen, -Spalten und -Zeilen lesen (Zeilen nur ueber die
v1-App-Route, v2 hat keine Leseroute), Zeile anlegen mit Spaltentiteln statt roher
Spalten-Ids; Mail-Konten/Postfaecher/Nachrichtenliste lesen sowie eine Nachricht im Volltext
lesen (letzteres ueber die einzige offizielle OCS-Route); App-Erkennung mit Graceful
Degradation fuer alle drei Familien nach dem Notes/Deck-Muster (Mail braucht dafuer einen
zweiten Kanal, siehe Architektur).

**Should have (Differenzierung):** Mail strikt lesend (positioniert das Projekt naeher an
Googles offiziellem Gmail-MCP als an beiden Nextcloud-Wettbewerbern, die beide senden koennen);
Vertrauens-Signale (`isSenderTrusted`, `dkimValid`, `phishingDetails`) als Datenfelder statt
gefiltert durchreichen; Read-ohne-Nebenwirkung als getestete, dokumentierte Eigenschaft;
Zeile-Anlegen ueber Spaltentitel statt Ids (Nextcloud-Issue #2237 zeigt, dass sogar Menschen
das Ids-Format falsch verwenden); ein Browse-Tool mit `level`-Enum pro Familie statt
CRUD-Spiegelung (5-6 neue Tools gegen 24+ bei beiden Wettbewerbern fuer dieselben drei Apps);
Talk-Digest in `prepare_context` praktisch kostenlos, weil die Konversationsliste
`unreadMessages`/`unreadMention` schon mitliefert.

**Defer / explizit nicht bauen (v2+ oder nie):** Mail senden, Mail-Entwurf anlegen (v1.2),
Mail-Flags/Tags/Verschieben/Loeschen, Mail-Anhaenge herunterladen, Talk-Nachricht
loeschen/bearbeiten, Talk-Konversation anlegen, Talk-Reaktionen/Umfragen/Teilnehmerlisten,
`lookIntoFuture=1` (Long-Polling), eigene Suchtools pro Familie (unified_search deckt das
schon ab), Tabellen-Schema aendern/Import/Shares, Zeile aktualisieren/loeschen,
ungekappte Volltext-Dumps, credential-abhaengige `tools/list`.

### Architecture Approach

Talk und Tables passen ohne neue Mechanik in die bestehende Architektur -- je ein
Client-Modul, ein Tool-Modul, eine `reg_*`-Datei, zwei Zeilen in `capabilities.py`. Mail ist
die einzige Familie, die echte Architekturentscheidungen erzwingt: keine Capability
vorhanden, Listing laeuft ueber eine interne, nicht als API zugesagte Route. `prepare_context`
waechst am billigsten **nicht** als neues Fan-out-Bein, sondern als zwei neue Provider-Kinds in
`provider_map.PROVIDER_KINDS` plus zwei neue Buckets in `KIND_BUCKETS` -- die Suche fragt
schon heute ohne Provider-Einschraenkung und Talk-/Mail-Treffer kommen bereits an (heute als
`url`, `resolvable: false`).

**Major components:**
1. `nextcloud/clients/{talk,tables,mail}.py` (neu) -- Endpunktwissen, Pfad-Waechter, Parser-Wahl (`parse_ocs` vs. `parse_app_json`)
2. `nextcloud/capabilities.py` (geaendert) -- App-Erkennung ueber zwei Kanaele: `cloud/capabilities` fuer Talk/Tables, `core/navigation/apps` als zweiter Kanal fuer Mail
3. `tools/{talk,tables,mail}.py` (neu) -- Fachlogik, Envelope, Kappung, Degradations-Wortlaut, `require_app` als erste Zeile jeder Funktion
4. `ids.py` / `provider_map.py` / `tools/chatgpt.py::fetch` (geaendert) -- drei neue Kinds (`message`, `row`, `mail`), Fragment-Auswertung fuer Talk und Tables, Talk-Nachricht und Mail ueber `fetch` statt eigenes Tool
5. `scripts/check_tool_budget.py` (geaendert, kritisch) -- CI-Gate mit neuer Messzeile pro Anhebung, plus empfohlene Ergaenzung: Pro-Tool-Deckel (kein Tool ueber 1400 Bytes)

**Build Order laut Architekturforschung:** Phase 0 (Erreichbarkeits-Spike, blockierend, prueft ob Mail unter reiner AppAPI-Impersonation erreichbar ist) -> Tables (risikoaermste Familie, etabliert die mechanische Checkliste) -> Talk (querschneidende Aenderungen: nicht-numerische IDs, neue Kinds, erster `provider_map`-Fragment-Fall) -> Mail (profitiert von den in Talk geweiteten Naehten, sensibelste Familie, zweiter Erkennungskanal) -> `prepare_context`-Erweiterung und Budget-Endstand.

### Critical Pitfalls

1. **Talk-"Lesen" schreibt in den Nutzerzustand, unwiderruflich** -- `setReadMarker`, `markNotificationsAsRead` (Default je 1) und `noStatusUpdate` (Default 0) muessen auf jedem Talk-Request explizit auf die sichere Seite gesetzt werden, im Client, nicht im Tool, mit einem positiv behauptenden Contract-Test (ein Denylist-Gate sieht das nicht, weil es ein GET auf einen Lese-Endpunkt ist). Der Leseeintrag ist zudem fuer Dritte sichtbar (`X-Chat-Last-Common-Read`); es gibt keinen Reparaturweg, weil `DELETE` per Gate verboten ist.
2. **Mail-Lesen plus Talk-Senden schliesst die "lethal trifecta"** -- private Daten, ungefilterter fremder Inhalt (jede beliebige Mail von aussen), Ausgangskanal (Talk-Senden, potenziell an Gaeste oder foederierte Server). Empfehlung: Senden auf v1.3 verschieben, oder hinter einen default-aus Admin-Schalter, oder strukturell auf lokale, nicht-oeffentliche Konversationen beschraenken. Muss vor der ersten Familienphase entschieden werden.
3. **Mail auf die interne API bauen** -- Mails Listing-Controller tragen `#[OpenAPI(scope: OpenAPI::SCOPE_IGNORE)]`, es gibt kein `openapi.json`; die einzige zugesagte Flaeche sind vier OCS-Routen. Empfehlung: Discovery ueber den bereits genutzten Unified-Search-Provider `mail`, Inhalt ueber `GET /ocs/v2.php/apps/mail/message/{id}` -- dann ist die interne Route optional und ersetzbar statt Rueckgrat.
4. **Tables-Zeilen ohne `limit` lesen alle Zeilen** -- `limit`/`offset` sind `nullable`, ein Weglassen liefert die ganze Tabelle. Immer explizites `limit` im Client erzwingen, nicht im Tool.
5. **Budget-Gate wird einmal angehoben und schuetzt dann nichts mehr** -- drei Familien sind realistisch sechs bis neun neue Tools; ohne gemessene Neu-Verankerung (Messung plus 5-15%, aufgerundet, plus Pro-Tool-Deckel) wird das Gate wieder zur Dekoration wie am Ende von Phase 1.

## Implications for Roadmap

Alle vier Recherchedateien konvergieren unabhaengig auf dieselbe Phasenreihenfolge
(ARCHITECTURE.md schlaegt sie explizit vor, PITFALLS.md ordnet ihre zwoelf Pitfalls exakt
diesen Phasen zu). Das ist ein starkes Signal -- die folgende Struktur sollte weitgehend
direkt uebernommen werden.

### Phase 0: Milestone-Design-Entscheidung + Erreichbarkeits-Spike
**Rationale:** Zwei Fragen entscheiden die gesamte weitere Planung, und beide sind billig
vorab zu klaeren, teuer nachtraeglich zu korrigieren: (a) wird `talk_send_message` in v1.2
geschickt, verschoben oder geschaltet? (b) ist Mail unter reiner AppAPI-Impersonation
ueberhaupt erreichbar (Mail ist die erste Familie, deren Listing auf dem Pfad "nur der
`OCS-APIRequest`-Header hebt CSRF auf" laeuft, ungemessen in dieser Topologie)?
**Delivers:** Eine schriftliche Entscheidung zur lethal-trifecta-Frage (in PROJECT.md Key
Decisions) plus ein Integrationstest, der Talk/Tables/Mail-Erreichbarkeit unter Impersonation
misst.
**Avoids:** Pitfall 2 (lethal trifecta) und die Situation, dass Mail erst in der letzten
Phase als nicht erreichbar auffaellt.

### Phase 1: Tables
**Rationale:** Die risikoaermste, mechanisch einfachste Familie (numerische IDs, beide Parser
schon vorhanden, kein Eingriff in `ids.py`/`provider_map`/`fetch`/`context.py` noetig).
Etabliert die komplette Checkliste (Capability-Feld, `EXPECTED_TOOLS`, `CREATE_TOOLS`, README
in drei Sprachen, `info.xml`, Budget-Messzeile) einmal an der Familie ohne Zusatzrisiko.
**Delivers:** `tables_browse` (Level tables/columns/rows), `tables_create_row` mit
Spaltentiteln statt Ids.
**Addresses:** Table-Stakes-Features Tables aus FEATURES.md.
**Avoids:** Pitfall 7b (ungekappte Zeilen), Pitfall 12b (Duplikate durch Retry).

### Phase 2: Talk
**Rationale:** Hier sitzen die querschneidenden Aenderungen (nicht-numerische Pfad-IDs, drei
neue `ids.py`-Kinds, erster `provider_map`-Fragment-Fall, erster neuer `fetch`-Case). Nach
dieser Phase sind alle Naehte geweitet, die Mail dann nur noch benutzt.
**Delivers:** `talk_browse` (Level conversations/messages) garantiert nebenwirkungsfrei,
`talk_send_message` (falls Phase 0 es freigibt) mit Permission-Vorpruefung.
**Uses:** `ocs_post`-Erweiterung aus STACK.md.
**Avoids:** Pitfall 1 (Lesen schreibt Zustand), Pitfall 6 (Rich Object Strings/Platzhalter), Pitfall 7a (Pagination im Header).

### Phase 3: Mail
**Rationale:** Sensibelste Familie inhaltlich, einzige ohne Capability, einzige mit
`/message/send` im eigenen OCS-Bestand (muss aktiv ausgeschlossen werden), profitiert am
meisten von den in Phase 2 geweiteten Naehten, Erreichbarkeit erst durch Phase 0 geklaert.
**Delivers:** `mail_browse` (Level accounts/mailboxes/messages), `fetch`-Erweiterung um
`mail:<databaseId>` statt eigenem Lesetool.
**Implements:** Zweiter Capability-Kanal (`core/navigation/apps`) aus ARCHITECTURE.md.
**Avoids:** Pitfall 3 (interne API als Rueckgrat), Pitfall 10 (Brute-Force durch ID-Raten), Pitfall 11 (Marker-Filter zu schwach fuer Mail-HTML/Unicode-Smuggling).

### Phase 4: prepare_context-Erweiterung, Budget-Endstand, Aussenwirkung
**Rationale:** `KIND_BUCKETS` und `EXCERPT_KINDS` sind erst sinnvoll zu entscheiden, wenn
beide neuen Kinds existieren und `fetch` sie aufloesen kann. Hier auch die
Budget-Neuverankerung und alle mechanischen Nachzieharbeiten (README x3, `info.xml`, `docs/`).
**Delivers:** Talk-Digest in `prepare_context`, finale Budget-Zahl mit Messzeile,
aktualisierte Store-Texte und Dokumentation in allen drei Sprachen.
**Avoids:** Pitfall 4 (unbudgetierte Fan-out-Latenz), Pitfall 5 (Budget-Gate ohne Schutzwirkung).

### Phase Ordering Rationale

- Reihenfolge folgt Risiko: Erreichbarkeit und die Sicherheitsentscheidung zuerst gemessen,
  dann die risikoaermste Familie, dann die querschneidende, dann die sensibelste.
- Tables vor Talk, obwohl Talk die "attraktivere" Familie ist: die mechanische Checkliste
  (fuenf eingefrorene Testliteralen, drei READMEs, `info.xml`) einmal an einer risikolosen
  Familie zu lernen macht die beiden schwierigen Phasen kuerzer.
- `prepare_context` bewusst als eigene, letzte Phase statt Anhaengsel an jede Familienphase,
  weil die Bucket-Entscheidung (welche Kinds bekommen einen Auszug) beide neuen Kinds
  gleichzeitig sehen muss, um konsistent zu sein.

### Research Flags

Braucht tiefere Recherche waehrend der Planung (`--research-phase`):
- **Phase 0 (Spike):** Mail-Erreichbarkeit unter AppAPI-Impersonation ist MEDIUM-Konfidenz, nur aus Quellcode gelesen, nie in dieser Topologie gemessen.
- **Phase 3 (Mail):** Mail-Mindestversion fuer die OCS-`messageApi`-Routen ist nicht sauber datierbar (kein Capability-Eintrag, kein Changelog-Treffer); die Zellwert-Formate je `column_types` bei Tables-Create sind ebenfalls unklar (wahrscheinlichste Quelle fuer einen 400).

Standardmuster, wahrscheinlich ohne Extra-Recherche planbar:
- **Phase 1 (Tables):** Endpunkte, Parameter und Parser sind HIGH-Konfidenz, direkt aus Quellcode und `openapi.json` verifiziert.
- **Phase 2 (Talk):** API-Version, Parameter-Defaults und Capability-Struktur sind HIGH-Konfidenz aus offizieller Doku plus Quellcode.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Endpunkte, Parameter und Auth-Mechanismus gegen den Quelltext von spreed/tables/mail/server (stable32-34) gelesen; MEDIUM nur fuer Mail-Mindestversion |
| Features | HIGH fuer API-Lage und Wettbewerb (Quellcode und Tool-Listen direkt gelesen), MEDIUM fuer Nutzererwartung (Vendor-MCPs als Proxy, keine eigenen Store-Rueckmeldungen) |
| Architecture | HIGH fuer Talk/Tables und Codebasis-Integrationspunkte (live gemessen, z. B. Budget), MEDIUM fuer Mail (Erreichbarkeit unter Impersonation nicht live belegt) |
| Pitfalls | HIGH fuer API-Fakten und Code-Interaktionen mit diesem Repo, HIGH fuer die Injection-Klasse (oeffentlicher Vorfall), MEDIUM fuer die konkrete Mitigations-Rangfolge (Urteil, keine Messung) |

**Overall confidence:** HIGH

### Gaps to Address

- **Mail-Erreichbarkeit unter reiner AppAPI-Impersonation** ist der einzige echte Blocker-Kandidat: ungemessen in dieser Topologie. Muss in Phase 0 als Spike geklaert werden, bevor Mail verplant wird.
- **Lethal-Trifecta-Entscheidung fuer `talk_send_message`** ist keine Recherchelluecke, sondern eine offene Produktentscheidung, die vor Phase 1 im PROJECT.md festgehalten werden muss (Optionen: verschieben auf v1.3, default-aus Admin-Schalter, strukturelle Empfaenger-Einschraenkung).
- **Mail-Mindestversion** fuer die OCS-`messageApi`-Routen laesst sich nicht sauber datieren; Empfehlung ist, nicht auf eine Version zu gaten, sondern bei 404/HTML degradiert zu antworten.
- **Tables-Zellwert-Formate je `column_types`** beim Zeile-Anlegen sind nicht vollstaendig dokumentiert; das ist der wahrscheinlichste Ort fuer einen 400 in der Tables-Phase und verdient eine kurze Recherche innerhalb der Phase.
- **`/core/navigation/apps` als Mail-Erkennungsweg** ist im Quellcode verifiziert, aber die Antwortform nie gegen eine laufende Instanz geprueft; Gegenprobe ueber die Unified-Search-Provider-Liste ist der billige Ausweg, falls eine Instanz Mails Navigationseintrag ausblendet.

## Sources

### Primary (HIGH confidence)
- nextcloud/server, stable32/33/34/master -- `Request::passesCSRFCheck()`, `SecurityMiddleware`, `NavigationController` (der `OCS-APIRequest`-CSRF-Ausweg, in vier Zweigen identisch)
- nextcloud-talk.readthedocs.io -- Conversation v4, Chat v1, Parameter-Defaults, Statuscodes
- nextcloud/spreed, nextcloud/tables, nextcloud/mail (main-Zweige) -- Controller, Capabilities, Search-Provider, Routen direkt gelesen
- nextcloud/tables `openapi.json` -- vollstaendige Routenliste, Abwesenheit einer v2-Zeilen-Leseroute
- nextcloud/app_api `CHANGELOG.md` -- Entfernung der API-Scopes (3.2.0)
- Eigener Code, live gemessen: `scripts/check_tool_budget.py` (11268/12500 Bytes, 16 Tools), `tests/contract/test_tool_surface.py`, `tests/integration/test_exapp_dav_matrix.py`
- EchoLeak / CVE-2025-32711 (CVSS 9.3) -- Beleg fuer die lethal-trifecta-Gefahrenklasse

### Secondary (MEDIUM confidence)
- github.com/cbcoutinho/nextcloud-mcp-server (332 Sterne) -- unabhaengige Bestaetigung des Mail-CSRF-Mechanismus gegen eine laufende Instanz, gemessene Warnungen zu v2-Scheme-Route und OCS-Anhangsroute, Field-Evidence zu Versions-Drift-Bruechen (#728, #730)
- nextcloud/context_agent (offiziell) -- Tool-Umfang und Adressierungsmuster als Negativbeispiel
- developers.google.com Gmail-MCP, docs.slack.dev Slack-MCP -- Referenzpunkte fuer Scope-Disziplin bei Vendor-MCPs
- nextcloud/tables Issue #2237 -- Row-Create-Format-Verwirrung auch bei Menschen

### Tertiary (LOW confidence)
- keine -- alle als LOW eingestuften Einzelpunkte wurden in den vier Recherchedateien bereits als MEDIUM mit expliziter Pruefempfehlung markiert, nicht als LOW belassen

---
*Research completed: 2026-08-21*
*Ready for roadmap: yes*
