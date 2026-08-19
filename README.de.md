[English](README.md) | **Deutsch** | [Français](README.fr.md)

> Die englische README (README.md) ist die maßgebliche Fassung; diese Übersetzung wird nachgezogen.

# MCP Connector für Nextcloud

Ein kuratierter MCP server, der Ihr Nextcloud (Dateien, Kalender, Notizen, Deck, Kontakte) mit KI-Assistenten
wie Claude, Cursor, ChatGPT oder Ihren eigenen Agenten verbindet.

**Dieser Server kann niemals etwas löschen, überschreiben oder neu teilen.**

Dieser Satz ist die Design-Einschränkung, kein Versprechen guten Verhaltens. Der Server implementiert
keinen einzigen destruktiven Aufruf: kein DELETE, kein MOVE, kein Überschreiben, keine Änderung von
Freigaben. Schreibende Tools legen nur neu an, und eine Namenskollision wird mit einer klaren Ablehnung
beantwortet statt mit einem stillen Überschreiben.

Zwei weitere Eigenschaften folgen aus derselben Idee:

- **Der Assistent sieht nie mehr als Sie.** Jede Anfrage läuft mit Ihren eigenen Nextcloud-Zugangsdaten,
  sodass die Nextcloud-Berechtigungen unverändert gelten.
- **Ein bewusst kleiner Tool-Satz.** Die 16 Tools sind so kuratiert, dass dieser Server neben Ihre
  anderen MCP server passt, selbst in Clients mit einer harten Tool-Obergrenze.

Lizenz: AGPL-3.0-or-later. App-ID, Paketnamen und Repository-Name sind eingefroren, siehe
[docs/app-id-freeze.md](docs/app-id-freeze.md).

## Status

Version 0.1.0, im Nextcloud App Store gelistet und als Nextcloud-ExApp über AppAPI
installierbar. Was heute vorliegt und wo jede dieser Aussagen festgehalten ist:

- Alle 16 Tools des v1-Satzes sind implementiert, und die Tool-Tabelle weiter unten wird nicht
  mehr von Hand gepflegt: ein Contract-Test liest die aktive Tool-Registry und schlägt fehl,
  wenn ein Name oder eine Berechtigungsstufe in der Tabelle davon abweicht.
- Die OAuth-2.1-Anmeldung ist Ende zu Ende gegen die zwei gehosteten Konnektoren belegt, für
  die sie gebaut wurde, Claude.ai und ChatGPT, samt dynamischer Client-Registrierung und
  Refresh-Rotation. Der Ablauf und die Messungen stehen in
  [docs/oauth-setup.md](docs/oauth-setup.md).
- Verwaltung pro Konto: jedes Konto pausiert oder setzt seinen eigenen MCP-Zugriff fort und
  trennt jede einzelne verbundene Assistenz auf der Verbindungsseite dieser App, die Nextcloud
  unter Einstellungen, Sicherheit, MCP Connector verlinkt.
- `prepare_context` bündelt eine Suche und die kommende Woche an Terminen in einem Aufruf, eine
  Frage kostet damit einen Rundlauf statt mehrerer.

Schritt-für-Schritt-Einrichtung für Claude Desktop, Claude Code und Remote-HTTP-Clients, inklusive der
drei Fehler, die tatsächlich auftreten: **[docs/client-setup.md](docs/client-setup.md)**.

### OAuth 2.1

Als Nextcloud-ExApp installiert, ist dieser Server zugleich sein eigener OAuth-2.1-Autorisierungsserver,
gemäß der MCP-Autorisierungsspezifikation: dynamische Client-Registrierung, PKCE S256, an die
Zielgruppe gebundene Tokens, Refresh-Rotation mit Wiederverwendungserkennung und sofortigem Widerruf.
Ein Client wie Claude.ai oder ChatGPT erhält eine URL, meldet den Nutzer auf den eigenen Seiten von
Nextcloud an und sieht niemals ein Passwort oder ein App password. Die Verbindung erscheint unter
Einstellungen, Sicherheit, Geräte und Sitzungen und kann dort beendet werden.

Was eine Administratorin einstellen muss, was ein Nutzer eingibt und die Messungen hinter beidem:
**[docs/oauth-setup.md](docs/oauth-setup.md)**.

## FAQ

**Mein Administrator hat diese App installiert. Kann ich sie für mich abschalten?**

