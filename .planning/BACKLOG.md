# Backlog

Ideas and tasks that are decided in principle but not yet assigned to a phase.
Review with /gsd:review-backlog before planning a new phase.

## BL-01: Findling synergy, README cross-link (after Findling v1.0 release)

**Trigger:** Findling v1.0 (github.com/street1983nk/nextcloud-search) is released
to the app store. Not before, the app is a walking skeleton until then.

**What:** One paragraph in README.md under "Known limitations", row "Search matches
names, not contents": with Findling installed, unified_search answers content hits
including scanned PDFs, because the connector reads the search provider list at
runtime (D-08, tools/search.py) and Findling registers an IProvider. Nothing to
configure on either side. Ask the Findling side (parallel session) for a matching
"works great with" note plus store listing cross-links.

**Why:** Each product closes the other one's biggest gap; the combination is the
local RAG story (assistant finds the passage, files_read fetches the document,
content never leaves the house).

## BL-02: Findling synergy, content-hit permission fidelity test (after Findling v1.0)

**Trigger:** same as BL-01.

**What:** Integration test in this repo, guarded by a skip when Findling is not
installed on the test instance: alice uploads a document whose UNIQUE marker exists
only in the CONTENT (not in the file name, e.g. text inside a PDF), then
(1) positive control: alice finds it over unified_search via the full ExApp chain,
(2) leak test: bob does not, (3) the hit is proven to be a content hit (file name
carries no marker). Extends the existing leak-test methodology from
tests/integration/test_permission_fidelity_exapp.py to content-level results and
proves Findling's PHP recheck holds behind our impersonation.

