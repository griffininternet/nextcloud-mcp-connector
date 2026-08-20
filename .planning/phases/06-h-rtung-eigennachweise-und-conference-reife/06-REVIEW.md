---
phase: 06-h-rtung-eigennachweise-und-conference-reife
reviewed: 2026-08-20T00:00:00Z
depth: standard
files_reviewed: 21
files_reviewed_list:
  - src/mcp_connector/oauth/cimd.py
  - src/mcp_connector/oauth/provider.py
  - src/mcp_connector/oauth/registry.py
  - src/mcp_connector/oauth/consent.py
  - src/mcp_connector/oauth/store.py
  - src/mcp_connector/oauth/metadata.py
  - src/mcp_connector/oauth/verifier.py
  - src/mcp_connector/exapp/responses.py
  - src/mcp_connector/exapp/ui/consent.py
  - src/mcp_connector/exapp/ui/strings.py
  - src/mcp_connector/exapp/ui/layout.py
  - src/mcp_connector/entry_exapp.py
  - appinfo/info.xml
  - compose.exapp.yml
  - vulture_whitelist.py
  - tests/unit/test_oauth_cimd.py
  - tests/unit/test_oauth_provider.py
  - tests/unit/test_oauth_registry.py
  - tests/unit/test_oauth_consent.py
  - tests/unit/test_oauth_store.py
  - tests/unit/test_oauth_metadata.py
findings:
  critical: 0
  warning: 3
  info: 3
  total: 6
status: issues_found
---

# Phase 6: Code Review Report

**Reviewed:** 2026-08-20
**Depth:** standard
**Files Reviewed:** 21
**Status:** issues_found

## Summary

Reviewed die Phase-6-Haertung um Client ID Metadata Documents (CIMD) als DCR-Alternative,
mit Sicherheitsfokus auf SSRF-Umgehungen, DCR-off-Umgehung, Allowlist-Umgehung, Injection
ueber Dokumentfelder und TOCTOU.

Der SSRF-Kern in `cimd.py` ist stark und gruendlich getestet: die IP-Pinning-Strategie
schliesst das Rebinding-Fenster (genau eine Aufloesung, Verbindung an die geprueften
Literale, `sni_hostname` haelt die Zertifikatspruefung auf dem Namen), die
`target_allowed`-Konjunktion faengt die drei gemessenen Ein-Flag-Luecken (CGNAT, NAT64,
Multicast) plus v4-mapped, Redirects werden verweigert statt gefolgt, das 5120-Byte-Limit
bricht im Chunk-Loop, und Fehler/kaputte Dokumente werden nicht gecacht. Die zentrale
Locked-Decision "ein abgeschaltetes DCR darf nicht ueber CIMD umgehbar sein" haelt sauber:
`cimd_enabled = CIMD-Schalter AND DCR-Schalter` (`registry.client_policy`), und
`_resolve_cimd` prueft diesen Schalter als allererste Frage, vor jedem Paket. Die
HTML-Ausgabe (`client_name`, `client_host`) laeuft ausnahmslos durch `layout._escape` bzw.
`layout.client_name`, sodass ueber Dokumentfelder kein Markup einbricht.

Die Befunde konzentrieren sich nicht auf die SSRF-Grenze selbst, sondern darauf, wo der
CIMD-Fetch in den Request-Lebenszyklus verdrahtet ist: der Refetch laeuft auf dem
Token-Verifikations-Hot-Path (WR-01), und die Allowlist verhindert den ausgehenden Fetch
nicht (WR-02).

## Narrative Findings (AI reviewer)

## Warnings

### WR-01: CIMD-Refetch laeuft auf dem Token-Verifikations-Hot-Path (ausgehender HTTP-Request plus Store-Write pro Tool-Call-Fenster)

**File:** `src/mcp_connector/oauth/verifier.py:215`, `src/mcp_connector/oauth/provider.py:340-347`, `src/mcp_connector/oauth/provider.py:436-476`