Ja, und Sie brauchen Ihren Administrator dafür nicht. Im Hintergrund läuft nichts: der
Connector handelt ausschließlich auf Anfrage einer Assistenz, die Sie selbst verbunden haben, es
gibt keinen Cron, keine Indizierung und keine Telemetrie. Ihr eigenes Konto hat einen Schalter
auf der Verbindungsseite dieser App, die Nextcloud unter Einstellungen, Sicherheit, MCP
Connector verlinkt, und jede verbundene Assistenz lässt sich einzeln trennen, wobei der
Connector ihr Nextcloud-App-Passwort an Nextcloud zurückgibt.

Die vollständige Antwort samt der Grenze zwischen dem, was diese App steuert, und dem, was der
Anbieter Ihrer Assistenz entscheidet: **[docs/faq.md](docs/faq.md)** (englisch).

## Schnellstart (stdio)

Sie benötigen ein Nextcloud-App password, nicht Ihr Anmeldepasswort. Erstellen Sie eines in Nextcloud
unter Einstellungen, Sicherheit, Geräte und Sitzungen.

```bash
uv tool install nextcloud-mcp-connector   # or: uv run nc-mcp inside a checkout

export NC_MCP_URL=https://cloud.example.com
export NC_MCP_USER=alice
export NC_MCP_APP_PASSWORD=xxxxx-xxxxx-xxxxx-xxxxx-xxxxx

nc-mcp
```

Client-Konfiguration, zum Beispiel für Claude Desktop oder Cursor:

```json
{
  "mcpServers": {
    "nextcloud": {
      "command": "nc-mcp",
      "env": {
        "NC_MCP_URL": "https://cloud.example.com",
        "NC_MCP_USER": "alice",
        "NC_MCP_APP_PASSWORD": "xxxxx-xxxxx-xxxxx-xxxxx-xxxxx"
      }
    }
  }
}
```

## HTTP-Modus

Derselbe Server spricht auch Streamable HTTP für Remote-Clients:

```bash
export NC_MCP_URL=https://cloud.example.com
export NC_MCP_ALLOWED_HOSTS=mcp.example.com
uv run uvicorn mcp_connector.entry_http:app --host 127.0.0.1 --port 8765
```

Der MCP-Endpunkt ist `POST /mcp`, und `GET /health` antwortet ohne Authentifizierung mit
`{"status":"ok","version":"..."}`. Ein Endpunkt bedient beide Protokoll-Generationen: Clients auf der
aktuellen Spezifikation und Clients auf Basis des MCP SDK 1.x werden anhand der Protokollversion ihrer
Anfrage weitergeleitet, und ein Neustart kann keine Konversation unterbrechen, weil der Server keinen
Sitzungszustand hält.

Zugangsdaten werden in diesem Modus nicht aus der Umgebung gelesen. Sie reisen pro Anfrage im
`Authorization`-Header (Basic, Nutzer und App password) und werden unverändert an Nextcloud
weitergereicht, das sie authentifiziert. Der Server behandelt den Header nie als eigene
Identitätsbehauptung und speichert nichts, sodass eine Bereitstellung mehrere Nutzer ohne einen
Zugangsdaten-Speicher bedienen kann.

Für Einzelnutzer-Bereitstellungen ist stattdessen ein statisches Bearer token verfügbar: setzen Sie
`NC_MCP_STATIC_BEARER`, und das Nextcloud-Konto wird wie im stdio-Modus aus der Umgebung genommen. Die
beiden HTTP-Modi schließen sich gegenseitig aus.

`NC_MCP_ALLOWED_HOSTS` ist in der Praxis nicht optional. Ohne den Wert akzeptiert die Transportschicht
nur `Host: localhost` und `Host: 127.0.0.1` und beantwortet jede andere Anfrage mit `421 Misdirected
Request`, bevor irgendein MCP-Code läuft. Beachten Sie, dass es sich um den `Host`-Header eingehender
Anfragen handelt, nicht um die Bind-Adresse: `--host 0.0.0.0` lässt niemanden herein.

## Umgebungsvariablen

