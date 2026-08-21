# Phase 9: Talk, Recherche

**Recherchiert:** 2026-08-21
**Domäne:** Nextcloud Talk (spreed) als lesende Familie mit genau einem Schreibpfad, plus der sechste Admin-Wert der Declarative-Settings-Kette
**Konfidenz:** HIGH (alle Routen, Parameter, Statuscodes, Berechtigungs- und Sichtbarkeitsregeln gegen den Tag `v24.0.4` gelesen, also gegen genau die Fassung, die auf NC 34 landet, und gegen die mitgelieferte `openapi.json` gegengeprüft; Codebasis-Anknüpfungspunkte gelesen, Budget und Instanzstand live gemessen)

> Diese Datei baut auf der Meilenstein-Kernrecherche in `.planning/research/` und auf
> `08-RESEARCH.md` auf und wiederholt sie nicht. Sie enthält (a) die Tag-genaue Talk-API-Referenz,
> (b) **fünfzehn Korrekturen**, von denen zwei die Phase blockieren, wenn sie nicht im Plan
> stehen, (c) die vollständige Kette des neuen Admin-Schalters durch das eigene Repo, und
> (d) die mechanische Checkliste mit exakten Anknüpfungspunkten. Der Korrekturabschnitt ist
> der wichtigste Teil dieser Datei.

## Zusammenfassung

Talk ist mechanisch die dritte Wiederholung des etablierten Musters (Client-Modul, Tool-Modul
mit `level`-Enum, `reg_*`-Datei, Capability-Feld), aber inhaltlich die erste Familie, deren
**Lese**-Route per Voreinstellung in den Nutzerzustand schreibt und deren **Schreib**-Route mit
einem Statuscode antwortet, den der gemeinsame OCS-Parser dieses Projekts heute als Fehler
behandelt. Zwei Punkte sind deshalb blockierend und müssen im Plan stehen, nicht im
Nachhinein auffallen: `POST /chat/{token}` antwortet **201**, und `parse_ocs` lehnt heute alles
ab, was nicht 100 oder 200 ist; ein leerer oder ausgelesener Verlauf antwortet **304**, und
`_check_transport` verwandelt jedes 3xx in "Nextcloud hat mit einer Weiterleitung geantwortet,
prüfe die Basis-URL". Beide Fälle treten beim ersten echten Aufruf auf, nicht in einem
Randfall: die erste gesendete Nachricht und jede frische Konversation.

Die grösste inhaltliche Falle ist zum dritten Mal in diesem Projekt dieselbe Klasse:
ein Berechtigungsfeld, das eine andere Frage beantwortet als die gestellte. Nach
`canCreateBoards` (Phase 1) und `onSharePermissions` (Phase 8, K5) heisst sie hier
`attendeePermissions`. Dieses Feld trägt die **rohen** Rechte des Teilnehmers und ist bei
praktisch jedem normalen Nutzer `0` (`PERMISSIONS_DEFAULT`), weil Rechte in Talk über eine
Fallback-Kette (Teilnehmer, dann Konversation, dann Instanz) aufgelöst werden und Moderatoren
immer alles dürfen. Das aufgelöste Ergebnis liegt im Feld **`permissions`** derselben Antwort,
und genau darauf prüft Talks eigene Middleware. Eine wörtliche Umsetzung von "Permission-Bit
128 an `attendeePermissions` prüfen" würde also nahezu jeden Nutzer in jeder Konversation
abweisen.

Der dritte Kern der Phase ist der Admin-Schalter, und er ist **keine** reine Kopie der
bestehenden fünf Werte. Die fünf bestehenden werden genau einmal beim Prozessstart gelesen und
als Umgebungs-Mapping an `build_exapp_app` gegeben; sie landen nie in `os.environ`, und kein
Werkzeug dieses Servers liest heute überhaupt Konfiguration zur Laufzeit. Ein Werkzeug, das den
Schalter beim Aufruf sehen muss, braucht deshalb eine bewusste Entscheidung über den Leseweg,
und die drei denkbaren Wege haben sehr unterschiedliche Preise (Abschnitt "Der Admin-Schalter").

**Primärempfehlung:** Zwei Werkzeuge (`talk_browse` mit `level="conversations"|"messages"`,
`talk_send` als CREATE_ONLY). Der Lesepfad setzt alle vier Sicherheitsparameter im Client,
nicht im Tool, und der Nachweis von Erfolgskriterium 3 besteht aus zwei Schichten: einem
positiv behauptenden Unit-Test auf die **gebaute URL** und einer Live-Messung von
`lastReadMessage`, `unreadMessages` und `lastCommonReadMessage` vor und nach dem Lesen. Die
Vorprüfung von `talk_send` läuft über die **Konversationsliste**, nie über
`GET /room/{token}` mit einem Modell-Token: ein unbekanntes Token dort registriert einen
Brute-Force-Versuch auf die IP der ExApp, also für alle Nutzer der Instanz gemeinsam.

## Phase Requirements

| ID | Beschreibung (aus REQUIREMENTS.md) | Research Support |
|----|------------------------------------|------------------|
| TALK-01 | Konversationen listen (Token, Name, Typ, Ungelesen-/Erwähnungs-Zähler, letzte Aktivität), zur Seite gelegte draussen, Kappe 50, `noStatusUpdate=1` | Route, Parameter und vollständige Feldliste gegen v24.0.4 plus `openapi.json` verifiziert; Korrektur T5 (es gibt **keinen** Server-Filter und **keine** Server-Sortierung, beides muss im Tool passieren), Korrektur T6 (was `noStatusUpdate` in dieser Fassung tatsächlich tut), Korrektur T12 (Ungelesen-Zähler 1 bei nie geöffneter Konversation) |
| TALK-02 | Verlauf lesen, nachweislich nebenwirkungsfrei (`setReadMarker=0`, `markNotificationsAsRead=0`, `noStatusUpdate=1`, `lookIntoFuture=0`), Platzhalter aufgelöst, Systemnachrichten draussen, Default 20 / Max 50, Byte-Kappe, Paginierung über `lastKnownMessageId` | Parameter-Defaults und Wirkungsbedingungen zeilengenau gelesen (T6); Korrektur T2 (304 blockierend), T7 (`lookIntoFuture` ist Pflichtparameter), T8 (Paginierung braucht den Antwort-Header, nicht die Nachrichten-Ids); `messageParameters`-Auflösung aus `UserMention` und `Message::toArray` verifiziert |
| TALK-03 | `talk_send` (CREATE_ONLY), Token nur aus `talk_browse`, Vorprüfung `readOnly == 0` und Bit 128, `@all`/`@here` abgelehnt, Kappe 32.000 Zeichen, kein `silent`-, Edit- oder Delete-Pfad | Korrektur T1 (201), T3 (`permissions` statt `attendeePermissions`), T4 (Typ 4 ist immer schreibgeschützt), T9 (Token-Regex), T10 (Brute-Force), T11 (`@here` ist keine Talk-Erwähnung, und ein naives Teilstring-Verbot trifft `@allan`); `MAX_CHAT_LENGTH = 32000` plus Capability `config.chat.max-length` verifiziert |
| TALK-04 | Neuer Admin-Schalter im Muster der fünf OAuth-Werte, an per Default, Ende-zu-Ende getestet (Form, Overlay-Lesepfad, Wirkung am Tool) | Vollständige Kette im eigenen Repo gelesen (`admin_settings.py`, `config_values.py`, `entry_exapp._resolved_env`, `oauth/registry._switch`); Korrektur T15 (das Overlay erreicht `os.environ` nicht, und kein Tool liest heute Konfiguration) mit drei Optionen und einer Empfehlung |

## Projekt-Constraints (aus CLAUDE.md und globalen Regeln)

Unverändert gegenüber Phase 8, hier nur die für diese Phase wirksamen Punkte:

- **Code und README auf Englisch**, Projektkommunikation auf Deutsch. Keine Em-Dashes, echte
  Umlaute in deutschen Texten, keine Emojis.
- **Security-Constraint aus PROJECT.md:** Der MCP darf nie mehr sehen als der angemeldete
  Nutzer; keine destruktiven Writes.
- **Python 3.13, `uv` als Toolchain** (jedes Kommando als `uv run ...`), offizielles MCP-SDK.
- **`ruff check .`, `ruff format --check .`, `pyright`, `vulture` (volle Konfidenz, annotierte
  Whitelist)** über das ganze Repo vor jedem Push.
- **Nach jedem Edit committen**, keine Claude-Attribution, GitHub-Push auf `master` erlaubt.
- **Tests decken alle Pfade ab:** Fehler, Edge, Negativ, `no_data`.
- **Doku dreisprachig mitziehen** (README EN/DE/FR, `docs/`, `CHANGELOG.md`).
- **Vokabular-Gate:** `FORBIDDEN_VOCABULARY = "archiv"` gilt laut
  `tests/unit/test_exapp_env_setup.py` **nur für `appinfo/info.xml`** (Manifest-Text, alle drei
  Sprachen, casefold). Der englische Feldname `isArchived` im Code ist unberührt, aber die
  deutsche und die französische Store-Beschreibung dürfen zur Seite gelegte Konversationen
  nicht mit diesem Wort benennen. Empfehlung: sie im Store-Text gar nicht erwähnen.
- **Store-Beschreibung-Regel (Owner, 2026-08-21):** eine neue Familie gehört in die drei
  `<description>`-Blöcke von `appinfo/info.xml` (Format-Regeln im Datei-Kommentar: Leerzeile
  als Absatztrenner, nur die sanitisierte Teilmenge an Markup, kein Backtick, keine Tabelle).
  `<version>` und `<image-tag>` bleiben unangetastet.
- **GSD-Workflow:** Datei-Änderungen nur innerhalb eines GSD-Kommandos.

Kein `.claude/skills/`- oder `.agents/skills/`-Verzeichnis vorhanden.

## Architektonische Verantwortungs-Zuordnung

| Fähigkeit | Primäre Schicht | Sekundäre Schicht | Begründung |
|-----------|-----------------|-------------------|------------|
| Endpunktwissen Talk (URL-Bau, API-Versionen v4 und v1, Token-Wächter) | `nextcloud/clients/talk.py` (neu) | `nextcloud/clients/ocs.py` (201 im Erfolgsraum) | Eine Familie, ein Modul; die zwei API-Versionen sind eine Eigenschaft der App und dürfen nicht beim Aufrufer landen |
| Die vier Sicherheitsparameter des Lesens | **Client** | Unit-Test auf die gebaute URL | Pitfall 1 der Kernrecherche: ein Tool-Parameter wäre vergessbar, und ein Denylist-Gate sieht ein GET auf einen Lese-Endpunkt nicht |
| 304 und der `X-Chat-Last-Given`-Header | Client | Tool (`no_data`, `truncated`) | Beide sind Transporttatsachen; das Tool darf nicht wissen, dass "leer" hier ein Statuscode ist |
| Kappen, Projektion, Platzhalter-Auflösung, Systemnachrichten-Filter, Fehlersätze | `tools/talk.py` (neu) | `tools/marks.py` (fremder Text) | Fachlogik und Wortlaut gehören ins Tool |
| Sende-Vorprüfung (readOnly, Typ, Bit 128, `@all`, Länge) | `tools/talk.py` | Talks `RequirePermission`- und `RequireReadWriteConversation`-Middleware als letzte Instanz | Muster 4 aus Phase 8: das Objekt entscheidet, unsere Prüfung ist nur die bessere Fehlermeldung |
| App-Erkennung `spreed` | `nextcloud/capabilities.py` (geändert) | `tools/talk.py` (`require_app` als erste Zeile) | Ein gecachter Request statt eines 404 auf einer HTML-Seite |
| Schema, Annotationen, Enum-Level | `server/reg_talk.py` (neu) | `scripts/check_tool_budget.py` (Gate) | Eine Registrierungsdatei je Familie, damit parallele Pläne keine gemeinsame Datei anfassen |
| Instanzweiter Schalter, Formularseite | `exapp/admin_settings.py` plus `exapp/ui/strings.py` (geändert) | `exapp/config_values.py` (Lesepfad, sechster Schlüssel) | Die Kette existiert; sie wird erweitert, nicht neu erfunden |
| Instanzweiter Schalter, Wirkung am Werkzeug | `config.py` (neuer Leser) plus `entry_exapp.py` (Übergabe) | `tools/talk.py` (erste Zeile von `send`) | Der einzige Punkt der Phase ohne Vorbild in der Codebasis, siehe T15 |
| Live-Nachweis Nebenwirkungsfreiheit | `tests/integration/test_talk_roundtrip.py` (neu) | `docs/` (Messwerte) | Eine Behauptung über Nebenwirkungen ist erst mit einer Messung vor und nach dem Lesen ein Nachweis |

## Standard Stack

### Kern

| Baustein | Version | Zweck | Warum Standard |
|----------|---------|-------|----------------|
| `httpx` | 0.28.x (bereits im Projekt) | Einziger HTTP-Client für alle Talk-Aufrufe | Beide Talk-Routen sind JSON über OCS; kein XML, kein DAV, kein Signaling |
| `mcp[cli]` | >=2.0,<3 (bereits) | Tool-Registrierung | `reg_talk.py` folgt `reg_tables.py` eins zu eins |
| `pytest` + `respx` | bereits im Dev-Group | Unit-Tests mit gemocktem httpx | Vorbild `tests/unit/test_tables_client.py` |
| Nextcloud Talk (`spreed`) | **24.0.4** (2026-08-13) | Zieldomäne | Aktuellste Store-Fassung für NC 34, Plattform-Spec `>=34.0.0 <35.0.0` [VERIFIED: apps.nextcloud.com/api/v1/platform/34.0.0/apps.json, heute abgefragt] |

**Keine neue Python-Abhängigkeit.** `pyproject.toml` und `uv.lock` bleiben in dieser Phase
unangetastet. Es gibt kein `uv add`, kein `npm install`, kein `pip install`.

### Alternativen, geprüft und verworfen