**Issue:**
`StoreTokenVerifier.verify_token` ruft auf jedem Cache-Miss (Fenster 5 s,
`VALIDATION_CACHE_TTL`) `self._get_client(authorization.client_id)` auf. Fuer einen
CIMD-Client fuehrt `get_client` in den Zweig
`if row is None or row.cimd_fetched_at is not None: row = await self._resolve_cimd(...)`.
Wenn die Frische der Zeile abgelaufen ist (`cimd_expires_at <= now`), macht `_resolve_cimd`
einen **ausgehenden HTTP-Fetch** (`cimd.fetch_document_and_lifetime`, bis zu 5 s Timeout,
Ziel-Host vom Client kontrolliert) und einen **Store-Write** (`store.save_client`) mitten
im Hot-Path eines Tool-Calls und ebenso in `HashedClientAuthenticator.authenticate_request`
auf `/token` und `/revoke`.

Das widerspricht der ausdruecklichen Invariante des Verifiers (Moduldocstring
`verifier.py:11-14`): "Validating a token ... would put a network call in the hot path of
every tool call, and it would make this server unavailable whenever [the host] is slow."
Genau das passiert hier, nur gegen den vom Client benannten Dokument-Host statt gegen
Nextcloud.

Zwei konkrete Auswirkungen:
- **Verfuegbarkeit:** Faellt der Dokument-Host an der Frische-Grenze aus, liefert
  `_resolve_cimd` `None`, `get_client` liefert `None`, `verify_token` liefert `None`, und
  eine laufende Sitzung wird mitten in der Konversation als unauthorized abgewiesen, obwohl
  Token und Nextcloud unveraendert gueltig sind. Das trifft genau den Vorzeige-Client
  dieser Phase (Claude Code) bei einer fremden Ausfallminute.
- **Latenz:** Der Tool-Call, der den Refetch ausloest, wartet bis zu 5 s auf einen fremden
  Host.

Die Haeufigkeit ist durch das Frischefenster (Boden 300 s, `CACHE_MIN_SECONDS`) begrenzt,
nicht durch das 5-s-Verifier-Fenster, weil ein erfolgreicher Refetch `cimd_expires_at`
erneuert. Also hoechstens ein Fetch pro >= 5 min pro aktivem Client, aber der Fehler liegt
im Prinzip: eine reine Autorisierungs-/Policy-Frage auf dem Hot-Path darf keinen
Netzaufruf und keinen Store-Write gegen einen fremden, vom Client gewaehlten Host
ausloesen.

**Fix:**
Die lokale Policy-Frage (allowed-Flag, Allowlist, Ablauf) von der CIMD-Frischeerneuerung
trennen, sodass der Hot-Path nur die lokale Zeile liest und niemals einen ausgehenden
Request ausloest. Skizze: einen reinen Lese-Pfad fuer Verifier/Client-Auth einfuehren, der
eine vorhandene Zeile auch mit abgelaufener Frische akzeptiert (die Identitaet aendert sich
selten und wurde bereits einmal byte-fuer-byte gebunden), und den Refetch nur auf dem
`/authorize`-Pfad bzw. asynchron/verzoegert erlauben:

```python
async def get_client(self, client_id: str, *, may_fetch: bool = True) -> OAuthClientInformationFull | None:
    ...
    if row is None or row.cimd_fetched_at is not None:
        row = await self._resolve_cimd(client_id, store, row=row, may_fetch=may_fetch)
        if row is None:
            return None
    ...
# Verifier und HashedClientAuthenticator rufen get_client(client_id, may_fetch=False);
# nur consent._refuse/_screen/_decide (die /authorize-Kette) rufen mit may_fetch=True.
```
So bleibt die "kein Netz im Hot-Path"-Invariante des Verifiers erhalten und eine laufende
Sitzung ueberlebt einen kurzen Ausfall des Dokument-Hosts.