| Variable | Modus | Erforderlich | Zweck |
|----------|------|----------|---------|
| `NC_MCP_URL` | alle | ja | Basis-URL Ihres Nextcloud, inklusive eines Unterpfads, falls Sie einen verwenden |
| `NC_MCP_USER` | stdio, statisches Bearer | ja | Nextcloud-Nutzer-ID |
| `NC_MCP_APP_PASSWORD` | stdio, statisches Bearer | ja | App password aus Einstellungen, Sicherheit, Geräte und Sitzungen |
| `NC_MCP_ALLOWED_HOSTS` | HTTP | in der Praxis ja | Komma-getrennte Allowlist der zulässigen `Host`-Header dieses Servers; ein Port-Wildcard wird je Name ergänzt |
| `NC_MCP_STATIC_BEARER` | HTTP | nein | Statisches Bearer token für Einzelnutzer-Bereitstellungen; ohne es authentifizieren sich Clients pro Anfrage |
| `NC_MCP_DISABLE_DNS_REBINDING_PROTECTION` | HTTP | nein | Nur hinter einem Proxy auf `true` setzen, der den `Host`-Header kontrolliert |
| `NC_MCP_PUBLIC_URL` | statisches Bearer, ExApp | ja für OAuth | Öffentliche URL dieses Servers. Im ExApp-Modus ist sie der Issuer des Autorisierungsservers und die Resource des Protected-Resource-Dokuments, sodass OAuth ohne sie nicht funktioniert |
| `NC_MCP_OAUTH_DCR` | ExApp | nein | Dynamische Client-Registrierung, an, sofern nicht abgeschaltet |
| `NC_MCP_OAUTH_ALLOWLIST_ONLY` | ExApp | nein | Nur gelistete Clients dürfen autorisieren; eine leere Liste verschließt dann die Tür für alle |
| `NC_MCP_OAUTH_ALLOWED_CLIENTS` | ExApp | nein | Komma-getrennte Client-IDs oder Redirect-URIs, nur gelesen, wenn die Allowlist aktiv ist |

Keine Zugangsdaten werden jemals protokolliert, in keinem Modus.

## Tools

Berechtigungsstufen: **read** bedeutet, das Tool liest nur, **create-only** bedeutet, das Tool kann
neue Objekte anlegen, aber niemals bestehende ändern oder entfernen.

| Tool | Berechtigung | Was es tut |
|------|------------|--------------|
| `files_search` | read | Sucht Dateien und Ordner nach Namen per WebDAV-Suche; Inhalte werden nicht indexiert |
| `files_list` | read | Listet die direkten Kinder eines Ordners, mit Größen und Änderungszeiten |
| `files_read` | read | Liest den Inhalt einer einzelnen Datei |
| `files_upload` | create-only | Lädt eine neue Datei hoch; ein bestehender Pfad wird abgelehnt, nie überschrieben |
| `calendar_list_events` | read | Listet Termine in einem expliziten Zeitraum, mit expliziter Zeitzone |
| `calendar_create_event` | create-only | Legt einen neuen Termin an; bestehende Termine werden nie geändert |
| `notes_search` | read | Findet Notizen nach Titel und Inhalt über den Nextcloud-Notes-Suchprovider |
| `notes_read` | read | Liest eine einzelne Notiz |
| `notes_create` | create-only | Legt eine neue Notiz an; bestehende Notizen werden nie geändert |
| `deck_browse` | read | Durchsucht Deck-Boards, -Stapel und -Karten |
| `deck_create_card` | create-only | Legt eine neue Karte in einem Stapel an; bestehende Karten werden nie geändert |
| `contacts_search` | read | Durchsucht Adressbuch-Kontakte |
| `unified_search` | read | Fragt die Nextcloud-Unified-Search über alle Provider ab, berechtigungsbewusst |
| `prepare_context` | read | Bündelt passende Dateien, Notizen und Karten mit den Terminen der kommenden Woche zu einer Frage |
| `search` | read | OpenAI-kompatibler Sucheinstiegspunkt, delegiert an die Unified-Search |
| `fetch` | read | OpenAI-kompatibler Abrufeinstiegspunkt, löst eine ID zu einer Datei, Notiz, Karte oder einem Termin auf |

`search` und `fetch` existieren, weil das ChatGPT-Connector-Profil genau diese beiden Namen und Schemata
verlangt. Sie sind dünne Hüllen über den obigen Tools, keine zweite Implementierung.

### Dateien: was die Suche tatsächlich trifft