| Statt | Möglich wäre | Abwägung |
|-------|--------------|----------|
| Vorprüfung über die Konversationsliste (`GET /room`) | `GET /room/{token}` für genau die eine Konversation | Die Einzelroute registriert bei einem unbekannten Token einen Brute-Force-Versuch auf die IP dieses Containers, also für alle Nutzer gemeinsam (T10). Die Liste kostet denselben einen Request, und ein erfundenes Token wird zu unserem eigenen Fehlersatz statt zu einer Instanz-Sperre |
| `includeLastMessage=false` in der Liste für `talk_send` | Voreinstellung `true` lassen | Die Vorprüfung braucht die letzte Nachricht nicht, und sie ist der grösste Einzelposten der Antwort. Für `talk_browse(level="conversations")` bleibt `true` sinnvoll, weil CTX-01 in Phase 11 genau diese Vorschau braucht |
| Paginierung über den Header `X-Chat-Last-Given` | Kleinste zurückgegebene Nachrichten-Id | Ein Fenster kann 200 mit **leerer** Liste und gesetztem Header sein (alle Nachrichten unsichtbar oder abgelaufen). Die Id-Variante würde dort still aufhören und älteren Verlauf verschweigen (T8) |
| Zwei Werkzeuge (`talk_browse`, `talk_send`) | Drei (eigenes `talk_read_message`) | Eine einzelne Nachricht adressierbar zu machen ist TOOL-16 in Phase 11 und läuft dort über `fetch`, nicht über ein eigenes Werkzeug; das Budget hat für ein drittes Talk-Werkzeug keinen Platz |
| `talk_browse(level="messages")` in der App-Reihenfolge (neueste zuerst) | Auf chronologisch aufsteigend drehen | Die App liefert `desc`, und die Paginierung läuft rückwärts in die Vergangenheit. Ein Umdrehen im Tool erzeugt eine Antwort, deren Reihenfolge der Bedeutung von `next` widerspricht. Empfehlung: Reihenfolge lassen und in der Tool-Beschreibung benennen |
| Systemnachrichten per `messageType == "system"` filtern | Über `systemMessage != ""` | Beide Felder tragen dieselbe Aussage (`Message::toArray`), aber `messageType` ist die Enumeration und deckt zusätzlich `comment_deleted` und `reaction` mit ab. Empfehlung: auf einer Positivliste filtern, nicht auf einer Negativliste (siehe Muster 6) |

## Package Legitimacy Audit

**Nicht anwendbar: es wird kein Sprachpaket installiert.** `pyproject.toml` und `uv.lock`
bleiben unverändert.

Das einzige neue externe Artefakt ist eine Nextcloud-App aus dem offiziellen Store:

| Artefakt | Quelle | Verifikation | Disposition |
|----------|--------|--------------|-------------|
| Nextcloud-App `spreed` 24.0.4 | apps.nextcloud.com (offizieller Store) | Store-API-Abfrage heute: Plattform-Spec `>=34.0.0 <35.0.0`, veröffentlicht 2026-08-13; Quellcode auf github.com/nextcloud/spreed Tag `v24.0.4` gelesen (Tag-Objekt `fcfa1058` über die GitHub-API bestätigt) | Freigegeben |

`occ app:install` funktioniert auf beiden Topologien: der Store ist aus den Containern
erreichbar (in Phase 8 mit HTTP 200 verifiziert, seither unverändert), und `tables` und `mail`
sind auf diesem Weg installiert worden.

## Korrekturen an der Kernrecherche und an der Roadmap

Diese fünfzehn Punkte sind gegen `spreed` **v24.0.4** und gegen die eigene Codebasis geprüft.
Wo sie `.planning/research/*` oder dem Wortlaut der ROADMAP widersprechen, gilt diese Datei.
**T1 und T2 sind blockierend:** ohne sie scheitert der erste echte Aufruf beider Werkzeuge.

**T1. `POST /chat/{token}` antwortet 201, und `parse_ocs` lehnt 201 heute ab.** Die
Dokumentation des Controllers listet als Erfolg ausschliesslich `201: Message sent
successfully`, und die `openapi.json` der App nennt für diese Route die Antworten
`201, 400, 403, 404, 413, 429`. In OCS v2 ist `ocs.meta.statuscode` der rohe Status
(`V2Response::render` schreibt `$this->getOCSStatus()`), also ebenfalls 201.
`clients/ocs.py` hat `_OK_STATUS = frozenset({100, 200})`, und `parse_ocs` wirft für alles
andere. Eine erfolgreich gesendete Nachricht käme also als "Nextcloud answered ... with an
unexpected status 201" beim Modell an, und das Modell würde vermutlich erneut senden. Das ist
der Gegenfall zu Phase 8, wo `createRow` mit 200 antwortete (Falle 4 dort).
**Empfehlung:** `_OK_STATUS` auf `{100, 200, 201}` erweitern, mit einer Kommentarzeile, die
sagt warum, plus einem Unit-Test, der einen 201-Envelope durch `parse_ocs` schickt. Risiko
gering: heute liefert keine benutzte Route 201, die Erweiterung kann also keine bestehende
Prüfung umdrehen. Die Alternative (201 nur im Talk-Client behandeln) würde die
Envelope-Auswertung ein zweites Mal implementieren.
[VERIFIED: nextcloud/spreed v24.0.4 lib/Controller/ChatController.php Zeilen 356-376 und
openapi.json; nextcloud/server stable34 lib/private/AppFramework/OCS/V2Response.php; eigene
Datei src/mcp_connector/nextcloud/clients/ocs.py Zeile 50]

**T2. Ein leerer Verlauf antwortet 304, und `_check_transport` nennt jedes 3xx eine
Weiterleitung.** `prepareCommentsAsDataResponse` gibt bei leerer Kommentarliste
`new DataResponse(null, Http::STATUS_NOT_MODIFIED)` zurück; die `openapi.json` listet für die
Leseroute `200, 304, 404`. Unser `_check_transport` behandelt `300 <= status < 400` als
Redirect und antwortet mit `config.REDIRECT_HINT`, also mit "prüfe die Basis-URL". Betroffen
ist nicht ein Randfall, sondern (a) jede frische Konversation, (b) jede Konversation, deren
Verlauf durchpaginiert ist, und (c) der Fall aus T12 (Ungelesen-Zähler 1, aber keine
Nachricht). **Empfehlung:** im Talk-Client **vor** `parse_ocs` auf `304` prüfen und eine leere
Liste zurückgeben; das Tool macht daraus die etablierte `no_data`-Antwort mit `count: 0`. Der
gemeinsame Parser bleibt unberührt, weil 304 nur an dieser einen Route eine Bedeutung hat.
[VERIFIED: lib/Controller/ChatController.php Zeilen 1096-1110 und openapi.json; eigene Datei
clients/ocs.py Zeilen 196-203]

**T3. Für das Chat-Recht zählt `permissions`, nicht `attendeePermissions`.** Die
Konversationsantwort trägt vier Rechte-Felder: `permissions`, `attendeePermissions`,
`callPermissions` und `defaultPermissions`. `attendeePermissions` ist der rohe Wert des
Teilnehmers und bei jedem Nutzer, für den nie ein Sonderrecht gesetzt wurde, `0`
(`Attendee::PERMISSIONS_DEFAULT`). `permissions` ist das Ergebnis von
`Participant::getPermissions()`: erst die Fallback-Kette (Teilnehmer, dann
`Room::defaultPermissions`, dann `Config::getDefaultPermissions()`), und danach überschreibt
ein Moderator alles mit `PERMISSIONS_MAX_DEFAULT`. Talks eigene Middleware prüft
`$participant->getPermissions() & Attendee::PERMISSIONS_CHAT`, also genau dieses Feld. Der
Instanz-Default ist `PERMISSIONS_MAX_DEFAULT & ~PERMISSIONS_LOBBY_IGNORE` und enthält Bit 128.
**Korrekte Vorprüfung:** `bool(permissions & 128)`, wobei `permissions` aus der
Konversationsantwort kommt. Ein wörtliches `attendeePermissions & 128` wäre falsch negativ für
fast jeden Nutzer in fast jeder Konversation, und ein Test mit einer selbst angelegten
Konversation wäre rot, ohne dass die Ursache am Feldnamen sichtbar wird. Das ist dieselbe Klasse
wie `canCreateBoards` (Phase 1) und `onSharePermissions` (Phase 8, K5), und die Begründung
gehört genauso in einen Docstring.
[VERIFIED: lib/Participant.php Zeilen 119-140, lib/Model/Attendee.php Zeilen 98-118,
lib/Config.php Zeilen 293-302, lib/Middleware/InjectionMiddleware.php Zeilen 382-397,
lib/Service/RoomFormatter.php Zeilen 240-243]

**T4. `readOnly == 0` genügt als Prüfung nicht: Typ 4 ist immer schreibgeschützt, und jeder
Nutzer hat so eine Konversation.** `checkReadOnlyState` wirft nicht nur bei
`Room::READ_ONLY` (`readOnly == 1`), sondern zusätzlich bei
`$room->getType() === Room::TYPE_CHANGELOG`, also `type == 4`. Das ist die automatisch
angelegte "Talk updates"-Konversation, die in der Liste jedes Nutzers steht, oft an prominenter
Stelle, und die ein Modell auf die Aufforderung "sende eine Nachricht" durchaus wählt. Die
Vorprüfung muss also `readOnly` **und** `type` lesen. Nebenbei: `type == 6`
(`TYPE_NOTE_TO_SELF`) ist beschreibbar und darf nicht mitgesperrt werden.
[VERIFIED: lib/Middleware/InjectionMiddleware.php Zeilen 354-363, lib/Room.php Zeilen 26-32
und 60-61]

**T5. Es gibt keinen Server-Filter für zur Seite gelegte Konversationen und keine
Server-Sortierung.** Die `openapi.json` nennt für `GET /room` genau vier Query-Parameter:
`noStatusUpdate`, `includeStatus`, `modifiedSince`, `includeLastMessage`. Ein Filter auf
`isArchived` existiert nicht, das Feld steht pro Teilnehmer in der Antwort
(`$attendee->isArchived()`), also muss der Filter im Tool laufen, genau wie Deck es mit
`archived` und Tables mit `archived` schon tun. Zweiter, gefährlicherer Teil: `getRoomsForUser`
baut seine Abfrage **ohne `ORDER BY`**, die Reihenfolge ist damit Datenbanksache (praktisch die
Anlegereihenfolge). Eine Kappe auf 50 ohne eigene Sortierung würde also nicht die 50 neuesten
Konversationen liefern, sondern 50 beliebige, und die Kappe wäre eine stille Falschaussage.
**Empfehlung:** nach `lastActivity` absteigend sortieren, dann filtern, dann kappen, und die
Kappung wie überall benennen.
[VERIFIED: openapi.json Pfad `/ocs/v2.php/apps/spreed/api/{apiVersion}/room`;
lib/Service/RoomFormatter.php Zeile 251; lib/Manager.php `getRoomsForActor`]

**T6. Die vier Sicherheitsparameter sind in dieser Fassung Versicherung, nicht Ursache, und das
ändert die Beweisführung für Erfolgskriterium 3.** Zeilengenau gelesen:

- `setReadMarker` wirkt nur innerhalb von
  `if ($lookIntoFuture && $setReadMarker === 1 && $lastKnownMessageId > $attendee->getLastReadMessage())`.
  Mit `lookIntoFuture=0` schreibt die Route den Lesemarker also gar nicht, unabhängig vom
  Parameter.
- `markNotificationsAsRead` wird ausschliesslich an `waitForNewMessages` übergeben, also nur im
  `lookIntoFuture=1`-Zweig; `getHistory` bekommt es nicht.
- `noStatusUpdate` wirkt nur, wenn eine Talk-**Session** existiert **und** der User-Agent
  `USER_AGENT_TALK_ANDROID` oder `USER_AGENT_TALK_IOS` ist. Beides trifft für diesen Server nie
  zu. Dasselbe gilt für `getRooms`: dort hängt der Status-Bump ebenfalls an der
  Mobil-App-Erkennung.