### WR-02: Allowlist-only verhindert den ausgehenden CIMD-Fetch nicht (Refetch vor der Allowlist-Verweigerung)

**File:** `src/mcp_connector/oauth/provider.py:461-476`, `src/mcp_connector/oauth/provider.py:355-359`

**Issue:**
Im Allowlist-Modus wird ein nicht gelisteter CIMD-Client erst **nach** dem ausgehenden
Dokument-Fetch verweigert: `_resolve_cimd` fetcht das Dokument, schreibt die Zeile mit
`allowed=self._policy.allows(...)` und gibt sie zurueck; die eigentliche Verweigerung
faellt danach in `get_client` (`if not row.allowed: return None`). Der Docstring nennt das
absichtlich (T-06-27), aber adversariell betrachtet heisst das: selbst in der haertesten
Konfiguration (`NC_MCP_OAUTH_ALLOWLIST_ONLY=on`) kann ein **unauthentifizierter**
Angreifer ueber die PUBLIC-Route `/authorize` mit
`client_id=https://angreifer.example/doc.json` den Server zu ausgehenden GET-Requests an
beliebige oeffentliche HTTPS-Ziele bewegen (Request-Forgery/Reflector; interne Ziele sind
durch die SSRF-Haertung geblockt, oeffentliche nicht). Die Amplifikation ist durch
`CLASS_AUTHORIZE_START`/`FLOW_LIMIT` gedrosselt und durch das Fehlen eines
Negativ-Caches nicht persistiert, aber die Allowlist als Haertungsmassnahme leistet hier
nichts.

**Fix:**
Wenn die Allowlist per Client-ID gefuehrt wird (die CIMD-Client-ID ist die URL und damit
vor dem Fetch bekannt), die ID-basierte Allowlist-Frage vor dem Fetch stellen und einen
unbekannten Bezeichner ohne Paket verweigern:

```python
async def _resolve_cimd(self, client_id, store, *, row=None):
    if not self._policy.cimd_enabled:
        return None
    if row is not None and _cimd_is_fresh(row, self._now()):
        return row
    # Vor jedem Paket: im Allowlist-Modus muss die per-ID gelistete Freigabe reichen,
    # sonst kein ausgehender Request auf fremde Rechnung.
    if self._policy.allowlist_only and not self._policy.listed(client_id):
        return None
    ...
```
Das kann eine per-redirect_uri-Allowlist nicht vollstaendig abdecken (die Adressen stehen
erst nach dem Fetch fest), schliesst aber den unauthentifizierten Missbrauch fuer den
gaengigen Fall (ID-Listen) und dokumentiert die verbleibende Luecke ehrlich.

### WR-03: Refetch auf dem Token-Pfad widerspricht der dokumentierten "kein Nextcloud/Netz"-Zusage der Exchange-Methoden

**File:** `src/mcp_connector/oauth/provider.py:730-731`, `src/mcp_connector/oauth/provider.py:842-843`

**Issue:**
`exchange_authorization_code` und `exchange_refresh_token` beginnen jeweils mit
`if await self.get_client(client.client_id) is None: raise TokenError(...)`. Fuer einen
CIMD-Client kann dieses `get_client` (siehe WR-01) einen ausgehenden Fetch ausloesen. Die
Docstrings beider Methoden versichern aber ausdruecklich "Nothing here talks to Nextcloud"
bzw. "a connector gives its token endpoint about ten seconds ... a family kill under load
must not depend on a PHP round trip" (`provider.py:720-722`, `838-840`). Ein langsamer oder
haengender Dokument-Host verzoegert damit die Token-Ausgabe bzw. -Rotation um bis zu 5 s
und kann eine an sich gueltige Rotation an der Frische-Grenze scheitern lassen. Dies ist
dieselbe Wurzel wie WR-01, aber auf dem Token-Endpoint, wo die Zusage explizit
niedergeschrieben ist; der Fix von WR-01 (`may_fetch=False` auf allen Nicht-`/authorize`-
Pfaden) deckt ihn mit ab.