`files_search` nutzt die WebDAV-Suche, die **Namen** trifft, nicht Dateiinhalte. Ein Wort, das nur
innerhalb eines Dokuments vorkommt, erzeugt keinen Treffer, und das ist das Verhalten des Protokolls,
kein Mangel dieses Servers. Jede Suchantwort trägt daher denselben Hinweis:

```json
{"query":"budget","folder":"/","count":1,"items":[{"path":"/Docs/budget-2026.md","name":"budget-2026.md","kind":"file","size":2048,"content_type":"text/markdown","modified":"Thu, 14 Aug 2026 10:00:00 GMT","id":"file:4711"}],"note":"matched on names only; contents are not indexed"}
```

Eine Volltextsuche bräuchte eine separat installierte Nextcloud-App, deshalb ist die ehrliche Antwort
der obige Hinweis statt eines stillen leeren Ergebnisses.

`files_list` gibt die direkten Kinder eines Ordners zurück, Ordner zuerst und dann Namen. Der Ordner
selbst ist nie Teil seiner eigenen Auflistung, und ein Pfad, der auf eine Datei zeigt, erhält eine
Erklärung statt einer leeren Liste.

### Lange Listen: Cursor-Handles statt Sitzungen

Eine Liste, die vorzeitig abbrechen musste, sagt das und gibt ein Handle aus:

```json
{"items": ["..."], "truncated": true, "next": "eyJmIjoiLyIsIm8iOjI1LCJxIjoiYnVkZ2V0In0"}
```

Geben Sie diesen Wert als Parameter `cursor` zurück, um fortzufahren. Das Handle ist base64url von
kompaktem JSON und hält die gesamte Position, sodass der Server keine Sitzung führt: ein Handle
funktioniert noch nach einem Server-Neustart und gegen einen anderen Prozess desselben Servers. Es ist
bewusst nicht signiert, weil es kein Geheimnis und keine Berechtigung trägt. Die Zugangsdaten kommen bei
jedem einzelnen Aufruf aus dem Auth-Kanal, sodass ein verändertes Handle nur anders durch die eigenen
Daten des Aufrufers blättern kann. Ein Handle aus einer anderen Abfrage wird abgelehnt, statt still die
falsche Seite zurückzugeben.

### Kalenderzeiten

CalDAV ist die eine Stelle, an der ein kleiner Zeitfehler eine selbstsicher falsche Antwort erzeugt,
deshalb sind die Kalender-Tools darin explizit:

- `start` und `end` sind erforderlich und müssen eine Zone tragen, zum Beispiel `2026-09-01T00:00:00+02:00`
  oder `2026-09-01T00:00:00Z`. Ein Wert ohne Zone wird abgelehnt statt geraten.
- Wiederkehrende Termine werden von Nextcloud selbst expandiert, sodass jede Instanz als absolute Zeit
  zurückkommt. Der optionale Parameter `timezone` (ein IANA-Name wie `Europe/Berlin`) ändert nur, wie
  die Antwort geschrieben wird, nie welche Termine sie enthält.
- Ganztägige Termine sind Datumsangaben ohne Uhrzeit und werden mit `all_day` markiert. Ihr Enddatum ist
  exklusiv, wie RFC 5545 es definiert: ein Termin am 24. Oktober endet am 25. Oktober.
- `calendar_create_event` liest den angelegten Termin einmal zurück und meldet die Zeiten, die der
  Server gespeichert hat, nicht die, um die er gebeten wurde.

### Kontakte

`contacts_search` ist reine Lesefunktion und bleibt es in dieser Version: es gibt überhaupt keinen
CardDAV-Schreibpfad.

- Der Suchbegriff wird von Nextcloud selbst gegen den vollständigen Namen und die Mail-Adressen einer
  Karte abgeglichen, groß-/kleinschreibungs- und akzentunabhängig. Eine Telefonnummer wird zurückgegeben,
  aber nicht durchsucht.
- Jedes Adressbuch des Kontos wird gleichzeitig abgefragt. Eines, das ausfällt, wird unter `degraded`
  benannt, sodass eine Teilantwort sichtbar teilweise ist.
- Die beiden Sammlungen, die Nextcloud für jedes Konto erzeugt, werden ausgelassen: das
  Konten-Verzeichnis der Instanz (`z-server-generated--system`, angezeigt als "Accounts") und die
  Liste "kürzlich kontaktiert". Keine davon ist ein Adressbuch, das der Nutzer pflegt, und eine
  Namenssuche sollte nicht als Nebeneffekt das Verzeichnis einer ganzen Organisation herausgeben.