- Der Kommentarblock über der Lesemarker-Logik nennt sie ausdrücklich vorläufig ("only setting
  it automatically here for old clients and the web UI, until it can be fixed in Vue").

Konsequenz: Die Parameter bleiben **Pflicht** (die Logik ist als temporär markiert und kann in
Talk 25 anders aussehen, und der Kernrecherche-Befund "Lesen schreibt Zustand" ist für
`lookIntoFuture=1` weiterhin wahr), aber ein Test, der nur behauptet "wir setzen sie", beweist
Erfolgskriterium 3 **nicht**. Der Beweis besteht aus zwei Schichten:
(1) positiv behauptender Unit-Test auf die gebaute URL (alle vier Parameter mit dem sicheren
Wert), (2) Live-Messung: `lastReadMessage`, `unreadMessages`, `unreadMention` und
`lastCommonReadMessage` derselben Konversation aus `GET /room` vor und nach dem Verlauf-Lesen
vergleichen, plus die Gegenprobe, dass keine Benachrichtigung quittiert wurde. Schicht 2 ist
die Aussage, die das Kriterium wörtlich verlangt ("nach einem Lesevorgang ist nachweislich
nichts verändert").
[VERIFIED: lib/Controller/ChatController.php Zeilen 908-956, lib/Controller/RoomController.php
Zeilen 246-261]

**T7. `lookIntoFuture` ist ein Pflicht-Query-Parameter ohne Default.** Die
`openapi.json` markiert ihn `required: true` (Enum `[0, 1]`), und die PHP-Signatur hat für ihn
im Gegensatz zu allen anderen Parametern keinen Vorgabewert. Ein Aufruf ohne ihn ist kein
"Default 0", sondern ein Fehler der App-Framework-Schicht. Der Client muss ihn also immer
mitsenden, und der eingefrorene URL-Test sollte ihn wörtlich enthalten.
[VERIFIED: openapi.json, `lookIntoFuture query req=True`; ChatController::receiveMessages
Signatur]

**T8. Die Paginierung des Verlaufs läuft über den Antwort-Header, und ein leeres Fenster mit
200 ist ein echter Fall.** `X-Chat-Last-Given` trägt `end($comments)`, also die Id der
**ältesten** zurückgegebenen Nachricht (die Route liefert `desc`). Dieser Wert ist der
`lastKnownMessageId` der nächsten, älteren Seite. Wichtiger noch: Die App filtert nach dem
Setzen des Headers unsichtbare und abgelaufene Nachrichten aus der Liste heraus. Ein Fenster
kann deshalb **200 mit leerer Liste und gesetztem Header** sein, und die Dokumentation der
Route sagt das ausdrücklich ("if none of the messages are visible ... the returned number of
messages will be 0, yet the status will still be 200 ... `X-Chat-Last-Given` may reference a
message not visible and thus not returned, but it should be used nevertheless").
Unser eigener Systemnachrichten-Filter erzeugt genau denselben Fall ein zweites Mal: 50
gelesene Nachrichten, die alle Systemnachrichten sind, ergeben null Ergebnisse bei vorhandenem
älteren Verlauf. **Konsequenz:** `truncated` und `next` dürfen **nicht** aus `len(results)`
abgeleitet werden, sondern aus dem Vorhandensein des Headers. Und `parse_ocs` reicht nur den
Körper zurück, der Client muss also Nachrichten **und** Header liefern (Tupel oder kleines
Datenobjekt).
[VERIFIED: lib/Controller/ChatController.php Zeilen 808-836 und 1112-1231]

**T9. Der Token ist nicht "nicht numerisch", sondern exakt `[a-z0-9]{4,30}`.** Beide
Talk-Routen tragen dieses `requirements`-Muster, ebenso `GET /room/{token}`. Der Pfad-Wächter
dieser Familie ist damit genauso scharf wie `_path_id` bei Tables, nur mit einem anderen
Zeichenvorrat: `re.fullmatch(r"[a-z0-9]{4,30}", token)`. Ein Token mit Grossbuchstaben,
Bindestrich oder Länge 3 ist kein Talk-Token und darf den Request nie erreichen (T-01-63 in
neuer Kleidung). Das ist die querschneidende Änderung, die die ROADMAP für diese Phase
ankündigt, und sie besteht aus dieser einen Funktion, nicht aus einer Änderung an `ids.py`.
[VERIFIED: ChatController und RoomController, `token` => `'[a-z0-9]{4,30}'` an jeder Route]

**T10. Ein unbekanntes Token auf `GET /room/{token}` registriert einen Brute-Force-Versuch für
die IP dieses Containers.** `getSingleRoom` antwortet auf `RoomNotFoundException` mit
`$response->throttle(['token' => $token, 'action' => 'talkRoomToken'])`, und die
`InjectionMiddleware` ruft bei derselben Ausnahme `sleepDelayOrThrowOnMax` mit
`$this->request->getRemoteAddress()`. Nextcloud zählt pro Quell-IP; für eine ExApp ist das eine
IP für alle Nutzer. Ein Modell, das ein Token erfindet, würde also die Talk-Nutzung für die
ganze Instanz verlangsamen und am Ende 429 erzeugen. **Empfehlung:** die Sende-Vorprüfung liest
die Konversationsliste (`GET /room`, ohne Token im Pfad, kein Brute-Force-Ziel) und sucht das
Token darin. Ein unbekanntes Token wird damit zu unserem eigenen Satz ("Dieses Token steht
nicht in deiner Konversationsliste; rufe zuerst talk_browse auf") und erreicht Nextcloud nie.
Zusätzlich: kein Retry auf einem 404 dieser Familie, in keiner Schicht.
[VERIFIED: lib/Controller/RoomController.php Zeilen 530-540,
lib/Middleware/InjectionMiddleware.php Zeilen 436-458]

**T11. `@here` ist in Talk keine Erwähnung, und ein naives Teilstring-Verbot trifft
`@allan`.** Die einzige Sammel-Erwähnung ist `@all`: `UserMention` erkennt
`$mention['type'] === 'user' && $mention['id'] === 'all'` und wandelt sie in den Typ `call`,
also die Benachrichtigung aller Teilnehmer. Das Wort "here" kommt in der App nur in
`searchIsPartOfConversationNameOrAtAll` vor, also in der Autovervollständigung, die "@here" auf
denselben `all`-Eintrag abbildet. Ein wörtlich getipptes "@here" in einer gesendeten Nachricht
ist damit gewöhnlicher Text und benachrichtigt niemanden. TALK-03 verlangt beide Wörter, also
werden beide abgelehnt, aber die Begründung ist unterschiedlich und gehört so in den Docstring
(`@all` ist die wirksame Erwähnung, `@here` die Vorsichtsmassnahme gegen eine künftige
Fassung). Zweiter Punkt: die Prüfung braucht eine Wortgrenze. Ein `if "@all" in message` würde
`@allan` und `@allison` mit ablehnen, also legitime Erwähnungen echter Nutzer. Empfehlung:
`re.search(r"@\"?(all|here)\"?(?![\w-])", message, re.IGNORECASE)`, weil Talk eine Erwähnung mit
Leerzeichen als `@"user id"` schreibt und die Anführungszeichen mitgeprüft werden müssen.
Ergänzend, aber nicht als Ersatz: `mentionPermissions` der Konversation (0 = alle, 1 = nur
Moderatoren) sagt, ob `@all` überhaupt erlaubt wäre.
[VERIFIED: lib/Chat/Parser/UserMention.php Zeilen 96-160, lib/Chat/ChatManager.php Zeilen
1302-1318, lib/Room.php Zeilen 88-89]

**T12. `unreadMessages` ist bei einer nie geöffneten Konversation 1, auch wenn sie leer ist.**
`RoomFormatter` setzt am Ende: wenn der Aufrufer ein Nutzer ist,
`lastReadMessage === UNREAD_FIRST_MESSAGE` und `unreadMessages === 0`, dann wird
`unreadMessages = 1`. Das ist ein Anzeige-Trick der Weboberfläche und keine Nachrichtenzahl.
Konsequenz für diese Phase: `talk_browse(level="conversations")` kann für eine leere
Konversation "1 ungelesen" melden, und der zugehörige Verlauf-Aufruf antwortet dann mit 304,
also mit null Nachrichten (T2). Diese Kombination ist der wahrscheinlichste erste
Integrationstest-Lauf überhaupt, weil eine frisch per `occ` angelegte Konversation genau so
aussieht. Sie gehört als Testfall in den Plan, und der Ungelesen-Zähler darf in der
Tool-Beschreibung nicht als exakte Nachrichtenzahl verkauft werden. Für CTX-01 in Phase 11 ist
derselbe Punkt relevant, weil "Konversationen mit Ungelesenem" damit leere Konversationen
enthalten kann.
[VERIFIED: lib/Service/RoomFormatter.php Zeilen 447-458]

**T13. Zwei Aussagen des ROADMAP-Ziels sind veraltet oder gehören nicht in diese Phase.**
(a) "erster `ocs_post`": den gibt es seit Phase 8 in `clients/ocs.py`, Phase 9 benutzt ihn nur
(das hat 08-RESEARCH als K9 schon korrigiert). (b) "neue Kinds": `ids.py`,
`provider_map.py` und `tools/chatgpt.py::fetch` sollten in dieser Phase **unangetastet**
bleiben. Ein `message:`-Kind, das `fetch` nicht auflösen kann, wäre ein totes Kind, und die
Auflösung ist wörtlich TOOL-16 in Phase 11 (`provider_map`-Eintrag für `talk-message` über die
Attribute `conversation` und `messageId`). Genau so hat Phase 8 mit `row:` entschieden (K8).
Was in dieser Phase wirklich querschneidend ist, ist der Token-Wächter (T9) und die
201-Erweiterung des OCS-Parsers (T1). Die gute Nachricht für Phase 11: die Attribute existieren
und sind verifiziert, `MessageSearch` setzt `conversation` (Token) und `messageId` an jedem
Treffer, und der Deep-Link ist `/index.php/call/{token}#message_{id}`.
[VERIFIED: lib/Search/MessageSearch.php Zeilen 288-316, lib/Controller/PageController.php
Zeile 86; eigene Dateien ids.py, provider_map.py]

**T14. Talk 24 hat einen geplanten Sendeweg, den die Kernrecherche nicht kennt.**
`POST /chat/{token}/schedule` (plus `POST .../schedule/{messageId}` und
`DELETE .../schedule/{messageId}`) legt eine Nachricht an, die die App später selbst sendet;
die Konversationsantwort trägt dazu `hasScheduledMessages`. Für das AST-Gate heisst das: der
Nadelsatz dieser Familie muss `/schedule` enthalten, sonst ist ein Sendeweg ausserhalb des
Schalters von TALK-04 nur durch Disziplin verhindert. Ebenfalls neu und ebenfalls
gate-relevant: `/summarize` (schickt Inhalt an einen KI-Anbieter der Instanz), `/pin`,
`/reminder`, `/attachment`, `/share`.
[VERIFIED: lib/Controller/ChatController.php, Routenliste aller `ApiRoute`-Attribute]

**T15. Der Admin-Schalter kann nicht einfach "wie die fünf anderen" gelesen werden, weil kein
Werkzeug dieses Servers heute Konfiguration liest.** Die bestehende Kette endet in
`entry_exapp._resolved_env()`: das Overlay wird einmal beim Start gelesen und als **Mapping**
an `build_exapp_app(env=...)` gegeben. Es landet nie in `os.environ`
(`grep` über `src/`: keine einzige Schreibstelle), und `tools/*.py` enthält keinen einzigen
Zugriff auf `config` oder `os.environ`. Der Tool-Kontext (`ctx`) trägt nur Header. Das ist der
einzige Punkt dieser Phase ohne Vorbild, und er braucht eine Entscheidung, siehe den eigenen
Abschnitt weiter unten.
[VERIFIED: eigene Dateien entry_exapp.py Zeilen 233-300, exapp/config_values.py,
deps.py Zeilen 75-102, tools/*.py]

## Architekturmuster

### Systemarchitektur, Datenfluss dieser Phase

```
MCP-Client (Claude, Cursor, Agent)
        |
        |  tools/call: talk_browse | talk_send
        v
server/reg_talk.py  [NEU]        Schema, Literal-Enum level, READ_ONLY / CREATE_ONLY
        |  compact(), graceful()
        v
deps.resolve_clients(ctx)        Credential-Naht, unverändert (appapi | basic | bearer | stdio)
        |
        v
tools/talk.py       [NEU]
        |
        +--> capabilities.require_app(clients, "spreed")     [Cache 60 s]
        |        GET /ocs/v2.php/cloud/capabilities -> Sektion "spreed" vorhanden?
        |
        +-- level=conversations --> clients.talk.get_rooms(include_last_message=True)
        |      GET /ocs/v2.php/apps/spreed/api/v4/room?noStatusUpdate=1     parse_ocs
        |      -> isArchived filtern, nach lastActivity sortieren, auf 50 kappen,
        |         projizieren (token, name, type, unread*, lastActivity, readOnly, can_send)
        |
        +-- level=messages ------> clients.talk.get_messages(token, limit, last_known)
        |      GET /ocs/v2.php/apps/spreed/api/v1/chat/{token}
        |          ?lookIntoFuture=0&setReadMarker=0&markNotificationsAsRead=0
        |          &noStatusUpdate=1&limit=<=50&lastKnownMessageId=<cursor>
        |      304 -> ([], None)          200 -> (messages, X-Chat-Last-Given)
        |      -> Systemnachrichten weg, Platzhalter aufgelöst, Byte-Kappe je Nachricht,
        |         marks.without_marks auf jeden Text, truncated/next aus dem HEADER
        |
        +-- talk_send ----------> config.talk_send_enabled()        [T15, erste Zeile]
                                  clients.talk.get_rooms(include_last_message=False)
                                     Token in der Liste suchen  (nie GET /room/{token}, T10)
                                     Vorprüfung: readOnly==0, type not in (4,), permissions&128,
                                                 kein @all/@here, Länge <= max-length
                                  clients.talk.send_message(token, message)
                                     POST /ocs/v2.php/apps/spreed/api/v1/chat/{token}
                                     Body {"message": "..."}      parse_ocs  (201!, T1)
                                     -> {id, token, conversation, url, timestamp}

Querschneidend, ausserhalb der Familie:
clients/ocs.py            _OK_STATUS um 201 erweitert (T1)
capabilities.py           spreed_available, spreed_features, spreed_chat_max_length, _MISSING
config.py                 ENV_TALK_SEND + talk_send_enabled()
exapp/config_values.py    CONFIG_KEYS[5] = "talk_send", KEY_TO_ENV, SWITCH_KEYS
exapp/admin_settings.py   sechstes Feld (checkbox, default True)
exapp/ui/strings.py       Label und Beschreibung des Feldes
entry_exapp.py            Übergabe des aufgelösten Wertes an den Tool-Lesepfad (T15)
```

### Empfohlene Projektstruktur, nur die Deltas

```
src/mcp_connector/
├── config.py                        # GEÄNDERT: ENV_TALK_SEND, talk_send_enabled()
├── entry_exapp.py                   # GEÄNDERT: aufgelöster Schalterwert erreicht den Tool-Pfad
├── nextcloud/
│   ├── capabilities.py              # GEÄNDERT: spreed_available, spreed_features,
│   │                                #           spreed_chat_max_length, _MISSING["spreed"]
│   └── clients/
│       ├── ocs.py                   # GEÄNDERT: _OK_STATUS + 201 (T1)
│       └── talk.py                  # NEU: v4-Räume, v1-Chat lesen und senden, Token-Wächter,
│                                    #      304-Behandlung, Header-Rückgabe
├── tools/
│   └── talk.py                      # NEU: browse(level), send, Projektion, Platzhalter,
│                                    #      Vorprüfungen, Byte-Kappe
├── server/
│   └── reg_talk.py                  # NEU
└── exapp/
    ├── admin_settings.py            # GEÄNDERT: sechstes Feld
    ├── config_values.py             # GEÄNDERT: sechster Schlüssel
    └── ui/strings.py                # GEÄNDERT: zwei neue Konstanten

tests/
├── contract/
│   ├── test_tool_surface.py         # GEÄNDERT: EXPECTED_TOOLS +2, CREATE_TOOLS +1, 18 -> 20,
│   │                                #           Enum-Prüfung, Verbotsliste je Ebene
│   └── test_no_destructive_calls.py # GEÄNDERT: Nadeln + Gegenproben + erlaubte Talk-Routen
├── integration/
│   └── test_talk_roundtrip.py       # NEU: Nebenwirkungsfreiheit live, Senden, readOnly-Absage
├── unit/
│   ├── test_talk_client.py          # NEU (respx): URL-Literale, 304, 201, Token-Wächter
│   ├── test_talk_tools.py           # NEU: Filter, Kappen, Vorprüfungen, Schalter aus
│   ├── test_ocs_capabilities.py     # GEÄNDERT: spreed-Sektion
│   ├── test_exapp_admin_settings.py # GEÄNDERT: sechstes Feld, Reihenfolge
│   ├── test_exapp_config_values.py  # GEÄNDERT: sechster Schlüssel, Switch-Validierung
│   └── test_exapp_entry.py          # GEÄNDERT: der Weg des Schalters in den Tool-Pfad
└── fixtures/
    ├── talk_rooms.json              # NEU
    └── talk_messages.json           # NEU

scripts/
├── bootstrap_exapp.sh               # GEÄNDERT: ensure_app spreed, Testkonversationen
├── bootstrap_test_nc.sh             # GEÄNDERT: ensure_app spreed, Testkonversationen
├── acceptance_all_tools.py          # GEÄNDERT: EXPECTED_TOOLS 18 -> 20
└── check_tool_budget.py             # NUR falls die Messung reisst, mit neuer Messzeile

README.md / README.de.md / README.fr.md   # GEÄNDERT: zwei Tabellenzeilen, Toolzahl
docs/oauth-setup.md                        # GEÄNDERT: sechste Zeile der Feldtabelle
docs/client-setup.md, docs/conference-demo.md  # GEÄNDERT: Toolzahlen
appinfo/info.xml                           # GEÄNDERT: Talk in den drei Beschreibungen
CHANGELOG.md                               # GEÄNDERT: nutzerrelevante Änderung
```

### Muster 1: Die Sicherheitsparameter stehen im Client, nicht im Tool

Der Client baut die URL, also gehört die Regel dorthin. Kein Tool-Parameter, keine
Vorgabewerte, die ein Aufrufer ändern kann, kein `lookIntoFuture` in der Signatur des
Werkzeugs. Die Konstante trägt die Begründung, damit der nächste Leser sie nicht
"aufräumt" (T6).

```python
# src/mcp_connector/nextcloud/clients/talk.py

#: The four parameters that keep a read a read. Not arguments: an argument is something a
#: caller can get wrong, and getting one of these wrong writes into the user's account.
#:
#: ``lookIntoFuture`` is mandatory in the API (no default) and 0 means "history" instead of
#: "long poll", which is what keeps a call from blocking for up to 30 seconds. The other
#: three default to the writing side in Talk (``setReadMarker`` 1,
#: ``markNotificationsAsRead`` 1, ``noStatusUpdate`` 0).
#:
#: In spreed 24.0.4 the read marker and the notification acknowledgement only happen on the
#: ``lookIntoFuture=1`` branch, and the status bump additionally needs a Talk mobile user
#: agent and a session, so with these values none of the three can fire. That is not a
#: reason to drop them: the code that skips them carries a comment calling itself temporary
#: ("until it can be fixed in Vue"), and this project promises the property, not the version.
READ_ONLY_PARAMS: Mapping[str, int] = {
    "lookIntoFuture": 0,
    "setReadMarker": 0,
    "markNotificationsAsRead": 0,
    "noStatusUpdate": 1,
}
```

### Muster 2: Der Token-Wächter (T9)

```python
#: Talk addresses a conversation by a token, and the token is not free text: every route of
#: the app declares ``[a-z0-9]{4,30}``. So this guard is as sharp as the numeric one of
#: Tables, only with a different alphabet, and it runs before the value reaches a URL.
_TOKEN = re.compile(r"[a-z0-9]{4,30}")


def _path_token(value: str) -> str:
    text = str(value).strip()
    if not _TOKEN.fullmatch(text):
        raise ToolError(
            message=f"{value!r} is not a Talk conversation token.",
            hint=(
                "Use a token exactly as talk_browse reports it; a Talk token is 4 to 30 "
                "lower case letters and digits."
            ),
        )
    return text
```

### Muster 3: 304 ist kein Fehler, sondern die leere Antwort (T2)

```python
async def get_messages(
    client: httpx.AsyncClient,
    creds: Credentials,
    token: str,
    *,
    limit: int,
    last_known_message_id: int = 0,
) -> tuple[list[dict[str, Any]], int | None]:
    """Read one window of history, newest first, plus the id to continue with.

    Two things about the answer are not obvious and both are load bearing.

    A conversation without messages, and a window past the oldest message, answer **304**
    with no body. That is a success and not a redirect, so it is handled here: the shared
    parser turns every 3xx into "Nextcloud answered with a redirect, check the base URL",
    which would send the reader of a fresh conversation after a configuration problem that
    does not exist.

    The continuation id comes out of the ``X-Chat-Last-Given`` header and never out of the
    returned messages. The app sets that header from the oldest comment it read and only
    afterwards drops the ones this user may not see, so a window can be a 200 with an empty
    list and a usable header. Deriving the next page from the message ids would stop there
    and silently hide the older history behind it.
    """
    conversation = _path_token(token)
    capped = min(max(int(limit), 1), MAX_MESSAGES)
    response = await ocs.ocs_get(
        client,
        creds,
        f"{CHAT_PREFIX}/{conversation}",
        params={
            **READ_ONLY_PARAMS,
            "limit": capped,
            "lastKnownMessageId": max(int(last_known_message_id), 0),
        },
    )
    if response.status_code == httpx.codes.NOT_MODIFIED:
        return [], None
    payload = ocs.parse_ocs(response, what=f"the messages of conversation {conversation}")
    return _as_list(payload, what="messages"), _last_given(response)
```

### Muster 4: Die Vorprüfung liest das Objekt, nicht das Konto (T3, T4, T10)

```python
def _may_send(room: dict[str, Any]) -> tuple[bool, str]:
    """Whether this account may send into this conversation, and why not if it may not.

    Three refusals, and the second one is the trap of this family. ``attendeePermissions``
    is the *raw* value of the participant and is 0 (``PERMISSIONS_DEFAULT``) for practically
    every ordinary user, because Talk resolves permissions through a fallback chain
    (attendee, then conversation, then instance) and grants a moderator everything. The
    resolved value is ``permissions``, and that is the field Talk's own middleware checks.
    Reading ``attendeePermissions`` would refuse almost everyone in almost every
    conversation, which is the same trap as ``canCreateBoards`` in phase 1 and
    ``onSharePermissions`` in phase 8.

    The type check is not decoration either: ``checkReadOnlyState`` refuses
    ``TYPE_CHANGELOG`` (4) regardless of the ``readOnly`` flag, and every user has exactly
    one of those, the automatically created "Talk updates" conversation.
    """
    if int(room.get("readOnly") or 0) != READ_WRITE:
        return False, "read-only"
    if int(room.get("type") or 0) == TYPE_CHANGELOG:
        return False, "changelog"
    if not int(room.get("permissions") or 0) & PERMISSIONS_CHAT:
        return False, "no-chat-permission"
    return True, ""
```

### Muster 5: Platzhalter auflösen statt durchreichen

Jede Nachricht trägt `message` mit Platzhaltern und `messageParameters` mit den Werten. Die
Schlüssel sind `{actor}`, `{file}`, `{mention-user1}`, `{mention-call1}`,
`{mention-user-group1}` und ähnliche; jeder Parameter ist ein Objekt mit `type`, `id`, `name`
und (bei Erwähnungen) `mention-id`. Auflösung: `{key}` durch `parameters[key]["name"]`
ersetzen, bei Erwähnungen mit `@` davor, ein unbekannter Platzhalter bleibt stehen (nie
raten). Der aufgelöste Text ist fremder Text und geht durch `marks.without_marks`.

```python
_PLACEHOLDER = re.compile(r"\{([a-z0-9_-]+)\}", re.IGNORECASE)

def _resolve(message: str, parameters: Any) -> str:
    params = parameters if isinstance(parameters, dict) else {}

    def replace(match: re.Match[str]) -> str:
        entry = params.get(match.group(1))
        if not isinstance(entry, dict):
            return match.group(0)          # never guess: an unknown placeholder stays
        name = str(entry.get("name") or "").strip()
        if not name:
            return match.group(0)
        kind = str(entry.get("type") or "")
        return f"@{name}" if kind.startswith("user") or kind == "call" else name

    return marks.without_marks(_PLACEHOLDER.sub(replace, str(message or "")))
```

### Muster 6: Auf einer Positivliste filtern, nicht auf einer Negativliste

`messageType` ist eine Enumeration mit elf Werten (`comment`, `system`, `object_shared`,
`command`, `comment_deleted`, `reaction`, `reaction_deleted`, `voice-message`,
`record-audio`, `record-video`, `private_reply`). TALK-02 verlangt "ohne Systemnachrichten";
eine Negativliste (`!= "system"`) lässt beim nächsten neuen Verb automatisch etwas durch.
Empfehlung: `KEPT_TYPES = {"comment", "object_shared", "voice-message", "private_reply"}`
und alles andere fällt weg, mit einem Kommentar, der die Entscheidung je Verb begründet.
Insbesondere `comment_deleted` (gelöschte Nachricht) und `reaction` gehören nicht in den
Verlauf, den ein Modell liest.

### Muster 7: Byte-Kappe je Nachricht, ausserhalb des Textes markiert

Eine Nachricht darf 32.000 Zeichen lang sein. 50 davon sind 1,6 MB in einer MCP-Antwort.
Die Kappe je Nachricht ist deshalb Pflicht (TALK-02). Sie wird **nicht** im Text markiert:
`tools/marks.py` erklärt genau, warum ein Marker im fremden Text ein Angriffsweg ist (ME-03),
und Talk-Nachrichten sind fremder Text von jedem, der in die Konversation schreiben darf.
Empfehlung: Feld `truncated: true` an der einzelnen Nachricht, Kappe als Modulkonstante
(Vorschlag 800 Zeichen, damit 50 Nachrichten schlimmstenfalls rund 40 KB ergeben), und
`marks.without_marks` läuft auf jedem Text, bevor gekappt wird.

### Anti-Muster in dieser Phase

- **`attendeePermissions` prüfen** statt `permissions` (T3). Der wahrscheinlichste Fehler der
  Phase, weil sowohl die Kernrecherche als auch der Phasenauftrag das Feld so nennen.
- **Auf 200 prüfen beim Senden** (T1). Antwort ist 201.
- **304 als Fehler behandeln** (T2).
- **`truncated` aus `len(results)` ableiten** (T8).
- **`GET /room/{token}` mit einem Modell-Token aufrufen** (T10).
- **`if "@all" in message`** ohne Wortgrenze (T11): lehnt `@allan` ab.
- **Kappen ohne zu sortieren** (T5): die Liste hat keine Server-Reihenfolge.
- **`lookIntoFuture` weglassen** (T7): Pflichtparameter.
- **`ids.py` oder `provider_map.py` anfassen** (T13): das ist TOOL-16 in Phase 11.
- **Retry auf dem POST:** eine doppelte Nachricht in einem Chat ist für Dritte sichtbar und
  von keinem Werkzeug dieses Servers entfernbar (DELETE ist per Gate verboten). Ein Versuch,
  die Antwort trägt die Nachrichten-Id, und die Tool-Beschreibung sagt, dass ein Timeout nicht
  bedeutet, dass nichts gesendet wurde.
- **Einen `Origin`-Header senden:** unverändert verboten (Phase 8), gilt auch hier.
- **`silent` durchreichen:** der Parameter existiert im Body-Schema, wird aber nie gesetzt und
  steht auch nicht als Konstante im Modul, damit ein Gate ihn fernhalten kann.

## Talk-API-Referenz (verifiziert gegen spreed 24.0.4)

### Die zwei benutzten Routen

| Zweck | Methode und Pfad | Parser | Bemerkung |
|-------|------------------|--------|-----------|
| Konversationen listen | `GET /ocs/v2.php/apps/spreed/api/v4/room` | `parse_ocs` | API-Version **v4**; Antwort ist eine Liste von `Room` (59 Pflichtfelder) |
| Verlauf lesen | `GET /ocs/v2.php/apps/spreed/api/v1/chat/{token}` | `parse_ocs` plus 304-Sonderfall | API-Version **v1**; Antworten 200, **304**, 404 |
| Nachricht senden | `POST /ocs/v2.php/apps/spreed/api/v1/chat/{token}` | `parse_ocs` (Status **201**) | Body `{"message": "..."}`; Antworten 201, 400, 403, 404, 413, 429 |

Zwei API-Versionen in einer Familie, wie bei Tables zwei Generationen: Räume sind `v4`, Chat
ist `v1`. Beide liegen unter `/ocs/v2.php/apps/spreed/api/`, also über `ocs.ocs_url` gebaut.
Kein `#[OpenAPI(scope: SCOPE_IGNORE)]` an Klasse oder Methode, beide Routen stehen in der
veröffentlichten `openapi.json` der App: eine zugesagte API wie die Tables-Routen (K10), kein
Frontend-Innenleben wie bei Mail. `appinfo/routes.php` existiert in Talk 24 nicht mehr, alle
Routen sind Attribute.

### Parameter, Defaults, Grenzen (aus der `openapi.json` der App)

`GET /api/v4/room`:

| Parameter | Pflicht | Default | Werte | Für uns |
|-----------|---------|---------|-------|---------|
| `noStatusUpdate` | nein | 0 | 0, 1 | immer **1** (TALK-01) |
| `includeStatus` | nein | false | bool | immer weglassen (Nutzerstatus ist Payload ohne Nutzen) |
| `modifiedSince` | nein | 0 | int >= 0 | nicht benutzen (Deltaliste, nicht unser Modell) |
| `includeLastMessage` | nein | **true** | bool | `true` bei `level="conversations"`, **`false`** bei der Sende-Vorprüfung |

`GET /api/v1/chat/{token}`:

| Parameter | Pflicht | Default | Werte | Für uns |
|-----------|---------|---------|-------|---------|
| `lookIntoFuture` | **ja** | keiner | 0, 1 | immer **0** (T7) |
| `limit` | nein | 100 | 1 bis 200 | Default 20, Max 50 (TALK-02) |
| `lastKnownMessageId` | nein | 0 | int >= 0 | Cursor, aus `X-Chat-Last-Given` |
| `lastCommonReadId` | nein | 0 | int >= 0 | nicht benutzen |
| `timeout` | nein | 30 | 0 bis 30 | irrelevant bei `lookIntoFuture=0` |
| `setReadMarker` | nein | **1** | 0, 1 | immer **0** |
| `includeLastKnown` | nein | 0 | 0, 1 | 0 lassen (sonst doppelt paginiert) |
| `noStatusUpdate` | nein | 0 | 0, 1 | immer **1** |
| `markNotificationsAsRead` | nein | **1** | 0, 1 | immer **0** |
| `threadId` | nein | 0 | int >= 0 | nicht benutzen (Threads sind Future Requirement) |

`POST /api/v1/chat/{token}`, Body: `message` ist das einzige Pflichtfeld. Weitere Felder des
Schemas, die alle **nicht** gesetzt werden: `actorDisplayName`, `referenceId`, `replyTo`,
`replyToToken`, `silent`, `threadTitle`, `threadId`.

### Antwort-Header

| Header | Wo | Bedeutung |
|--------|-----|-----------|
| `X-Chat-Last-Given` | Verlauf, 200 | Id der ältesten zurückgegebenen Nachricht, Cursor der nächsten (älteren) Seite; kann eine Nachricht bezeichnen, die nicht in der Liste steht (T8) |
| `X-Chat-Last-Common-Read` | Verlauf und Senden, nur bei `read-privacy` öffentlich | Der für Dritte sichtbare gemeinsame Lesestand. Nur lesen, nie interpretieren; er ist der Grund, warum ein versehentlich gesetzter Lesemarker nicht privat bliebe |
| `X-Nextcloud-Talk-Hash`, `X-Nextcloud-Talk-Modified-Before` | Konversationsliste | Für Clients mit Cache; für uns ohne Bedeutung |

### Feldauswahl der Konversationsliste

Die Antwort hat **59 Pflichtfelder** je Konversation (Anruf, Lobby, Signaling, SIP,
Breakout-Räume, Avatare, Aufzeichnung, Live-Transkription). Projektion ist damit nicht
Optimierung, sondern Voraussetzung. Gebraucht werden:

| Feld | Wofür |
|------|-------|
| `token` | Adressierung, das einzige Identitätsfeld, das ein Modell zurückgeben darf |
| `displayName` | Anzeigename (bei Eins-zu-eins der andere Teilnehmer); `name` ist bei Eins-zu-eins ein JSON-Array der Nutzer-Ids und **nicht** anzeigbar |
| `type` | 1 Eins-zu-eins, 2 Gruppe, 3 öffentlich, 4 Changelog, 5 ehemaliges Eins-zu-eins, 6 Notiz an mich |
| `unreadMessages`, `unreadMention`, `unreadMentionDirect` | Zähler (TALK-01); Vorsicht T12 |
| `lastActivity` | Unix-Zeitstempel, Sortierschlüssel (T5) |
| `readOnly`, `permissions` | Sende-Vorprüfung (T3, T4) |
| `isArchived` | Filter (T5) |
| `isSensitive` | nur zur Kenntnis: die App lässt bei `isSensitive` die `lastMessage` **serverseitig** weg, wir müssen dafür nichts tun (relevant für CTX-01) |
| `lastMessage` | nur bei `level="conversations"`, für die Vorschau (Phase 11 kappt sie auf ~200 Zeichen) |
| `mentionPermissions` | optional, für die Begründung der `@all`-Absage (0 alle, 1 nur Moderatoren) |

Bewusst **nicht** in der Projektion: `id` (die numerische Raum-Id; sie ist kein Adressat
irgendeiner benutzten Route, und ein zweites Identitätsfeld in der Antwort ist eine Einladung,
das falsche zu benutzen), sowie alles rund um Anruf, Lobby, SIP und Avatar.

### Feldauswahl einer Nachricht

`BaseMessage` (Pflicht): `actorType`, `actorId`, `actorDisplayName`, `message`,
`messageParameters`, `messageType`, `systemMessage`, `expirationTimestamp`.
`ChatMessage` ergänzt (Pflicht): `id`, `token`, `timestamp`, `isReplyable`, `markdown`,
`reactions`, `referenceId`; optional `deleted`, `silent`, `threadId`, `isThread`,
`threadTitle`, `threadReplies`, `lastEdit*`, `metaData`, `reactionsSelf`, `parent`.

Empfohlene Projektion: `id`, `timestamp`, `actorDisplayName` (bereinigt), `message`
(aufgelöst, gekappt, bereinigt), plus `truncated` nur wenn gekappt, plus `edited: true` nur
wenn `lastEditTimestamp` gesetzt ist. `reactions` ist bei jeder Nachricht Pflichtfeld und
kostet Bytes ohne Nutzen. `parent` kann eine ganze zweite Nachricht enthalten und bleibt
draussen; `isReplyable` und `markdown` ebenso.

### Capabilities

Sektion **`spreed`** in `GET /ocs/v2.php/cloud/capabilities`, mit `features` (Liste),
`features-local`, `config` und `config-local`. Es gibt **kein** `enabled`-Feld wie bei Tables
und **kein** `apiVersions` wie bei Deck. Die Erkennung ist also die Präsenz der Sektion, wie
bei Notes und Deck. Talk gibt bei einem für den Nutzer deaktivierten Talk ein leeres Array
zurück, wodurch der Schlüssel im zusammengeführten Ergebnis gar nicht auftaucht; eine
defensive Prüfung "Sektion vorhanden und nicht leer" kostet nichts und deckt beides ab.

Nützliche Einzelwerte:

- `config.chat.max-length` = `ChatManager::MAX_CHAT_LENGTH` = **32000**. Empfehlung: die Kappe
  von TALK-03 aus der Capability lesen und 32000 nur als Rückfall im Code halten, dann ist die
  Zahl nicht doppelt gepflegt.
- `features` enthält unter anderem `chat-v2`, `conversation-v4`, `system-messages`,
  `chat-permission`, `mention-permissions`, `chat-keep-notifications`,
  `archived-conversations-v2`, `threads`. `chat-keep-notifications` ist die Fassung, in der
  `markNotificationsAsRead` überhaupt existiert; auf Talk 24 immer vorhanden, aber ein
  ehrlicher Hinweis im Docstring ist billiger als eine stille Annahme.
- Kein Gate auf eine Versionsnummer: `features` ist die Aussage der App über sich selbst.

### Was die App an Schreibwegen sonst noch anbietet (für das Gate, T14)

`chat/{token}/read` (POST Lesemarker setzen, DELETE auf ungelesen), `chat/{token}` (DELETE
Verlauf leeren), `chat/{token}/{messageId}` (DELETE löschen, **PUT** bearbeiten),
`chat/{token}/schedule` und `chat/{token}/schedule/{messageId}` (geplante Nachricht),
`chat/{token}/share`, `chat/{token}/summarize`, `chat/{token}/attachment`,
`chat/{token}/{messageId}/reminder`, `chat/{token}/{messageId}/pin`, plus auf der Raumseite
`room/{token}/favorite`, `/notify`, `/participants`, `/permissions/{mode}`,
`/attendees/permissions`, `/archive`, `/read-only`, `/public`, `/password` und `DELETE
room/{token}`.

Beachten: **PUT** ist kein verbotenes Verb in diesem Projekt (`files_upload` benutzt es), das
Bearbeiten einer Nachricht wird also von keiner Verb-Nadel erfasst. Die tragfähige Absicherung
für diese Familie ist deshalb die **positive** Behauptung: eine eingefrorene Liste der genau
drei Pfadformen, die `clients/talk.py` baut, nach dem Vorbild von `ALLOWED_TABLES_ROUTES`.

## Der Admin-Schalter (TALK-04): die Kette und die eine offene Entscheidung

### Was schon steht

| Baustein | Datei | Was er tut |
|----------|-------|-----------|
| Formular | `exapp/admin_settings.py::form_scheme` | Baut ein Declarative-Settings-Schema mit `section_type: "admin"`, `section_id: "security"`, und **fünf** Feldern; die Feld-Ids werden aus `CONFIG_KEYS` **entpackt** (`public_url_field, dcr_field, cimd_field, allowlist_field, allowed_field = CONFIG_KEYS`), also bricht ein sechster Schlüssel diese Zeile absichtlich |
| Registrierung | `exapp/admin_settings.py::register_admin_form` | POST auf `SETTINGS_PATH` im App-Kontext, ein Versuch, nie eine Ausnahme |
| Schlüssel | `exapp/config_values.py::CONFIG_KEYS` | Fünf Feld-Ids, gleichzeitig die Konfigurationsschlüssel (AppAPIs `SetValueListener` speichert unter der Feld-Id, ohne Präfix) |
| Übersetzung | `exapp/config_values.py::KEY_TO_ENV` | Schlüssel zu `NC_MCP_*`-Variablenname; das Overlay spricht die Sprache der Deploy-Umgebung |
| Schalter-Validierung | `exapp/config_values.py::SWITCH_KEYS`, `_switch` | Nur `on`/`off` verlassen das Modul; ein unverständlicher Wert wird abgelehnt und protokolliert, ohne den Wert zu nennen |
| Lesen | `exapp/config_values.py::read_values` | Ein POST auf `.../ex-app/config/get-values`, jedes Scheitern ist ein leeres Ergebnis plus eine Logzeile; ein 401 ist der erwartete Fall vor dem `enable` |
| Auflösung | `entry_exapp._resolved_env` | Genau einmal beim Start: `{**os.environ, **overlay}`, danach als Mapping an jede Fabrik |
| Texte | `exapp/ui/strings.py` | Label und Beschreibung je Feld, als Modulkonstanten in `__all__` (wegen des vulture-Gates) |
| Tests | `tests/unit/test_exapp_admin_settings.py::test_the_five_fields_are_the_five_config_keys_in_order`, `tests/unit/test_exapp_config_values.py` (mehrere, u.a. `test_the_five_keys_are_the_field_ids_of_the_admin_form`, `test_one_request_asks_for_all_five_keys`, `test_all_five_values_travel_together`) | Halten Form und Lesepfad aneinander; jeder dieser Namen und Docstrings nennt die Zahl fünf |

Zwei geerbte Fallen, beide im Modul-Docstring von `admin_settings.py` benannt und beide für
das neue Feld relevant: `sensitive: true` würde den Wert verschlüsseln, sodass die ExApp ihn
nicht mehr lesen kann (nicht setzen), und Declarative Settings kennen **keinen Button**, nur
`text`, `password`, `email`, `tel`, `url`, `number`, `checkbox`, `multi-checkbox`, `radio`,
`select`, `multi-select`. Der Schalter ist also eine `checkbox` mit `"default": True`
(TALK-04: an per Default).

### Die offene Entscheidung: wie das Werkzeug den Schalter sieht (T15)

Das Overlay landet **nicht** in `os.environ`, und kein Werkzeug liest heute Konfiguration.
Drei Wege, mit ihren Preisen:

**Weg A (Empfehlung): den aufgelösten Wert beim Start in `os.environ` schreiben, und im Tool
mit `config.talk_send_enabled()` pro Aufruf lesen.**
- Passt exakt zum bestehenden Muster: `config.select_mode`, `config.static_bearer`,
  `config.exapp_configured` lesen alle `os.environ if env is None else env`, und
  `select_mode` läuft schon heute **pro Request**.
- Kein neuer Modulzustand. Das ist der entscheidende Punkt: D-20 erlaubt genau zwei namentlich
  gelistete Ausnahmen, und `tests/contract/test_no_destructive_calls.py::ALLOWED_MODULE_STATE`
  führt sie wörtlich (`nextcloud/http.py::_clients`, `nextcloud/capabilities.py::_cache`). Ein
  Policy-Modul mit einem Setter wäre eine dritte Ausnahme plus eine Gate-Änderung.
- Funktioniert in allen vier Modi: im stdio-, HTTP- und Bearer-Modus gibt es kein Overlay, dort
  ist `NC_MCP_TALK_SEND` aus der Umgebung die einzige Quelle, und das ist korrekt.
- Preis: eine Schreibstelle auf `os.environ` beim Start, vor dem ersten Socket, für genau
  diesen einen Schlüssel. Das muss im Kommentar begründet und im Test festgehalten werden
  (`tests/unit/test_exapp_entry.py`), sonst ist es die Art Zeile, die beim nächsten Refactor
  verschwindet. Zweiter Preis: der bekannte Schritt "einmal deaktivieren und aktivieren",
  damit ein geänderter Wert greift, genau wie bei den fünf anderen; er steht schon an drei
  Stellen und muss auch in der Beschreibung dieses Feldes stehen.

**Weg B: pro `talk_send`-Aufruf frisch aus Nextcloud lesen** (`config_values.read_values` mit
diesem Schlüssel).
- Vorteil: der Schalter wirkt sofort, ohne Aktivierungszyklus. Für einen Sicherheitsschalter
  ist das ein echtes Argument, und D-48 hat für den Per-Nutzer-Schalter genau so entschieden
  ("je Request lokal gelesen, ohne Prozess-Cache").
- Nachteil: ein zusätzlicher Nextcloud-Roundtrip pro Sendevorgang, ein zweiter Fehlermodus
  (was gilt, wenn der Lesevorgang scheitert), und der 401-Zeitraum vor dem `enable`. Der
  Vergleich mit D-48 trägt nur halb: dort liegt der Schalter in **unserem** lokalen Store, hier
  in Nextcloud.
- Wenn der Owner Weg B will, muss die Antwort auf "Lesevorgang scheitert" **fail closed** sein
  (nicht senden), und das widerspricht "an per Default" bei jeder Netzwerkstörung.

**Weg C: den Wert per Request durch die Middleware in den Header-Kanal geben.**
- Abzulehnen. `ctx` trägt nur Header, ein Header ist von aussen setzbar, und die Absicherung
  wäre "die Middleware überschreibt ihn zuverlässig". Ein Sicherheitsschalter, dessen
  Aus-Zustand von einer Header-Bereinigung abhängt, ist schlechter als der Aktivierungszyklus.

**Empfehlung: Weg A**, mit diesen Bausteinen:
- `config.ENV_TALK_SEND = "NC_MCP_TALK_SEND"` und
  `config.talk_send_enabled(env=None) -> bool` mit Default `True`.
- Die Wertmengen (`1/true/yes/on` gegen `0/false/no/off`) existieren schon dreimal
  (`oauth/registry._TRUE_VALUES`, `exapp/config_values.TRUE_VALUES` und deren Gegenstücke).
  `config_values` importiert `config`, ein Import in die andere Richtung wäre zirkulär. Also:
  eigene Konstanten in `config.py` plus ein Test, der sie gegen die bestehenden gleichsetzt,
  genau wie `config_values` es heute für `registry` beschreibt ("held equal by a test").
- `CONFIG_KEYS` bekommt `"talk_send"` als **sechsten** Eintrag; das Entpacken in
  `form_scheme` und alle Tests mit "five" im Namen ziehen nach.
- Reihenfolge im Formular: `talk_send` **hinten**, nach den vier OAuth-Werten. Begründung, die
  in den Kommentar gehört: die drei OAuth-Schalter stehen bewusst beieinander, weil der Code
  zwei davon als eine Antwort liest (`registry.client_policy`); der Talk-Schalter ist
  unabhängig, und ihn dazwischen zu setzen würde diese Gruppierung zerreissen.
- Das Formular heisst weiter "MCP Connector" und sitzt in `security`. Der Titel muss nicht
  geändert werden, aber `ADMIN_SETTINGS_DESCRIPTION` sollte einen Satz bekommen, damit die
  Seite nicht nur von OAuth spricht.
- `docs/oauth-setup.md` Zeile 110 sagt wörtlich "carries five fields" und darunter steht die
  Tabelle: sechste Zeile plus ein Satz, dass ein Feld dieser Form nicht OAuth betrifft.

### Was der Ende-zu-Ende-Nachweis von TALK-04 messen muss

Erfolgskriterium 5 verlangt die ganze Kette. Drei Schichten, alle drei billig:
1. **Form:** das Schema trägt sechs Felder in der Reihenfolge von `CONFIG_KEYS`, das neue ist
   eine `checkbox` mit `default: True` und trägt kein `sensitive` (bestehender Test erweitert).
2. **Lesepfad:** eine gefälschte OCS-Antwort mit `configkey: "talk_send"`, `configvalue: "0"`
   ergibt ein Overlay `{"NC_MCP_TALK_SEND": "off"}`; ein unverständlicher Wert wird abgelehnt
   und lässt die Umgebung stehen (bestehende Testmuster erweitern).
3. **Wirkung:** `talk_send` mit `NC_MCP_TALK_SEND=0` antwortet mit dem Fehlersatz plus nächstem
   Schritt und macht **keinen** HTTP-Aufruf (mit `respx` beweisbar: die Route wurde nie
   gerufen). Genau diese Behauptung ist der Kern, denn ein Schalter, der erst nach dem Request
   greift, hätte die Nachricht schon gesendet.

Der Fehlersatz braucht einen nächsten Schritt, der zum Adressaten passt. Der Nutzer kann hier
nichts tun, also lautet er ungefähr: "Sending Talk messages is switched off for this
Nextcloud. An administrator can enable it under Administration settings, Security, MCP
Connector. Reading conversations with talk_browse is unaffected."

## Don't Hand-Roll

| Problem | Nicht selbst bauen | Stattdessen | Warum |
|---------|--------------------|-------------|-------|
| Erwähnungen und Dateinamen in Nachrichtentext einsetzen | Eigener Parser über `@"user id"`-Syntax des Rohtexts | `message` plus `messageParameters` der App auflösen | Die App hat die Anzeigenamen schon aufgelöst, inklusive Gästen, Gruppen, Teams und föderierten Nutzern; ein zweiter Parser wäre eine zweite Wahrheit über fremde Identitäten |
| Fenster über den Verlauf legen | Eigene Offset-Rechnung über Nachrichten-Ids | `X-Chat-Last-Given` plus `paging.encode_cursor` | Die Id-Variante bricht am leeren Fenster mit Status 200 (T8); `check_scope` verhindert zusätzlich, dass ein Handle einer anderen Konversation angewendet wird |
| Statuscodes auf Sätze abbilden | Neue Fehlerbehandlung im Talk-Client | `ocs.parse_ocs` plus `_status_error` (mit 201 im Erfolgsraum, T1) | Eine Stelle für alle Familien; der 403 dieser Familie ist ohne Körper und wird ohnehin von unserer Vorprüfung überholt |
| Chat-Rechte selbst herleiten | Eigene Auswertung von `attendeePermissions`, `defaultPermissions` und Teilnehmertyp | Das aufgelöste `permissions`-Feld lesen (T3) | Talk hat die Kette schon gelaufen, inklusive der Moderator-Regel; letzte Instanz bleibt die Middleware der App |
| Marker in fremdem Text | Eigene Kürzungsmarkierung im Nachrichtentext | `marks.without_marks` plus ein Feld neben dem Text | `tools/marks.py` erklärt genau diesen Angriffsweg (ME-03); Chatnachrichten sind der Ort, an dem er am billigsten ist |
| Länge prüfen | Feste 32000 im Code | `config.chat.max-length` aus den Capabilities, 32000 als Rückfall | Die Zahl gehört der Instanz, nicht uns |
| Zeitstempel formatieren | Eigene Umrechnung in ISO | Den Unix-Zeitstempel der App durchreichen | Präzedenz `tools/notes.py` (`modified` als Zahl); eine ISO-Zeichenkette kostet rund 700 Bytes bei 50 Nachrichten und muss eine Zone erfinden |
| Testkonversation anlegen | Eigenen Raum über die API bauen | `occ talk:room:create` plus `talk:room:update` | Die App bringt die Kommandos mit, inklusive `--readonly` für den Negativfall; ein Raum ist keine Fähigkeit dieses Connectors |

## Häufige Fallen in dieser Phase

### Falle 1: Der erste erfolgreiche Sendevorgang sieht wie ein Fehler aus

Siehe T1. **Frühwarnzeichen:** "unexpected status 201" im Testlauf, und die Nachricht steht
trotzdem in Talk. Wer dann den Status im Talk-Client sonderbehandelt, baut die
Envelope-Auswertung ein zweites Mal.

### Falle 2: Eine frische Konversation meldet ein Konfigurationsproblem

Siehe T2. **Frühwarnzeichen:** `REDIRECT_HINT` in der Antwort eines Verlauf-Aufrufs. Der Satz
schickt den Leser zur Basis-URL, obwohl die Konversation nur leer ist. Zusammen mit T12 ist
das der wahrscheinlichste erste Integrationstest-Lauf.

### Falle 3: Die Vorprüfung sperrt jeden aus

Siehe T3. **Frühwarnzeichen:** der erste Sendeversuch in eine selbst angelegte Konversation
wird mit dem eigenen Fehlersatz abgewiesen. Wer dann die Prüfung entfernt, verliert sie ganz
und läuft in einen 403 ohne Körper.

### Falle 4: Die Changelog-Konversation

Siehe T4. Sie ist oft die einzige Konversation eines frischen Testkontos, `readOnly` ist dort
0, und ein Sendeversuch endet in einem 403 ohne Begründung. **Vermeidung:** Typ 4 in der
Vorprüfung, und im Integrationstest bewusst nicht als Ziel wählen.

### Falle 5: Kappen ohne Sortieren

Siehe T5. **Frühwarnzeichen:** keins. Das ist die Gefahr. Auf einer Testinstanz mit drei
Konversationen fällt es nie auf, und auf einer echten Instanz mit 80 Konversationen liefert die
Liste 50 beliebige. **Vermeidung:** der Unit-Test enthält eine Fixture, deren Server-Reihenfolge
absichtlich nicht der `lastActivity`-Reihenfolge entspricht.

### Falle 6: Die Paginierung hört zu früh auf

Siehe T8. **Frühwarnzeichen:** ein Verlauf, der bei einer Konversation mit vielen
Systemnachrichten nach der ersten Seite endet, obwohl älterer Verlauf existiert.
**Vermeidung:** `truncated` und `next` aus dem Header ableiten, und ein Unit-Test mit einem
Fenster, das nur Systemnachrichten enthält (200, leere Ergebnisliste, gesetzter Header, also
`count: 0` **mit** `next`).

### Falle 7: Ein erfundenes Token sperrt die Instanz

Siehe T10. **Frühwarnzeichen:** 429 aus Talk, für alle Nutzer, nach einem Testlauf mit
geratenen Tokens. Auf der lokalen Topologie ist der Schutz per Bootstrap abgeschaltet
(`DISABLE_BRUTEFORCE=1`), die Regel gehört also in den Code, nicht in die Topologie, genau wie
Phase 8 es für den Mail-Spike festgehalten hat.

### Falle 8: Das Budget-Gate

Live gemessen: **12801 Bytes bei 18 Werkzeugen, Gate 15000, Pro-Tool-Deckel 1400**
[VERIFIED: `uv run python scripts/check_tool_budget.py`, heute gelaufen]. Freiraum: 2199 Bytes.
Das Tables-Paar aus Phase 8 kostete 751 plus 780, also 1531. Ein Talk-Paar mit vergleichbarem
Schnitt landet damit bei etwa 14300 bis 14500, also knapp unter dem Gate. Zwei Konsequenzen für
den Plan: (a) die Messung gehört in denselben Commit wie die Werkzeuge, damit ein Reissen sofort
sichtbar ist, und eine Anhebung nur mit neuer datierter Messzeile; (b) die Beschreibung von
`talk_send` ist der Ort, an dem das Budget wirklich reissen kann, weil dort viel zu sagen wäre
(kein Bearbeiten, kein Löschen, kein Retry, Token nur aus `talk_browse`, Schalter). Der
Pro-Tool-Deckel von 1400 Bytes ist die eigentliche Grenze; heutiger Ausreisser ist
`calendar_create_event` mit 1351. TOOL-15 verankert das Gate in Phase 11 neu, diese Phase muss
es nur nicht stillschweigend brechen.

### Falle 9: Die eingefrorenen Literale

`tests/contract/test_tool_surface.py` prüft an fünf Stellen gegen feste Werte, und die Zahl 18
steht zusätzlich in einem Docstring (Zeile 370), in einer Assertion-Meldung (Zeile 520) und in
einem Kommentar (Zeile 560). Dazu die Zahlen in drei READMEs, zwei `docs/`-Seiten und
`scripts/acceptance_all_tools.py` (`EXPECTED_TOOLS = 18`, plus Modul-Docstring und Zeile 16).
Vollständige Liste unten. Ein vergessener Punkt macht die Phase rot an einer Stelle, die nichts
mit Talk zu tun hat.

### Falle 10: Der Schalter greift nach dem Request

Siehe TALK-04-Abschnitt, Schicht 3. Ein Schalter, der geprüft wird, nachdem der POST
abgeschickt wurde, hat nichts verhindert. `config.talk_send_enabled()` ist die **erste** Zeile
von `tools.talk.send`, vor `require_app`, vor jedem Client-Aufruf, und der Test beweist das
über die nicht gerufene `respx`-Route.

## Mechanische Checkliste (exakte Anknüpfungspunkte)

### Produktionscode

| Datei | Änderung |
|-------|----------|
| `src/mcp_connector/nextcloud/clients/talk.py` | NEU. Vorbild `clients/tables.py`: Modul-Docstring mit den Pflichtheadern (D-18) und der Begründung der vier Leseparameter, `ROOM_PREFIX = "/apps/spreed/api/v4/room"`, `CHAT_PREFIX = "/apps/spreed/api/v1/chat"`, `TALK_WEB_PREFIX = "/index.php/call"`, `READ_ONLY_PARAMS`, `MAX_MESSAGES = 50`, `_path_token` (T9), `get_rooms`, `get_messages` (304 plus Header, T2/T8), `send_message` (201, T1), `web_url` |
| `src/mcp_connector/nextcloud/clients/ocs.py` | `_OK_STATUS` auf `{100, 200, 201}` mit Begründungskommentar (T1) |
| `src/mcp_connector/nextcloud/capabilities.py` | `Capabilities`: `spreed_available` (Präsenz der Sektion, nicht `enabled`), `spreed_features: tuple[str, ...]`, `spreed_chat_max_length: int`; `has()`-Dictionary um `"spreed"`; `_MISSING["spreed"]` mit einem Satz plus einer Sache, die der Nutzer tun kann; `parse()` entsprechend. **Achtung:** der Schlüssel heisst `spreed`, nicht `talk`; der Docstring des Moduls sagt heute "Only these three optional apps" und muss mitgezogen werden |
| `src/mcp_connector/tools/talk.py` | NEU. `APP = "spreed"`, `LEVELS = ("conversations", "messages")`, `DEFAULT_LIMIT = 20`, `MAX_LIMIT = 50`, `MAX_CONVERSATIONS = 50`, `MAX_MESSAGE_BYTES` (UTF-8-Byte-Kappe), `KEPT_TYPES`, `browse`, `send`, `_conversation`, `_message`, `_resolve`, `_may_send`, `_rejects_mention_all`, `_envelope` |
| `src/mcp_connector/server/reg_talk.py` | NEU. Vorbild `reg_tables.py`: `Literal["conversations", "messages"]`, leere Strings statt `None`, `structured_output=False`, `READ_ONLY` / `CREATE_ONLY`, `@graceful`, `compact(...)` |
| `src/mcp_connector/config.py` | `ENV_TALK_SEND`, `talk_send_enabled()`, Wertmengen (T15) |
| `src/mcp_connector/entry_exapp.py` | Der aufgelöste Schalterwert erreicht den Tool-Lesepfad (T15, Weg A: eine begründete Zeile in `main`, nach `_resolved_env`, vor jedem Socket) |
| `src/mcp_connector/exapp/config_values.py` | `CONFIG_KEYS` plus `"talk_send"`, `KEY_TO_ENV`, `SWITCH_KEYS`; Modul-Docstring ("Die fünf Werte") nachziehen |
| `src/mcp_connector/exapp/admin_settings.py` | Entpackzeile auf sechs Namen, sechstes Feld (`checkbox`, `default: True`, kein `sensitive`), Modul-Docstring nachziehen |
| `src/mcp_connector/exapp/ui/strings.py` | `ADMIN_FIELD_TALK_SEND_LABEL` und `..._DESCRIPTION`, beide in `__all__` (sortiert, vulture-Gate); die Beschreibung nennt den Aktivierungszyklus und dass Lesen unberührt bleibt |
| `src/mcp_connector/ids.py`, `provider_map.py`, `tools/chatgpt.py`, `tools/context.py` | **Unverändert** (T13, Phase 11) |

### Tests

| Datei | Änderung |
|-------|----------|
| `tests/contract/test_tool_surface.py` | `EXPECTED_TOOLS` plus `talk_browse`, `talk_send`; `CREATE_TOOLS` plus `talk_send`; `len(tools) == 18` auf 20 (Zeile 375), Docstring Zeile 370, Assertion-Meldung Zeile 520, Kommentar Zeile 560; neuer Test für das Level-Enum und die Abwesenheit von `$defs`; Verbotsliste `talk_list_conversations`, `talk_list_messages`, `talk_read_message`, `talk_send_message` analog `test_there_is_no_tool_per_deck_level` |
| `tests/contract/test_no_destructive_calls.py` | Nadeln für die Talk-Schreibwege, die kein verbotenes Verb brauchen: `/schedule`, `/summarize`, `/reminder`, `/pin`, `/attachment`, `/read`, `/favorite`, `/notify`, `/participants`, `/archive` (T14), je mit Gegenprobe wie die fünf Tables-Nadeln; plus eine `ALLOWED_TALK_ROUTES`-Behauptung über die genau drei Pfadformen des neuen Clients, weil **PUT** kein verbotenes Verb ist und ein Bearbeiten-Pfad sonst durch keine Nadel fällt. **Achtung Kollisionsprüfung:** die Nadel `/read` darf keine bestehende Zeile treffen (heute existiert kein Pfadliteral mit diesem Segment; `files_read` und `read_offset` sind Identifier ohne Schrägstrich) |
| `tests/unit/test_talk_client.py` | NEU, `respx`. Muss enthalten: die vier Leseparameter wörtlich in der gebauten URL (positiv behauptend, T6), `lookIntoFuture=0` vorhanden (T7), `limit` gekappt auf 50, 304 ergibt `([], None)` (T2), 200 mit leerer Liste plus Header ergibt `([], id)` (T8), Senden mit Status 201 (T1), Token-Wächter lehnt `ABC`, `abc`, `ab-cd` und 31 Zeichen ab (T9), eingefrorene URL-Literale beider API-Versionen |
| `tests/unit/test_talk_tools.py` | NEU. Level-Validierung, `isArchived` gefiltert, Sortierung nach `lastActivity` bei absichtlich unsortierter Fixture (T5), Kappe 50 mit `truncated`, Systemnachrichten weg (Positivliste), Platzhalter aufgelöst inklusive unbekanntem Platzhalter, Byte-Kappe je Nachricht, `no_data` bei 304, Vorprüfung: `readOnly=1`, `type=4` (T4), `permissions` ohne Bit 128, `permissions=0` gegen `attendeePermissions=0` als Regressionsfall zu T3, `@all`, `@here`, `@allan` **erlaubt**, Text über der Kappe, unbekanntes Token nicht in der Liste, Schalter aus (kein HTTP-Aufruf) |
| `tests/unit/test_ocs_capabilities.py` | `spreed`-Sektion, plus der Fall "Sektion fehlt" und "Sektion leer" |
| `tests/unit/test_exapp_admin_settings.py` | `test_the_five_fields_...` auf sechs, Reihenfolge gegen `CONFIG_KEYS`, neues Feld ist `checkbox` mit `default: True` und ohne `sensitive` |
| `tests/unit/test_exapp_config_values.py` | Sechster Schlüssel in den vier Stellen mit "five" im Namen oder Docstring (Zeilen 1, 73, 76, 84, 102, 123, 690), Switch-Validierung für `talk_send`, Overlay-Zuordnung auf `NC_MCP_TALK_SEND` |
| `tests/unit/test_exapp_entry.py` | Der Weg des Schalterwertes vom Overlay in den Tool-Lesepfad (T15) |
| `tests/unit/test_config.py` | `talk_send_enabled` mit allen Schreibweisen, Default `True`, unverständlicher Wert |
| `tests/integration/test_talk_roundtrip.py` | NEU, Marker `integration`. Vorbild `test_tables_roundtrip.py`: idempotentes Gerüst nach Namen (T-08-30), Nebenwirkungs-Messung vor und nach dem Lesen (T6, Schicht 2), Senden mit Rücklesen, Absage in einer per `occ` schreibgeschützten Konversation, Messwerte per `warnings.warn` |
| `tests/integration/test_permission_fidelity_exapp.py` | Zwei-Konten-Negativbeweis für Talk: das zweite Konto sieht die Konversation des ersten nicht in seiner Liste, erreicht den Verlauf bei bekanntem Token nicht und kann nicht hineinsenden; Nachrichtenzahl des Eigentümers davor und danach unverändert (Muster aus Phase 8, Plan 05) |
| `tests/fixtures/talk_rooms.json`, `talk_messages.json` | NEU. Vorbild `deck_boards.json`. Die Raum-Fixture trägt bewusst eine Server-Reihenfolge, die der `lastActivity`-Reihenfolge widerspricht, eine zur Seite gelegte Konversation, eine schreibgeschützte, eine mit Typ 4 und eine mit `permissions` ohne Bit 128 |

### Skripte, Doku, Topologie

| Datei | Änderung |
|-------|----------|
| `scripts/bootstrap_exapp.sh` | `ensure_app spreed` neben `ensure_app tables` / `ensure_app mail` (Zeilen 891 und 892); dazu idempotent zwei Testkonversationen für den Testnutzer über `occ talk:room:create`, eine davon `--readonly` |
| `scripts/bootstrap_test_nc.sh` | `ensure_app spreed` neben `ensure_app tables` (Zeile 164), dieselben Konversationen |
| `scripts/acceptance_all_tools.py` | `EXPECTED_TOOLS = 18` auf 20 (Zeile 52), plus Modul-Docstring (Zeile 1) und Zeile 16; `docs/conference-demo.md` beschreibt die Fehlermeldung dieses Skripts wörtlich |
| `scripts/check_tool_budget.py` | Nur falls die Messung reisst: `BUDGET_BYTES` anheben **mit** neuer datierter Messzeile im Kommentarblock (die Regel steht dort wörtlich) |
| `README.md` | Tool-Tabelle um zwei Zeilen nach dem Muster von Zeile 198 und 199; "The 18 tools" in Zeile 19 und "All 18 tools" in Zeile 30 |
| `README.de.md`, `README.fr.md` | Dieselben zwei Zeilen (nach Zeile 205/206 bzw. 208/209) und Zahlen (Zeilen 21 und 32 bzw. 21 und 34) |
| `docs/oauth-setup.md` | "carries five fields" (Zeile 110) und die Feldtabelle (Zeilen 113 bis 119) um den sechsten Wert, plus ein Satz, dass nicht jedes Feld dieser Form OAuth betrifft |
| `docs/client-setup.md` | "18 tools" in Zeilen 11 und 74 (Zeile 431 ist ein datierter Messwert und darf stehenbleiben, solange die Seite auf `tests/contract/test_tool_surface.py` zeigt) |
| `docs/conference-demo.md` | `tools=18` (Zeile 140) und die Beispielmeldung des Abnahmeskripts (Zeile 271) |
| `appinfo/info.xml` | Talk in die drei `<description>`-Blöcke (zweiter Absatz nennt die Familien namentlich), Format-Regeln des Datei-Kommentars beachten, Vokabular-Gate beachten, `<version>` und `<image-tag>` **nicht** anfassen |
| `CHANGELOG.md` | Nutzerrelevante Änderung: Konversationen und Verlauf lesen, Nachricht senden, Admin-Schalter |

## Codebeispiele

### Senden, mit dem Statuscode dieser Familie

```python
# src/mcp_connector/nextcloud/clients/talk.py

async def send_message(
    client: httpx.AsyncClient, creds: Credentials, token: str, *, message: str
) -> dict[str, Any]:
    """Send one message into an existing conversation and return what Talk stored.

    The answer is **201**, not 200: the controller documents 201 as its only success and the
    app's own ``openapi.json`` lists exactly that. OCS v2 puts the raw status into
    ``ocs.meta.statuscode``, so the shared parser has to accept 201 as success as well; it is
    the first route of this project that answers with it.

    Only ``message`` travels. The body schema also knows ``silent``, ``replyTo``,
    ``threadId``, ``threadTitle``, ``actorDisplayName`` and ``referenceId``; none of them is
    set, and ``silent`` is not even spelled in this module, so a gate can keep it out.

    There is no retry. A duplicated message is visible to other people and no tool of this
    server can remove it again, so the answer carries the id and the model can read back
    instead of repeating.
    """
    conversation = _path_token(token)
    response = await ocs.ocs_post(
        client, creds, f"{CHAT_PREFIX}/{conversation}", {"message": message}
    )
    return _as_dict(
        ocs.parse_ocs(response, what="the sent message"), what="a message"
    )
```

### Der Cursor dieser Familie

```python
# src/mcp_connector/tools/talk.py

# The handle carries the id to continue with and the conversation it belongs to. ``o`` is the
# key ``paging.read_offset`` reads, and a message id fits it: it is a non-negative int. The
# scope key is the token, so a handle of another conversation is refused instead of silently
# answering the wrong history.
state = paging.decode_cursor(cursor)
paging.check_scope(state, "c", token, "conversation")
last_known = paging.read_offset(state)
...
if last_given is not None:
    answer["truncated"] = True
    answer["next"] = paging.encode_cursor({"o": last_given, "c": token})
```

### Die Nebenwirkungs-Messung (Erfolgskriterium 3, Schicht 2)

```python
# tests/integration/test_talk_roundtrip.py  (Skizze)

async def test_reading_the_history_changes_nothing_about_the_account(...) -> None:
    """The property TALK-02 promises, measured instead of asserted about our own URL.

    The unit test holds that the four parameters are in the request. This one holds the
    consequence: the read marker, both unread counters and the read state other people can
    see are the same before and after. Those four are the whole observable surface of the
    three side effects the parameters switch off.
    """
    before = await _conversation(clients, token)
    await talk_tools.browse(clients, level="messages", token=token, limit=20)
    after = await _conversation(clients, token)

    for field in ("lastReadMessage", "unreadMessages", "unreadMention", "lastCommonReadMessage"):
        assert before[field] == after[field], f"reading changed {field}"
```

## Stand der Technik

| Alt | Aktuell | Seit | Bedeutung |
|-----|---------|------|-----------|
| Talk 21/22 mit `appinfo/routes.php` | Talk **24.0.4**, alle Routen als `ApiRoute`-Attribute, kein `routes.php` | 2026-08-13 (24.0.4), Attribut-Umstellung früher | Eine Routenliste entsteht nur aus dem Controller-Quellcode oder aus `openapi.json`; wer `routes.php` sucht, findet nichts und hält die API für verschwunden |
| Chat ohne Threads | `threads`-Capability, `threadId` an jeder Chat-Route, `ThreadController` | Talk 24 | Für uns: Future Requirement, `threadId` bleibt ungesetzt. Aber die Antwortfelder `threadId`, `isThread`, `threadTitle`, `threadReplies` existieren und gehören nicht in die Projektion |
| Kein geplanter Versand | `chat/{token}/schedule`, `hasScheduledMessages` am Raum | Talk 24 | Neuer Sendeweg, der in das AST-Gate muss (T14); die Kernrecherche kennt ihn nicht |
| `archived-conversations` | `archived-conversations-v2`, plus `isImportant` und `isSensitive` pro Teilnehmer | Talk 22/23 | `isSensitive` unterdrückt die letzte Nachricht serverseitig, was für CTX-01 in Phase 11 die Vorschau-Frage teilweise beantwortet |
| Tables 2.2.2, Mail 5.11.1 | unverändert installiert auf beiden Topologien | 2026-08-21 | Keine Aktion in dieser Phase |

**Veraltet oder irreführend:**
- Die Formulierung der Kernrecherche und von TALK-01, `noStatusUpdate=1` verhindere, dass das
  Listen den Online-Status setzt: in 24.0.4 hängt der Status-Bump zusätzlich an einem
  Talk-Mobil-User-Agent, den dieser Server nie sendet (T6). Der Parameter bleibt richtig, die
  Begründung ist eine andere.
- Die Formulierung "Permission-Bit 128 an `attendeePermissions`": falsches Feld (T3).
- Die ROADMAP-Zeile "erster `ocs_post`" und "neue Kinds" für diese Phase (T13).
- Die Annahme, `@here` sei eine Talk-Erwähnung (T11).

## Security Domain

`security_enforcement` ist in `.planning/config.json` nicht gesetzt, gilt damit als aktiv.

### Anwendbare ASVS-Kategorien

| ASVS-Kategorie | Betroffen | Standardkontrolle in dieser Phase |
|----------------|-----------|-----------------------------------|
| V2 Authentication | nein | Die vier Credential-Modi bestehen unverändert; kein neuer Auth-Pfad |
| V3 Session Management | nein | Kein Zustand zwischen zwei Aufrufen; der Cursor trägt keine Autorität. **Wichtig:** der Admin-Schalter darf keinen neuen Modulzustand einführen (T15, Weg A) |
| V4 Access Control | **ja** | Vorprüfung am Objekt (`readOnly`, `type`, `permissions`), letzte Instanz bleiben Talks `RequirePermission` und `RequireReadWriteConversation`; kein Edit-, Delete-, Schedule- oder Silent-Pfad im Client; instanzweiter Schalter als zweite, administrative Grenze (TALK-04) |
| V5 Input Validation | **ja** | `_path_token` gegen `[a-z0-9]{4,30}` vor jedem Request (T9); `limit` im Client gekappt; Nachrichtenlänge gegen `config.chat.max-length` geprüft; `@all`/`@here` mit Wortgrenze abgelehnt (T11); Token nur aus der Konversationsliste (T10) |
| V6 Cryptography | nein | Nichts Neues, kein Geheimnis in dieser Phase |
| V7 Error Handling und Logging | **ja** | Jeder Fehler ist ein Satz plus nächster Schritt; 403 dieser Familie hat keinen Körper und wird von der Vorprüfung überholt; 304 ist kein Fehler (T2); nie eine Nachricht oder ein Token in eine Logzeile |
| V13 API und Web Service | **ja** | Kein `Origin`-Header; Redirects werden nicht gefolgt; alle URLs aus der konfigurierten Basis-URL (SSRF-Grenze); kein Long Polling, also keine bis 30 Sekunden offene Verbindung |
| V14 Configuration | **ja** | Der neue Admin-Wert ist keine `sensitive`-Checkbox (sonst verschlüsselt und unlesbar), Default an, Wirkung fail-loud am Werkzeug, Aktivierungszyklus dokumentiert |

### Bekannte Bedrohungsmuster für diesen Stack

| Muster | STRIDE | Standard-Gegenmassnahme |
|--------|--------|-------------------------|
| Modellgesteuertes, erfundenes Konversations-Token | Spoofing, Denial of Service | `_path_token` plus Suche in der eigenen Konversationsliste; nie `GET /room/{token}` mit einem Modell-Token, weil ein 404 dort einen Brute-Force-Versuch für die IP aller Nutzer registriert (T10) |
| Nachricht an den falschen Empfänger | Tampering, Information Disclosure | Adressierung ausschliesslich per Token aus `talk_browse`; die Antwort nennt den Anzeigenamen der Konversation zurück, damit ein Fehlgriff sichtbar wird |
| Sammel-Erwähnung als Verstärker | Denial of Service (Aufmerksamkeit), Repudiation | `@all`/`@here` mit Wortgrenze abgelehnt; `mentionPermissions` als Begründung im Fehlersatz |
| Doppelte Nachricht durch Retry | Tampering | Kein Retry auf dem POST, Nachrichten-Id in der Antwort, Hinweis in der Tool-Beschreibung |
| Lesen, das schreibt (Lesemarker für Dritte sichtbar) | Tampering | Vier Parameter im Client plus Live-Messung vor und nach dem Lesen (T6); es gibt keinen Reparaturweg, weil `DELETE chat/{token}/read` per Gate verboten ist |
| Fremder Chattext im Modellkontext | Tampering (Prompt Injection) | `marks.without_marks` auf jeden Nachrichtentext und jeden Anzeigenamen; Kappungsmarkierung **ausserhalb** des Textes; Systemnachrichten weg |
| Ausgangskanal in fremde Hände (Lethal Trifecta) | Information Disclosure | Der instanzweite Schalter (TALK-04) ist genau diese Gegenmassnahme; die Benennung der Kette selbst ist SEC-01 in Phase 10 und darf hier nicht vorweggenommen werden, weil Mail-Lesen noch nicht existiert |
| Zugriff auf eine fremde Konversation | Elevation of Privilege | Impersonation trägt die Talk-ACL; Zwei-Konten-Negativbeweis wird für Talk erweitert |
| Geplanter Versand als Umgehung des Schalters | Tampering | `/schedule` als Gate-Nadel (T14) |

## Environment Availability

Gemessen am 2026-08-21 auf dem Entwicklungsrechner.

| Abhängigkeit | Gebraucht für | Verfügbar | Version | Ausweg |
|--------------|---------------|-----------|---------|--------|
| Docker Engine | Integrationstests | ja | läuft | keiner nötig |
| HaRP-Topologie `nc-mcp-exapp` | Impersonation, Berechtigungstreue | ja, `nc-mcp-exapp-nc` up 20 h und healthy, HaRP, Caddy und Registry up 29 h | NC **34.0.3**, AppAPI 34.0.0 | `docker compose -p nc-mcp-exapp -f compose.exapp.yml up -d --wait` plus `scripts/bootstrap_exapp.sh` |
| Testinstanz `nc-mcp-test` | App-Passwort-Integrationsebene | ja, up 6 Tage und healthy | notes 6.0.1, deck 1.18.3, tables 2.2.2 | `scripts/bootstrap_test_nc.sh` |
| App `spreed` | TALK-01 bis TALK-03 | **nein, auf keiner der beiden Instanzen** | soll 24.0.4 | `occ app:install spreed`, Store aus dem Container erreichbar (in Phase 8 mit 200 verifiziert); `ensure_app spreed` in beide Bootstrap-Skripte |
| Testkonversationen | Integrationstests | nein | - | `occ talk:room:create <name> --user <u> --owner <u>` und ein zweiter Raum mit `--readonly`; `talk:room:update --readonly` als Alternative. Idempotent nach Namen, weil das Kommando bei zweitem Aufruf einen zweiten Raum anlegt |
| App `tables` 2.2.2, `mail` 5.11.1 | Phasen 8 und 10 | ja (exapp-Topologie), `tables` ja (Testinstanz) | wie oben | keiner nötig |
| ExApp-Image im Registry | **nicht nötig für diese Phase** | Tag 0.1.2 vorhanden, Repo auf 0.1.3 | - | Die Tests sprechen Nextcloud direkt an bzw. laufen in-process; ein Rebuild gehört zu EXAPP-07 in Phase 11 |
| `uv` | jedes Python-Kommando | ja | im Projekt etabliert | keiner (System-Python ist defekt) |

**Fehlende Abhängigkeiten ohne Ausweg:** keine.
**Fehlende Abhängigkeiten mit Ausweg:** `spreed` per `occ app:install` (idempotent über
`ensure_app`), Testkonversationen per `occ talk:room:create`.

Zwei Hinweise zur Topologie, die im Plan stehen sollten:

1. **Talk braucht für Chat kein Signaling.** Der interne Signaling-Server genügt; ein
   High-Performance-Backend (Janus, nats, signaling) ist nur für Anrufe nötig. Die zwei
   benutzten Routen sind reine OCS-Aufrufe gegen die Datenbank. Der Installationsschritt ist
   damit so billig wie bei Tables.
2. **Eine per `occ` deaktivierte App bleibt in `/cloud/capabilities` sichtbar, bis die
   Nextcloud neu startet** (Befund aus Phase 1). Ein Degradations-Test für `spreed` braucht
   also den Neustart; unser Cache ist nicht die Ursache.

*Runtime State Inventory: entfällt. Diese Phase ist kein Rename, Refactor oder Migration. Der
Zustand ausserhalb von git (installierte Nextcloud-Apps, Testkonversationen, gesetzter
Admin-Wert in der ExApp-Konfiguration) ist in der Tabelle oben erfasst und wird über die
Bootstrap-Skripte reproduzierbar. Ein Punkt verdient trotzdem eine Zeile im Plan: ein einmal in
der Nextcloud gespeicherter Admin-Wert überlebt jedes Neubauen des Containers, und ein auf
"aus" gesetzter Talk-Schalter würde einen späteren Testlauf ohne erkennbaren Grund rot machen.
Der Integrationstest sollte den erwarteten Zustand deshalb feststellen und nicht annehmen.*

*Validation Architecture: entfällt, `workflow.nyquist_validation` ist in
`.planning/config.json` ausdrücklich `false`.*

## Assumptions Log

| # | Annahme | Abschnitt | Risiko, wenn falsch |
|---|---------|-----------|---------------------|
| A1 | Der Körper einer 304-Antwort ist leer oder wird von uns ohnehin nicht gelesen | T2 | Gering: die Empfehlung prüft den **Statuscode** vor jedem Parsen, das Ergebnis ist also unabhängig davon, ob Nextcloud bei 304 noch einen Envelope mitschickt |
| A2 | `occ app:install spreed` läuft auf beiden Instanzen durch | Environment | Gering: derselbe Weg hat für `notes`, `deck`, `tables` und `mail` funktioniert, und der Store ist aus den Containern erreichbar. Rückfall (Handinstallation in `custom_apps`) ist in beiden Bootstrap-Skripten dokumentiert |
| A3 | Die geschätzten Schemagrössen (rund 800 plus 700 Bytes) halten das Gate von 15000 | Falle 8 | Gering: die Anhebung erfolgt gegen eine **Messung**. Die Schätzung sagt nur voraus, dass es knapp wird; reisst es, ist die Anhebung mit Messzeile Teil desselben Commits |
| A4 | `ocs_post` mit JSON-Körper erreicht Talks Controller-Parameter korrekt | Muster, Codebeispiel | Gering: Nextclouds App-Framework liest JSON-Körper in die Controller-Parameter, und `tables_create_row` sendet über denselben Helfer erfolgreich. Der Integrationstest zeigt es sofort |
| A5 | Der Anzeigename einer Eins-zu-eins-Konversation kommt brauchbar in `displayName` an, während `name` dort ein JSON-Array ist | Feldauswahl | Gering: `RoomFormatter` setzt `displayName` über `$room->getDisplayName($userId)`, und der Eins-zu-eins-Zweig füllt `name` aus den Teilnehmer-Ids. Im ersten Integrationslauf sichtbar |
| A6 | 800 Zeichen sind die richtige Kappe je Nachricht | Muster 7 | Mittel: eine zu kleine Kappe schneidet Sinn ab, eine zu grosse kostet Kontext. Die Zahl ist eine Setzung, keine Messung, und gehört als benannte Konstante an eine Stelle, damit Phase 11 sie gegen `prepare_context` nachjustieren kann |
| A7 | Weg A des Admin-Schalters (Export nach `os.environ` beim Start) ist mit D-20 vereinbar | TALK-04 | Mittel: es ist kein Modulzustand im Sinne des Gates (`os.environ` ist die Prozessumgebung, die Schreibstelle liegt vor dem ersten Socket), aber es ist eine neue Art von Zeile in diesem Projekt. Die Entscheidung gehört in die Plan-Diskussion und in eine Kommentarzeile mit Begründung, nicht in einen stillen Einzeiler |

## Offene Fragen

1. **Welcher Leseweg für den Admin-Schalter (T15)?**
   - Was wir wissen: Weg A passt zum bestehenden Muster und braucht keinen neuen Modulzustand,
     Weg B macht den Schalter sofort wirksam, kostet aber einen Roundtrip pro Sendevorgang und
     einen zweiten Fehlermodus.
   - Was unklar ist: ob der Owner für einen Sicherheitsschalter den Aktivierungszyklus
     akzeptiert, den die fünf bestehenden Werte schon haben, oder Sofortwirkung verlangt.
   - Empfehlung: **Weg A**, mit dem Aktivierungszyklus in der Feldbeschreibung, in
     `docs/oauth-setup.md` und im Fehlersatz des Werkzeugs. Begründung: Gleichbehandlung mit
     den fünf bestehenden Werten, kein neuer Zustand, keine neue Ausfallart. Weg B bleibt als
     benannte Ausbaustufe dokumentiert.

2. **Bekommt `talk_browse(level="conversations")` einen Cursor?**
   - Was wir wissen: die Liste ist serverseitig nicht paginierbar, die Kappe liegt bei 50, und
     eine Instanz mit mehr als 50 Konversationen pro Nutzer ist realistisch.
   - Was unklar ist: ob ein zweiter Seitenaufruf über einen selbstgebauten Offset (die ganze
     Liste holen und weiter hinten schneiden) den Schemaplatz wert ist, oder ob `truncated`
     plus der Hinweis "verfeinere über unified_search" ehrlicher ist.
   - Empfehlung: **kein Cursor auf der Konversationsebene.** Ein Offset-Handle würde bei jedem
     Aufruf die ganze Liste erneut holen und nur anders schneiden, und die relevanten
     Konversationen stehen nach der Sortierung nach `lastActivity` oben. `truncated: true` plus
     die Gesamtzahl im Envelope sagt die Wahrheit und kostet nichts. Auf der Nachrichtenebene
     ist der Cursor dagegen zwingend (T8).

3. **Wird der Systemnachrichten-Filter abschaltbar?**
   - Was wir wissen: TALK-02 verlangt "Systemnachrichten per Default draussen", was einen
     Parameter erlauben würde.
   - Was unklar ist: ob irgendein Anwendungsfall sie braucht.
   - Empfehlung: **kein Parameter.** Ein `include_system`-Schalter kostet Schema-Bytes für
     einen Nutzen, den niemand belegt hat, und die Positivliste (Muster 6) ist die schärfere
     Aussage. Wenn ein Abnehmer sie später braucht, ist es eine Zeile.

4. **Zeitstempel als Zahl oder als ISO-Zeichenkette?**
   - Was wir wissen: `tools/notes.py` reicht `modified` als Zahl durch, `tools/calendar.py`
     arbeitet mit ISO, weil ICS es so verlangt.
   - Was unklar ist: wie gut ein Modell einen Unix-Zeitstempel in eine Aussage über "heute"
     verwandelt, ohne zu raten.
   - Empfehlung: **durchreichen wie Notes**, weil das die Präzedenz dieser Codebasis ist und
     rund 700 Bytes pro Verlaufsantwort spart. Falls die Planung es anders entscheidet, dann
     einheitlich für beide Ebenen und mit einer Zeile Begründung im Docstring.

## Quellen

### Primär (HIGH)

- nextcloud/spreed, Tag **v24.0.4** (Tag-Objekt `fcfa10588c14c53e7179b2de09850b0a6503aa42` über
  die GitHub-API bestätigt): `lib/Controller/ChatController.php`,
  `lib/Controller/RoomController.php`, `lib/Controller/PageController.php`,
  `lib/Service/RoomFormatter.php`, `lib/Middleware/InjectionMiddleware.php`,
  `lib/Participant.php`, `lib/Model/Attendee.php`, `lib/Model/Message.php`, `lib/Room.php`,
  `lib/Config.php`, `lib/Capabilities.php`, `lib/Chat/ChatManager.php`,
  `lib/Chat/Parser/UserMention.php`, `lib/Manager.php`, `lib/Search/MessageSearch.php`,
  `lib/Search/ConversationSearch.php`, `lib/Command/Room/Create.php`,
  `lib/Command/Room/Update.php`, `lib/Exceptions/PermissionsException.php`
- nextcloud/spreed `openapi.json` (Tag v24.0.4): vollständige Parameterlisten, Pflichtfelder,
  Statuscodes und Schemata `Room`, `BaseMessage`, `ChatMessage`, `DeletedChatMessage`
- nextcloud/server, `stable34`: `lib/private/AppFramework/OCS/V2Response.php` (die Herkunft von
  `ocs.meta.statuscode`, Grundlage von T1)
- Nextcloud App Store API, `https://apps.nextcloud.com/api/v1/platform/34.0.0/apps.json`, heute
  abgefragt: `spreed` 24.0.4 (`>=34.0.0 <35.0.0`, 2026-08-13)
- Eigene Codebasis, gelesen am 2026-08-21: `nextcloud/clients/{ocs,tables}.py`,
  `nextcloud/capabilities.py`, `tools/{tables,marks,notes,deck}.py`, `server/{__init__,reg_tables}.py`,
  `paging.py`, `ids.py`, `provider_map.py`, `config.py`, `deps.py`, `entry_exapp.py`,
  `exapp/{admin_settings,config_values}.py`, `exapp/ui/strings.py`, `oauth/registry.py`,
  `tests/contract/{test_tool_surface,test_no_destructive_calls}.py`,
  `tests/unit/{test_exapp_admin_settings,test_exapp_config_values}.py`,
  `scripts/{check_tool_budget,acceptance_all_tools}.py`, `scripts/bootstrap_{exapp,test_nc}.sh`,
  `README*.md`, `docs/{oauth-setup,client-setup,conference-demo}.md`, `appinfo/info.xml`,
  `.planning/config.json`
- Live gemessen: `uv run python scripts/check_tool_budget.py` (12801 Bytes, 18 Werkzeuge, Gate
  15000, Pro-Tool-Deckel 1400); `docker ps` (beide Topologien laufen);
  `docker exec nc-mcp-exapp-nc php occ app:list` und dasselbe auf `nc-mcp-test` (`spreed` auf
  keiner Instanz installiert, `tables` 2.2.2 auf beiden, `mail` 5.11.1 auf der
  exapp-Topologie); `occ status` (NC 34.0.3)

### Sekundär (MEDIUM)

- `.planning/research/{SUMMARY,ARCHITECTURE,STACK,PITFALLS,FEATURES}.md` (2026-08-21):
  Meilenstein-Kernrecherche, an den in T1 bis T15 genannten Stellen korrigiert
- `.planning/phases/08-erreichbarkeits-spike-und-tables/08-RESEARCH.md` und `08-05-SUMMARY.md`:
  die elf Korrekturen und die Messwerte der Tables-Phase, insbesondere K5 (dieselbe
  Fehlerklasse wie T3), K9 (`ocs_post` existiert), K8 (`ids.py` bleibt unberührt) und der
  Befund zu leeren 4xx-Körpern
- `.planning/{ROADMAP,REQUIREMENTS,STATE}.md`: gesetzte Entscheidungen und Requirement-Wortlaut

### Tertiär (LOW)

- keine. Jede Einzelaussage dieser Datei ist entweder gegen den Quellcode des Tags v24.0.4,
  gegen die `openapi.json` der App, gegen die eigene Codebasis oder gegen eine laufende Instanz
  geprüft, oder sie steht im Assumptions Log.

## Metadaten

**Konfidenz je Bereich:**
- Talk-Routen, Parameter, Defaults, Statuscodes, Header: HIGH (Tag v24.0.4 plus `openapi.json`
  gelesen, Version gegen den Store abgeglichen)
- Berechtigungs- und Schreibschutz-Semantik (T3, T4): HIGH (vier zusammenhängende Quelldateien
  gelesen: `Participant`, `Attendee`, `Config`, `InjectionMiddleware`)
- Nebenwirkungs-Semantik des Lesens (T6): HIGH für den Quellcode, und genau deshalb die
  Empfehlung, das Kriterium zusätzlich live zu messen statt es aus dem Quellcode zu behaupten
- Codebasis-Anknüpfungspunkte, mechanische Checkliste, Zeilennummern: HIGH (Dateien gelesen,
  Budget und Instanzstand live gemessen)
- Admin-Schalter-Kette: HIGH für den bestehenden Teil (alle beteiligten Dateien gelesen),
  MEDIUM für den Leseweg im Tool (Entscheidung, keine Messung; siehe Offene Frage 1 und A7)
- Byte-Kappe je Nachricht und Zeitstempelform: MEDIUM (Setzungen, A6 und Offene Frage 4)

**Recherchedatum:** 2026-08-21
**Gültig bis:** 2026-09-20 (30 Tage; Talk veröffentlicht etwa monatlich, deshalb die Version vor
dem ersten Integrationstest gegen `occ app:list` gegenprüfen)
