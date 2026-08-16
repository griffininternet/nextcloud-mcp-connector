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