- Ein Konto ohne eigenes Adressbuch bekommt einen Fehler, der `occ dav:create-addressbook <user> contacts`
  benennt, nie ein leeres Ergebnis: "kein Adressbuch" und "kein passender Kontakt" sind
  unterschiedliche Antworten.

### Deck

Deck ist ein Browse-Tool mit einer Ebene, nicht ein Tool pro Ebene:

```json
{"level":"cards","count":2,"results":[{"id":"card:2:11:101","title":"Deck-Client bauen","stack":"To Do","url":"https://cloud.example.org/index.php/apps/deck/card/101"}]}
```

- `deck_browse(level="boards")` listet die Boards mit `can_edit`, `level="stacks"` braucht eine
  `board_id` und meldet, wie viele Karten ein Stapel enthält, `level="cards"` gibt die Karten selbst
  zurück. Eine ungültige Ebene wird vom Schema zurückgewiesen, und eine fehlende `board_id` benennt den
  Parameter, statt einen zu raten.
- `level="cards"` kostet genau **eine** HTTP-Anfrage pro Board, weil Nextcloud die Karten bereits in der
  Stapel-Antwort mitschickt. Ein Test zählt die Anfragen, gegen den Mock und gegen eine echte Instanz.
- Eine Karten-ID ist die kanonische Langform `card:<board>:<stack>:<card>`, die die Karte über die
  öffentliche Deck-API ohne Nachschlagen adressiert.
- `deck_create_card` legt nur an. Es gibt kein Update, kein Delete und keine Board- oder
  Stapel-Erstellung irgendwo im Deck-Codepfad. Ein Titel länger als 255 Zeichen oder ein Fälligkeitsdatum,
  das nicht ISO-8601 ist, wird vor der Anfrage abgelehnt, und ein Konto, dessen Nextcloud
  Board-Erstellung verbietet, wird gegen die eigenen Berechtigungen des Boards geprüft, sodass ein
  schreibgeschütztes Board erklärt wird statt mit einem 403 beantwortet.

### Cloud-weite Suche

`unified_search` fragt jeden Suchprovider ab, den die Instanz anbietet, gleichzeitig:

```json
{"query":"budget","count":2,"results":[{"id":"file:4711","title":"Budget 2026.md","subline":"in Dokumente","url":"https://cloud.example.org/index.php/f/4711","provider":"files","kind":"file"},{"id":"url:https://cloud.example.org/index.php/call/abc123","title":"Khaled","url":"https://cloud.example.org/index.php/call/abc123","provider":"spreed","kind":"url","resolvable":false}],"note":"matched on names and metadata; file contents are not indexed","degraded":[{"provider":"search-deck-card-board","reason":"The provider did not answer within 15 seconds."}]}
```

- Die Provider-Liste kommt bei jedem Aufruf von Nextcloud und ist nie fest verdrahtet, weil sie den
  installierten Apps folgt. Eine vor einer Minute aktivierte App ist ohne Neustart durchsuchbar.
- Jeder Provider bekommt sein eigenes Timeout. Einer, der ausfällt oder hängt, wird unter `degraded` mit
  einem Grund benannt, sodass eine Teilantwort immer sichtbar teilweise ist, nie eine still verkürzte
  Liste.
- Berechtigungen sind Sache von Nextcloud: jeder Provider läuft als der authentifizierte Nutzer, und
  dieser Server hält keinen Index und cacht kein Ergebnis.
- Treffer aus Files, Notes und Deck tragen eine ID, die die Lese-Tools verstehen. Alles andere bekommt
  eine `url:`-ID und `resolvable: false`, weil eine erfundene ID zum falschen Objekt auflösen würde. Der
  Provider von Deck meldet nur eine Karten-ID, sodass seine kurze Form `card:<cardId>` ebenso markiert
  wird.
- `providers` verengt den Fan-out auf eine komma-getrennte Teilmenge, zum Beispiel `files,notes`. Ein
  Name, den die Instanz nicht kennt, wird unter `degraded` gemeldet, statt still ignoriert zu werden.
- `limit` gilt pro Provider und wird von Nextcloud selbst erneut gedeckelt. Wenn ein Provider paginiert,
  kommt sein Cursor unter `cursors` zurück.

### ChatGPT-Connector-Profil