**Why:** The synergy claim ("assistant searches inside documents, permissions
intact") must be a measured fact before it goes into any README or pitch.

## BL-03: Findling synergy, demo video "Frag deine Cloud" (optional, after BL-02)

**What:** Short promo: assistant is asked a question, unified_search hits the
passage inside a scanned PDF (Findling), files_read fetches it, answer with source.
Both products on screen, on-prem framing. Owner publishes.

**Decision note:** No direct connector-to-Findling tool. Everything goes through
the Nextcloud unified search, so Nextcloud stays the single permission boundary,
as both threat models require.

## BL-04: Lokale Clients (Loopback, private-use scheme) als OAuth-Client

**Befund (03-RESEARCH.md):** Claude Code nutzt Loopback-Redirects und CIMD und
passt nicht ins exakte Redirect-Matching der v1. In v1 bleibt Claude Code auf dem
App-Passwort-Pfad (AUTH-01, funktioniert heute). Spaeter: Loopback-Ausnahme nach
RFC 8252 Abschnitt 7.3 (beliebiger Port auf 127.0.0.1) sauber implementieren.

**Gemessen am 16.08.2026 gegen Staging (03-09-MEASUREMENTS.md, Lauf 4):** Die
Vermutung war falsch. Loopback ist nicht das Hindernis, D-35 lässt ihn zu:
eine Registrierung mit `http://127.0.0.1:49731/callback` allein wird mit 201
angenommen. Cursor scheitert an etwas anderem. Cursor registriert drei
Rückkehradressen auf einmal:

```
cursor://anysphere.cursor-mcp/oauth/callback
https://www.cursor.com/agents/mcp/oauth/callback
http://localhost:8787/callback
```

Die erste ist ein private-use URI scheme. Unsere Regel kennt nur https und
Loopback, und sie prüft das ganze Feld: ein unzulässiger Eintrag lässt die
gesamte Registrierung mit 400 `invalid_redirect_uri` scheitern, obwohl zwei
zulässige Adressen dabeistehen. Gegenprobe: derselbe Rumpf ohne den ersten
Eintrag wird mit 201 angenommen. Cursor zeigt unsere Fehlermeldung wörtlich in
seinem eigenen Log an und verbindet sich nicht.

**Damit sind es zwei getrennte Entscheidungen, nicht eine:**

1. **Alles-oder-nichts beim Feld `redirect_uris`.** Ein Server darf unzulässige
   Einträge auch verwerfen und den Rest registrieren. Dann käme Cursor durch,
   weil es beim Autorisieren ohnehin eine der verbleibenden Adressen wählen
   müsste. Fail-closed ist die strengere und heute gewählte Lesart.
2. **Private-use URI schemes.** RFC 8252 nennt sie in Abschnitt 7.1 als eine der
   drei zulässigen Formen für native Clients; D-35 hat bewusst nur 7.2 (https)
   und 7.3 (Loopback) zugelassen, weil ein Schema auf dem Desktop niemandem
   exklusiv gehört und jede andere Anwendung es abfangen kann. Diese Begründung
   steht weiterhin. Neu ist nur der gemessene Preis: eine ganze Client-Klasse
   bleibt draußen.

**Offen bleibt** die ursprüngliche Portfrage: Cursor benutzt einen festen Port
(8787), also sagt dieser Lauf nichts darüber, ob ein Client mit wechselndem
Loopback-Port an unserem exakten Matching scheitert. Wer das beantworten will,
braucht einen Client, der den Port je Lauf neu wählt (Claude Code ist der
Kandidat).

## BL-05: Client ID Metadata Documents als Nachfolger von DCR

**Anlass (Plan 03-09):** Die MCP-Authorization-Spec fuehrt Client ID Metadata
Documents (CIMD) und markiert Dynamic Client Registration als ueberholt. Heute
traegt dieser Server ausschliesslich DCR; ein Client, der sich per CIMD ausweist
(Claude Code tut das), kann sich hier nicht anmelden.

**Was zu tun waere:** Die Client-Identitaet zusaetzlich aus einem vom Client
genannten Metadatendokument beziehen duerfen, mit denselben Kontrollen wie heute
bei DCR: Rueckkehradressen pruefen, Allowlist-Modus (AUTH-07) greift auch hier,
und ein abgeschaltetes DCR darf nicht ueber CIMD umgangen werden. Die Abholung
des Dokuments ist ein ausgehender Request der Instanz und braucht deshalb eine
eigene Betrachtung (SSRF, Zwischenspeicher, Groessengrenze).

**Warum nicht in v1:** AUTH-04 ist mit DCR erfuellt, beide gehosteten Connectoren
verbinden. CIMD ist die Zukunftssicherung, nicht die Voraussetzung.

## BL-06: Admin-Settings-UI, Ein-Klick-Prinzip (Owner-Vorgabe 17.08.2026)

**Owner-Vorgabe:** Alles soll einfach sein, ein Klick und man ist drin, und
trotzdem muss der Admin die Gelegenheit haben, Einstellungen zu machen.

**Ist-Zustand:** Die Nutzerseite erfuellt das Prinzip weitgehend (URL im
Client einfuegen, anmelden, drin; Schalter und Trennen auf /connections).
Die Admin-Seite ist reine Env-Var-Konfiguration (NC_MCP_OAUTH_DCR,
NC_MCP_OAUTH_ALLOWLIST_ONLY, NC_MCP_OAUTH_ALLOWED_CLIENTS,
NC_MCP_ALLOWED_HOSTS, NC_MCP_PUBLIC_URL, ...). Das kollidiert mit der
Store-Installation per Klick (Phase 5 SC 2): ein Admin, der aus dem App
Store installiert, setzt keine Env-Vars.

**Was zu tun waere (Phase 5):** Admin-Settings-Zugang fuer die
sicherheitsrelevanten Schalter (mindestens DCR an/aus und Allowlist), mit
sicheren Defaults ab Installation, so dass der Ein-Klick-Weg ohne Pflicht-
Konfiguration funktioniert und die Security-Note (oeffentliche Instanzen:
Allowlist AN oder DCR AUS) per UI statt nur per Env erfuellbar ist.
Recherche-Vorbehalt: Declarative Settings sind pull-only (04-RESEARCH);
fuer Admin-Werte, die die ExApp zur Laufzeit braucht, ist der Speicherort
(appconfig via AppAPI vs. eigener Store) zu klaeren.

**Warum nicht in Phase 4:** Phase 4 war der Per-User-Slice; die
Admin-Schalter haengen an der Store-Paketierung (EXAPP-04/05).

## BL-07: Datenschutz-Doku + Datenweitergabe-Disclosure (Owner-Frage 17.08.2026)

**STATUS 17.08.: Doku-Teil ERLEDIGT** (docs/privacy.md gepusht; Datenweitergabe als Prosa in info.xml <description>, weil der Store kein data-sharing-Feld hat, siehe 05-store-research.md Frage 4). Offen bleibt nur, den Hinweis in die spaeteren Client-Setup-Docs zu spiegeln.

**Anlass:** Datenschutz-Review des Connectors. Der Connector selbst ist
datenschutzfreundlich (self-hosted, keine Telemetrie, keine Calls ausser an
die eigene Nextcloud, App-Passwoerter verschluesselt at rest, Token nur als
Hash, Zweckbindung: Assistent sieht nie mehr als der Nutzer im Web). Es fehlt
aber jede Datenschutz-Doku in docs/.

**Der DSGVO-Knackpunkt liegt hinter dem Connector:** Sobald ein Nutzer einen
gehosteten KI-Client (Claude.ai, ChatGPT) verbindet, fliessen die abgerufenen
Nextcloud-Inhalte (Dateien, Kalender, Kontakte, via prepare_context auch
Datei-Auszuege) an den LLM-Anbieter, i.d.R. Drittland (US). Der Connector
leitet nichts von sich aus weiter, ist aber das Tor. Betreiber brauchen dafuer
eine Rechtsgrundlage (AVV mit dem LLM-Anbieter, ggf. Einwilligung, TIA fuer
Drittlandtransfer). EU-/self-hosted-LLM (z.B. MUCGPT) entschaerft das.

**Was zu tun waere (Phase 5, deckt zugleich SC 1 Datenweitergabe-Disclosure):**
1. docs/privacy.md (oder datenschutz.md): welche personenbezogenen Daten der
   Connector speichert (nc_user, verschluesseltes App-Passwort, Token-Hashes,
   Zeitstempel), wo (SQLite im ExApp-Container), Verschluesselung, Loeschung
   (Trennen/Deinstallation), Betroffenenrechte.
2. Datenweitergabe-Disclosure fuer den App Store: klar benennen, dass Inhalte
   an den vom Nutzer gewaehlten KI-Client gehen, mit Drittland-/LLM-Hinweis
   und Empfehlung, den Datenschutz des Clients zu pruefen.
3. info.xml-Beschreibung: die Zusicherung "sieht nie mehr als der Nutzer"
   bleibt korrekt, darf aber nicht suggerieren, dass nach dem Tool-Call kein
   Datenabfluss an den Client mehr stattfindet.

**Warum nicht in Phase 4:** Phase 4 war der Per-User-Slice; Store-Disclosure
und Doku gehoeren zu Phase 5 (EXAPP-04/05, SC 1).

## BL-08: Anti-Fälschungs-Werte mit Zeitfenster, oder als Restrisiko führen (Review 04, ME-02)

**Befund:** `form_token` ist eine reine Funktion aus Datenschlüssel, Zweck und
Handle. Der Wert hat keine Gültigkeitsdauer, kein Nonce, keinen Sitzungsbezug
und keine Verbrauchszählung: für ein Konto ist der Schalter-Wert über die ganze
Lebensdauer der Installation derselbe. Wer ihn einmal erlangt, kann den
MCP-Zugang dieses Kontos zeitlich unbegrenzt per Cross-Site-POST pausieren und
wieder freigeben, solange die Nutzerin bei Nextcloud angemeldet ist. Der einzige
Rotationspunkt wäre der Datenschlüssel, und dessen Austausch macht jedes
gespeicherte App-Passwort unlesbar, also alle Verbindungen kaputt.

**Was zu entscheiden ist (Owner):** Ein Zeitfenster in die Ableitung nehmen, wie
bei Double-Submit-Token üblich (Vorschlag des Reviews: `FORM_TOKEN_WINDOW = 3600`,
aktuelles und vorheriges Fenster akzeptieren, beide mit `compare_digest`). Das ist
eine UX-Entscheidung, keine reine Sicherheitsentscheidung: ein Formular, das
länger als zwei Fenster offen liegt, wird ungültig, und der Nutzer bekommt die
ruhige Ablehnung statt seiner Aktion. Alternative: den Sachverhalt als
akzeptiertes Restrisiko mit Id führen, statt ihn in `crypto.py` als vollwertigen
Schutz zu beschreiben.

**Nicht im Review-Fix erledigt,** weil die Fensterbreite und das Verhalten
offener Tabs eine Produktentscheidung sind. ME-01 (Zweckbindung) ist umgesetzt
und unabhängig davon.

## BL-09: Trunkierungsmarke von Auszügen aus dem Text herausziehen (Review 04, ME-03, D-57)

**Befund:** `context._capped` hängt `EXCERPT_TRUNCATION` ohne Trenner an den
Nutzertext, und `chatgpt.TRUNCATION_NOTE` läuft in denselben Textstrom. Ein
Dokument, das dieselbe Zeichenfolge enthält, kann für das Modell so aussehen, als
ende der Serverauszug dort und als folge danach eine Systemmitteilung: der
Angreifer entscheidet über die Rahmung seines eigenen Texts, also genau über die
Grenze, auf die sich D-57 stützt. Umgekehrt kann ein Dokument behaupten,
vollständig zu sein, wo gekappt wurde.

**Was zu entscheiden ist (Owner):** Sauber wäre ein eigenes Feld
(`hit["excerpt_truncated"] = True`), das ein Dokument nicht erzeugen kann. Das
ändert die Antwortstruktur von `prepare_context` und berührt bei `chatgpt.fetch`
den ChatGPT-kompatiblen Vertrag, in dem die Marke bewusst im Text steht, damit ein
Modell, das nur `text` liest, den Unterschied sieht. Beides zusammen ist eine
Schema-Entscheidung (Tool-Budget, Client-Kompatibilität), keine lokale Korrektur.

**Zwischenschritt, falls die Marke im Text bleiben soll:** einen Trenner
verwenden, den `_capped` vorher aus dem Nutzertext filtert, und
`chatgpt.TRUNCATION_NOTE` nicht ungeprüft in denselben Strom schreiben.

## BL-10: Schalter auch dort durchsetzen, wo eine Zugangsberechtigung entsteht (Review 04, ME-04)

**Befund:** Das Gate hängt ausschließlich an `MCP_PATH`. `/authorize`,
`/authorize/decide` und `POST /connect` sind ungebremst, ein pausiertes Konto kann
also einen kompletten Login-Flow abschließen, und Nextcloud legt dabei ein echtes
App-Passwort an, das im Store landet. Erst der spätere Tool-Aufruf läuft in R1.
Die Oberfläche sagt "MCP access is switched off for your account", und die Menge
gültiger Nextcloud-App-Passwörter wächst trotz gezogener Bremse weiter.

**Was zu entscheiden ist (Owner):** Entweder den Schalter an genau der Stelle
mitprüfen, an der eine Zugangsberechtigung entsteht (vor `create_authorization` in
`consent.py` und vor `_start` in `connect.py`, Antwort ist dieselbe Seite, die den
Schalter zeigt), oder die Texte präzisieren (`SWITCH_OFF_STATE`,
`CONNECTIONS_PAUSED_BODY`, `ACCESS_DISABLED_DESCRIPTION`) und den Sachverhalt als
Restrisiko mit Id führen. Was nicht bleiben darf, ist die Differenz zwischen
Zusage und Durchsetzung.

**Nicht im Review-Fix erledigt,** weil beide Wege den App-Passwort-Flow berühren:
die Prüfung fällt mitten in den Login-Flow-v2-Ablauf, in dem der Poll genau
einmal antwortet und ein Abbruch nach dem Poll eine Rückgabe erzwingt. Das ist
eine Design-Entscheidung, keine Raterei wert.

## BL-11: Drei kleinere Befunde aus dem Phase-4-Review (LO-02, LO-03, LO-06)

Alle drei sind kein Sicherheitsdefekt, aber jeder hat einen benennbaren Preis.

**LO-02, `access_disabled` kostet mehr als der Docstring sagt.** Gemessen 1,54 ms
pro Aufruf (300 Durchläufe, warm), weil `_connect` bei jedem Öffnen `mkdir`, drei
Pragmas, `executescript(SCHEMA)` mit 13 Statements und zwei `PRAGMA table_info`
ausführt. Das liegt auf jedem MCP-Request einer authentifizierten Identität, und
`/mcp` trägt bewusst keine Drosselung. **Zu tun:** Schema nur beim ersten Öffnen
pro Prozess ausführen (Flag im `OAuthStore`, gesetzt nach dem ersten
erfolgreichen `_connect`) und den Docstring auf das korrigieren, was gemessen ist.
Zu klären: Verhalten, wenn die Datei zur Laufzeit verschwindet.

**LO-03, `user_access`-Zeilen werden nie aufgeräumt.** Die Tabelle wächst monoton
und hält Zeilen für Konten, die es nicht mehr gibt; bei Verzeichnis-Setups mit
Wiederverwendung von Konto-Ids startet ein neues Konto mit demselben Namen still
pausiert. Über `/connections` sichtbar und behebbar, aber überraschend. **Zu tun:**
`purge_expired` um ein Aufräumen für Konten ohne jede Autorisierung und mit altem
`disabled_at` erweitern, oder auf ein `deleteUser`-Ereignis von Nextcloud hören
(falls eine ExApp das erreichen kann), und den Grenzfall in `docs/` benennen.

**LO-06, ein Auszug von 2 KB kostet bis zu 512 KB Transfer je Treffer.**
`context._excerpt` ruft `chatgpt_tools.fetch`, und das liest bis
`files.DEFAULT_MAX_BYTES` (512 KB), um daraus 2 KB zu behalten: bei `detail="full"`
bis zu 1,5 MB Nextcloud-Transfer je Bundle-Aufruf, zeitlich durch
`EXCERPT_TIMEOUT` begrenzt, mengenmäßig gar nicht. **Zu tun:** eine Leseobergrenze
durch `fetch` durchreichen (etwa `max_bytes=EXCERPT_MAX_BYTES * 2`). Ändert nichts
am Ergebnis und spart den Faktor 250; berührt aber die Signatur von `fetch`, die
zum ChatGPT-Vertrag gehört, deshalb zusammen mit BL-09 zu entscheiden.