**Fix:** Wie WR-01: die Token-Pfade rufen `get_client(..., may_fetch=False)`, damit die
Policy-Pruefung lokal bleibt und keine fremde Netzabhaengigkeit in den Token-Endpoint
gelangt.

## Info

### IN-01: `is_cimd_client_id` verwirft prozentkodierte Dot-Segmente nicht

**File:** `src/mcp_connector/oauth/cimd.py:151`

**Issue:**
`if any(segment in (".", "..") for segment in path.split("/"))` prueft nur die dekodierte
Literalform. Ein Bezeichner wie `https://host/a/%2e%2e/c.json` traegt kein `.`/`..`-Segment
in `parts.path` und passiert die Pruefung, obwohl der Draft "MUST NOT contain single-dot or
double-dot path segments" fordert. Nicht ausnutzbar fuer SSRF, weil der Bezeichner
byte-fuer-byte als Identitaet gebunden und die Verbindung an die gepruefte IP gepinnt wird
(die kodierte Traversierung landet auf dem eigenen Server des Angreifers), aber eine
Abweichung von der Spezifikation.

**Fix:** Optional zusaetzlich gegen die case-insensitive kodierten Formen pruefen
(`%2e`), z. B. Pfadsegmente vor dem Vergleich mit `urllib.parse.unquote` normalisieren und
dann erneut auf `.`/`..` testen.

### IN-02: IDN/Unicode-Host-Schreibweise divergiert zwischen `urlsplit` und `httpx`

**File:** `src/mcp_connector/oauth/cimd.py:344`, `src/mcp_connector/oauth/consent.py:479`

**Issue:**
`is_cimd_client_id` (`urlsplit().hostname`) und `_identifier_host`
(`urlsplit(client_id).hostname`) liefern die Unicode-Form eines internationalisierten
Hosts, waehrend `_fetch_pinned` mit `url.raw_host.decode("ascii")` die Punycode-Form fuer
SNI/Host verwendet. Der auf der Consent-Seite angezeigte `client_host` (Unicode) kann damit
optisch von dem abweichen, wohin tatsaechlich verbunden wird (Punycode), was die MUST-Zusage
"clearly display the redirect URI hostname" aufweichen kann (Homoglyph-Anzeige). Kein
demonstrierter XSS (alles ist escaped). `tests/unit/test_oauth_cimd.py` deckt keinen
IDN-Fall ab.

**Fix:** Fuer die Anzeige und die Formpruefung eine konsistente Schreibweise waehlen (z. B.
den Host ueber `host.encode("idna")` normalisieren oder die Punycode-Form anzeigen) und
einen IDN-Negativtest ergaenzen.

### IN-03: Kein Element-/Groessenlimit auf `redirect_uris` eines CIMD-Dokuments

**File:** `src/mcp_connector/oauth/cimd.py:499-501`, `src/mcp_connector/oauth/provider.py:447`

**Issue:**
`validate_document` prueft nur, dass `redirect_uris` eine Liste ist; `_resolve_cimd`
filtert sie danach ueber `redirect_uri_allowed` und speichert alle admissiblen. Ein
Dokument innerhalb des 5120-Byte-Limits kann dennoch dutzende Adressen enthalten, die alle
gespeichert und bei jeder `get_client`-Auswertung linear geprueft werden. Kein
Sicherheitsrisiko (Groesse ist gedeckelt, Performance ist laut Auftrag v1-out-of-scope),
aber eine unnoetig unbegrenzte Zahl gespeicherter Adressen pro fremdem Dokument.

**Fix:** Eine kleine Obergrenze fuer die uebernommenen `redirect_uris` setzen (z. B. die
ersten N admissiblen), konsistent mit dem Byte-Limit als "sag es, statt es zu verstecken".

---

_Reviewed: 2026-08-20_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