`search` und `fetch` sind die beiden Namen, nach denen der OpenAI-Connector sucht. Ihre Parameter sind
`query` und `id`, ihre Feldnamen sind festgelegt, und beide sind die einzigen Tools dieses Servers, die
ein Output-Schema mitliefern, weil ChatGPT die Nutzlast als strukturierten Inhalt liest:

```json
{"results":[{"id":"file:4711","title":"Budget 2026.md","url":"https://cloud.example.org/index.php/f/4711","text":"in Dokumente"}]}
```

```json
{"id":"file:4711","title":"Budget 2026.md","text":"# Budget 2026 ...","url":"https://cloud.example.org/index.php/f/4711","metadata":{"kind":"file","path":"/Dokumente/Budget 2026.md","content_type":"text/markdown"}}
```

- `search` fügt keine zweite Suche hinzu. Es ruft `unified_search` auf und benennt die Felder um, sodass
  beide Tools dieselbe Frage auf dieselbe Weise beantworten.
- Jeder Treffer trägt eine nicht-leere, absolute URL auf der konfigurierten Instanz. ChatGPT erzeugt nur
  dann Zitations-Metadaten, solange `url` ein nicht-leerer String ist, sodass eine leere die Quelle still
  fallenlassen würde.
- `fetch` löst die vier ID-Arten auf, die die Lese-Tools verstehen: `file:<fileid>` (nachgeschlagen über
  eine einzige WebDAV-Suche auf `oc:fileid`), `note:<id>`, `card:<board>:<stack>:<card>` inklusive der
  kurzen Form `card:<cardId>` aus dem Deck-Suchprovider, und `event:<calendar>:<object>`.
- Eine `url:`-ID wird ehrlich beantwortet: dieser Server fordert nie eine URL an, die aus einem
  Sucheintrag stammt, und sagt das, statt Inhalt zu erfinden. Ein unbekanntes Präfix wird mit der Liste
  der gültigen abgelehnt, weil eine Chat-Nachricht als Notiz aufzulösen schlimmer ist als ein Fehler.
- Eine lange Datei wird an derselben Grenze abgeschnitten wie bei `files_read`. Der Schnitt wird
  innerhalb von `text` und erneut in `metadata` markiert, mit dem Offset zum Fortsetzen.

### Optionale Apps

Notes und Deck sind optionale Nextcloud-Apps. Die Tool-Liste ist überall gleich: sie hängt nie davon ab,
welche Apps eine Instanz hat, sodass sie cachebar und für jeden Client vorhersagbar bleibt. Fehlt eine
App, sagt das Tool das in einem Satz und nennt eine Alternative, zum Beispiel "The Notes app is not
installed on this Nextcloud." Kalender und Kontakte brauchen überhaupt keine App: CalDAV und CardDAV sind
Teil des Nextcloud-Kerns.

## Was dieser Server nicht kann

- **Kein Löschen.** Kein Tool setzt ein DELETE gegen Dateien, Termine, Notizen, Karten oder Kontakte ab.
- **Kein Überschreiben.** Schreibvorgänge legen nur neu an. `files_upload` lehnt einen bestehenden
  Zielpfad mit einem klaren Fehler ab, statt ihn zu ersetzen, und die create-Tools rühren nie ein
  bestehendes Objekt an.
- **Kein Verschieben oder Umbenennen.** MOVE und COPY sind nicht implementiert.
- **Keine Freigabe-Änderungen.** Der Server erstellt, ändert oder entfernt keine Freigaben und ändert nie
  Berechtigungen.
- **Kein Admin-Zugriff.** Der Server handelt als ein Nutzer mit einem App password und erbt genau die
  Berechtigungen dieses Nutzers.
- **Keine Volltextsuche in Dateiinhalten**, sofern nicht die Nextcloud-Full-text-search-App installiert
  und konfiguriert ist. Ohne sie trifft die Dateisuche Namen und Metadaten.
- **Keine Hintergrundjobs, keine Synchronisation, keine lokale Kopie Ihrer Daten.** Jeder Aufruf geht an
  Ihr Nextcloud und kehrt zurück.

## Bekannte Einschränkungen

Dinge, die keine Mängel sind, Sie aber einmal überraschen werden. Jede davon ist ein bewusster Kompromiss,
und jede ist in der Antwort sichtbar, die das Tool gibt, statt hinter einem leeren Ergebnis verborgen.

| Einschränkung | Was Sie sehen | Was zu tun ist |
|------------|--------------|------------|
| **Suche trifft Namen, nicht Inhalte** | Jede Suchantwort trägt `"note":"matched on names only; contents are not indexed"` | Installieren und konfigurieren Sie die Nextcloud-Full-text-search-App, oder suchen Sie nach Dateinamen |
| **Ein mit `occ user:add` erstelltes Konto hat keinen Kalender** | `calendar_list_events` gibt einen Fehler zurück, der den fehlenden Kalender benennt | `occ dav:create-calendar <user> personal`, oder melden Sie sich einmal über die Web-UI bei Nextcloud an, was ihn erstellt |
| **Dasselbe gilt für das Adressbuch** | `contacts_search` benennt den Ausweg, statt nichts zurückzugeben | `occ dav:create-addressbook <user> contacts` |
| **Notes und Deck sind optionale Apps** | Die Tools bleiben überall in `tools/list` und antworten "The Notes app is not installed on this Nextcloud." | Installieren Sie die App, oder ignorieren Sie diese fünf Tools |
| **Nichts kann gelöscht oder überschrieben werden** | `files_upload` lehnt einen bestehenden Pfad mit einem Konflikt ab, und es gibt überhaupt kein Update- oder Delete-Tool | Wählen Sie einen anderen Namen. Das ist die Design-Einschränkung, kein fehlendes Feature |
| **Keine Sitzung, also kein serverseitiger Paging-Zustand** | Eine lange Liste gibt ein `next`-Handle zurück, das Sie erneut übergeben | Nichts. Das Handle übersteht einen Neustart, und genau das ist der Sinn |
| **Kalender brauchen ein explizites Zeitfenster mit Zone** | Ein `start` oder `end` ohne Zone wird abgelehnt | Senden Sie `2026-09-01T00:00:00+02:00` oder `...Z`. Eine geratene Zone ist eine selbstsicher falsche Antwort |
| **Eine IP für viele Nutzer löst den Brute-Force-Schutz aus** | `429` nach einem falschen App password, für alle hinter derselben Bereitstellung | Warten Sie und verwenden Sie ein korrektes App password; siehe den Troubleshooting-Abschnitt in der Client-Einrichtung |
| **Der ExApp-Modus authentifiziert mit einem App password, noch nicht mit OAuth** | Der Endpunkt `/exapps/mcp_connector/mcp` akzeptiert ein Basic-App password, das HaRP zu Ihrem Nutzer auflöst | Verwenden Sie das App password; OAuth ist der Weg in Phase 3, siehe den ExApp-Abschnitt von [docs/client-setup.md](docs/client-setup.md) |

Phase 2 machte den Server als Nextcloud-ExApp über AppAPI installierbar, wobei jede Anfrage unter der
eigenen Identität des aufrufenden Nutzers läuft. Drei Dokumente halten das fest sowie die beiden Spikes,
von denen es abhing:

- [docs/exapp-install.md](docs/exapp-install.md): die Installation der App als ExApp auf der
  HaRP-Topologie, die Belege, die bekannten Fallstricke und die Nextcloud-AIO-Übergabe an Phase 5.
- [docs/spike-discovery.md](docs/spike-discovery.md): die Discovery-Entscheidung für die
  OAuth-Topologie der Phase 3, mit der gemessenen Matrix und dem Reverse-Proxy-Fallback.
- [docs/spike-dav.md](docs/spike-dav.md): das DAV-Impersonation-Ergebnis, nämlich dass alle sechs
  API-Familien unter einem Impersonation-Modus laufen, sodass es keine Provider-Aufteilung je Familie
  gibt.

## Entwicklung

```bash
uv sync
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

`uv run pytest` startet nichts und braucht nichts. Die beiden schwereren Schichten sind opt-in:

- `uv run pytest -m matrix` startet den HTTP-Server als Subprozess und prüft, dass ein aktueller Client
  und ein Client auf MCP SDK 1.29 beide vom selben Endpunkt bedient werden, und dass die Konversation
  einen Neustart übersteht. Es braucht kein Nextcloud.
- `uv run pytest -m integration` braucht das lokale Test-Nextcloud aus `compose.test.yml`.

## Lizenz

AGPL-3.0-or-later, siehe [LICENSE](LICENSE).
