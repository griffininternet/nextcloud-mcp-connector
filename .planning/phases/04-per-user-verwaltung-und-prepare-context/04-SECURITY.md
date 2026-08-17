---
phase: 4
slug: per-user-verwaltung-und-prepare-context
status: verified
threats_open: 0
asvs_level: 1
created: 2026-08-17
---

# Phase 4: Security

> Sicherheitsvertrag der Phase: Threat-Register, akzeptierte Restrisiken, Audit-Trail.
> Register-Quelle: die vier threat_model-Blöcke der Pläne 04-01 bis 04-04 (zur Planzeit
> erstellt), 27 Positionen (23 mitigate, 4 accept). Verifiziert am 2026-08-17 durch
> gsd-security-auditor (opus) gegen den Quelltext bei `873b381` (Arbeitsbaum sauber bis auf
> die noch nicht committete 04-VERIFICATION.md), gegen eigene Testläufe (1543 passed, 82
> deselected) und gegen die sechs Gates (ruff check, ruff format, pyright 0/0/0, vulture,
> check_tool_budget, pytest), alle grün.
>
> Dieses Audit sucht keine neuen Schwachstellen. Es prüft für jede der 27 Positionen, ob die
> in ihrer Zeile deklarierte Gegenmaßnahme im ausgelieferten Stand wirklich existiert, an der
> genannten Stelle im Quelltext und, wo vorhanden, mit ihrem Wächter-Test. Nicht gegen die
> vier SUMMARYs, nicht gegen 04-REVIEW.md, nicht gegen 04-VERIFICATION.md geprüft, sondern
> gegen den Code selbst.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| MCP-Client zu /mcp (PUBLIC) | Jeder Tool-Aufruf trägt ein Credential, das eine Identität behauptet; die Schalter-Entscheidung (EXAPP-02) kommt dahinter | Bearer-Token, App-Passwort-Handshake, aufgelöste Nutzer-Id |
| Middleware zu Store | Aus einer SQLite-Zeile (`user_access`) wird die Zugriffsentscheidung für ein ganzes Konto | Konto-Id, Schalter-Zustand |
| Browser zu /connections (PUBLIC, Route 13) | Formular-POSTs entscheiden über Verbindungen und den Zugriff eines ganzen Kontos; die Identität kommt allein aus dem HaRP-signierten Header | Anti-Fälschungs-Merkmal, auth_id-Handle, Schalter-Aktion |
| Fremde Origin zu /connections | Eine fremde Seite kann POSTs im Namen eines angemeldeten Browsers absetzen wollen | Formularentscheidungen |
| DCR-Registrierung zu Seiten-Markup | Client-Namen sind Angreifer-Input und werden auf der Kontoseite gerendert | Client-Name |
| Fremde Inhalte zu Assistenten-Kontext | `prepare_context` hebt viele von Dritten geschriebene Texte in EINEM Aufruf in den Modell-Kontext (D-57) | Titel, Ids, Auszüge fremder Dokumente |
| ExApp zu Nextcloud-OCS (App-Kontext) | Die Settings-Registrierung trägt das App-Secret in den Auth-Headern | App-Secret, Form-Scheme |
| Nextcloud-Settings-Seite zu Nutzer | Der Wegweiser-Text und sein Link erscheinen auf Nextclouds eigener Seite | public_url, Beschreibung |

---

## Threat Register

27 Positionen: 23 `mitigate`, 4 `accept` (T-04-SC je Plan). **27 closed, 0 open.** Belege
verkürzt; jede Zeile wurde einzeln gegen den Quelltext bei `873b381` geprüft, nicht gegen die
SUMMARYs.

### Plan 04-01: Der pro-Konto-Schalter an der Transportgrenze

| Threat ID | Category | Component | Disposition | Mitigation (Beleg) | Status |
|-----------|----------|-----------|-------------|--------------------|--------|
| T-04-01 | Info Disclosure | exapp/middleware.py (Prüf-Reihenfolge) | mitigate | R1 sitzt hinter Handshake (R3) und Bearer (R2): `__call__` prüft `require_appapi` (`middleware.py:128`), dann `_bearer_is_valid` (`:137`), erst dann `_switch_refusal` (`:142`); ein ungültiger Bearer verlässt die Grenze mit 401, bevor der Schalter gefragt wird. Wächter `test_an_invalid_bearer_of_a_paused_account_is_still_the_discovery_401` inkl. `switch.asked == []` | closed |
| T-04-02 | DoS | R1-Antwortform | mitigate | 403 mit `_ACCESS_DISABLED_BODY`, `media_type` application/json, `headers=NO_STORE`, **kein** `WWW-Authenticate` (`middleware.py:186-191`); die bewusste RFC-6750-Abweichung steht im Docstring von `_switch_refusal` (`:166`) | closed |
| T-04-03 | Elevation | Schalter-Durchsetzung | mitigate | Read je Request direkt `await self._access_check(nc_user)` (`middleware.py:178`) auf `store.access_disabled` = `SELECT 1 ... WHERE nc_user` ohne Cache (`store.py:740-758`); Wächter `test_flipping_the_switch_takes_effect_on_the_very_next_request` | closed |
| T-04-04 | Elevation | App-Kontext (leere Identität) | mitigate | `nc_user = user or (identity.nc_user ...)`, dann `if not nc_user: return None` (`middleware.py:174-176`); `access_disabled("")` liefert False ohne Dateizugriff (`store.py:753-754`), `set_access("")` wirft ValueError vor jedem Schreiben (`store.py:724-725`); Wächter `test_the_app_context_is_never_asked_for_a_switch` | closed |
| T-04-05 | Info Disclosure | R1-Body | mitigate | `_ACCESS_DISABLED_BODY` einmal auf Modulebene aus zwei Konstanten gebaut (`middleware.py:84-86`), `ACCESS_DISABLED_DESCRIPTION` ohne Platzhalter (`strings.py:475-482`), nie ein Wert aus der Anfrage; `no-store` gegen den PHP-Proxy-Cache. Wächter assertet zusätzlich, dass Kontoname und App-Secret nicht im Body stehen | closed |
| T-04-06 | DoS | Store-Ausfall am Gate | mitigate | Fail closed: `except Exception: ... return Response(status_code=503, headers=NO_STORE)` (`middleware.py:179-183`), kein Durchlass und kein gelogenes access_disabled; Logzeile ohne Kontonamen; Wächter `test_a_store_that_cannot_answer_the_switch_refuses_instead_of_letting_through` | closed |
| T-04-SC | Tampering | pip/npm/cargo-Installationen | accept | Kein Paket installiert: `git diff e30ab81 873b381 -- uv.lock pyproject.toml` ist leer (im Audit nachgezogen). Restrisiko AR-04-05 | closed |

### Plan 04-02: prepare_context, der gebündelte Lesevorgang

| Threat ID | Category | Component | Disposition | Mitigation (Beleg) | Status |
|-----------|----------|-----------|-------------|--------------------|--------|
| T-04-20 | Tampering | tools/context.py (Prompt-Injection, D-57) | mitigate | Herkunft als Strukturfelder (`id`, `provider`, `kind`) im `_bundle`, nie als Fließtext; der Auszug ist ein Datenfeld ohne Anweisungs-Rahmung; die Tool-Description warnt vor Inhalten Dritter (`reg_context.py`, Docstring von `prepare_context`); keine Maskierung (Owner-Entscheid 14.08.). Wächter `test_an_injected_instruction_arrives_as_data_and_moves_no_key_of_the_answer` (Strukturgleichheit, zeichengenaue Ankunft) | closed |
| T-04-21 | DoS | Fan-out | mitigate | Harte Teil-Budgets: `CALENDAR_BUDGET=10` (`context.py:65`), 15 s je Suchprovider (bestehend), `EXCERPT_TIMEOUT` je Auszug; Caps `MAX_PER_BUCKET=5`, `MAX_EVENTS=10`, `MAX_EXCERPTS=3`, `EXCERPT_MAX_BYTES=2000` (`:70-82`); `asyncio.gather(..., return_exceptions=True)` ohne globalen Abbruch (`:115-119`); beide Quellen tot = ToolError statt leerem Bündel (`:125-131`); kein Retry. Restband LO-06 → BL-11 (AR-04-06) | closed |
| T-04-22 | Elevation | Berechtigungsgrenze | mitigate | `search_tools.unified_search(clients, query=term, limit=SEARCH_LIMIT)` ohne Provider-Argument (`context.py:116`), kein eigener Index, kein Cache über Requests, kein Direktdraht zu Findling (D-53); Wächter `test_the_search_is_asked_without_any_provider_restriction`, `test_this_module_reads_no_content_of_its_own` | closed |
| T-04-23 | Info Disclosure | degraded/Fehlertexte | mitigate | `_reason` nennt Vorgang und Budget, nie Host, Pfad oder Credential; die Sätze aus `tools/search.py` wörtlich wiederverwendet; Wächter `test_the_degraded_entries_of_the_search_are_passed_through_unchanged` | closed |
| T-04-24 | Tampering | Tool-Oberfläche | mitigate | Eingefrorenes `EXPECTED_TOOLS`-Literal mit genau 16 Namen inkl. `prepare_context` (`test_tool_surface.py:31-49`), Mengengleichheits-Assertion `set(tools) == EXPECTED_TOOLS` (`:308`), Budget-Gate `11268/12500 Bytes, 16 tools, exit 0` (im Audit nachgezogen) | closed |
| T-04-SC | Tampering | pip/npm/cargo-Installationen | accept | uv.lock unverändert (siehe T-04-SC oben). Restrisiko AR-04-05 | closed |

### Plan 04-03: Die Verbindungsseite (Route 13)

| Threat ID | Category | Component | Disposition | Mitigation (Beleg) | Status |
|-----------|----------|-----------|-------------|--------------------|--------|
| T-04-30 | Tampering | Disconnect- und Schalter-POSTs (CSRF) | mitigate | Zustandsänderung nur per POST (`connections.py:150,163`), verstecktes `form_token` = HMAC(data_key, `len:purpose:handle`) (`crypto.py:150-175`), Vergleich mit `secrets.compare_digest` auf Bytes (`connections.py:411-424`), `form-action 'self'` in der CSP (`layout.py:71`); der Schalter-Wert zweckgebunden an `access:`+Konto (`connections.py:92,296`). Purpose-Bindung (ME-01) trennt Consent- von Disconnect-Wert. Wächter `test_a_row_value_cannot_pause_the_account`, `test_a_disconnect_without_the_anti_forgery_value_changes_nothing` | closed |
| T-04-31 | Elevation | Geratene auth_id (IDOR) | mitigate | `is_user(user, row.nc_user)` je Zeile (`connections.py:357`), leere Identität = E8 vor jedem Read (`:141-144`); unbekannt/fremd/widerrufen antworten byte-identisch dieselbe Seite minus Nonce (`_owned` liefert None → `DISCONNECT_GONE`); Wächter `test_an_unknown_a_foreign_and_a_revoked_handle_answer_the_same_page` | closed |
| T-04-32 | Info Disclosure | PHP-Proxy cacht die Kontoseite | mitigate | `no-store` (via `NO_STORE`) plus CSP, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer` auf jeder Antwort über `layout.page._headers` (`layout.py:553-559`); Wächter `test_every_page_of_this_family_carries_the_five_required_headers` | closed |
| T-04-33 | DoS | HaRP-Blacklist bei access_level USER | mitigate | Route 13 PUBLIC (access_level 0) mit Identitätsprüfung in der App; der gemessene CR-01-Grund als eigener Absatz im Manifest (`info.xml:150-166`) und im Bootstrap-Kommentar (`bootstrap_exapp.sh:521,564-566`); Wächter `test_the_manifest_declares_exactly_the_thirteen_routes_of_this_phase` | closed |
| T-04-34 | Tampering | Bösartiger Client-Name im Markup | mitigate | `layout.client_name` (Steuerzeichen raus, 80 Zeichen, `layout.py:506`) vor dem zentralen `_escape` an genau einer Stelle je Fragment (`layout.py:352-380`); Wächter `test_a_hostile_client_name_does_not_add_a_single_element`, `test_a_hostile_client_name_stays_text_on_every_screen_of_this_family` | closed |
| T-04-35 | Elevation | Zweiter Widerrufs-Pfad driftet | mitigate | Zeilen-Widerruf ausschließlich über `provider.end_connection` (`connections.py:272`), das `_end_connection` → `self._invalidate()` (Verifier-Cache) aufruft (`provider.py:781,809`); Quelltext-Wächter hält `revoke_authorization`/`revoke_family` aus beiden neuen Modulen heraus (`test_connections_page.py:1149-1167`), per Direktaufruf gegengeprüft | closed |
| T-04-36 | Spoofing | Routenmuster ohne Endanker | mitigate | `^/connections/?$` beidseitig verankert, `GET,POST` ohne DELETE, `headers_to_exclude` wie die zwölf anderen; Manifest (`info.xml:245`) und Bootstrap (`bootstrap_exapp.sh:547`) je 13 Routen, deckungsgleich; Wächter `test_the_connections_route_declares_both_verbs_and_no_third`, `test_the_manifest_passes_its_own_gate` (Endanker-Prüfung) | closed |
| T-04-37 | DoS | Formular-Flut auf /connections | mitigate | **Korrigiert (Review 04, HI-01, Commit 7ada840):** eigene Klasse `CLASS_CONNECTIONS` (`throttle.py:117`), `machine=False`, Zähler pro signiertem Konto via `identity=account` (`connections.py:183`); anonyme Anfragen werden gar nicht gezählt (`throttle.py:359-365`), so schließt eine anonyme Flut weder Notbremse noch Consent-Oberfläche. Wächter `test_an_anonymous_flood_closes_neither_the_brake_nor_the_consent_surface`, `test_the_refusals_of_one_account_do_not_lock_out_another` | closed |
| T-04-SC | Tampering | pip/npm/cargo-Installationen | accept | uv.lock unverändert. Restrisiko AR-04-05 | closed |

### Plan 04-04: Der Settings-Wegweiser

| Threat ID | Category | Component | Disposition | Mitigation (Beleg) | Status |
|-----------|----------|-----------|-------------|--------------------|--------|
| T-04-40 | Spoofing | doc_url / description der Settings-Form | mitigate | Beide URLs aus `config.public_url(env)`: `connections_url` (`settings_form.py:63`), `doc_url` (`:73`), `description.format(connections_url=...)` (`:72`); kein interner Hostname; Wächter `test_the_form_never_carries_an_internal_host_name` | closed |
| T-04-41 | DoS | /enabled-Handler | mitigate | Fire-and-forget: `register_settings_form` fängt jeden Fehler und gibt zurück (`settings_form.py:100-108`); der `/enabled`-Handler kapselt zusätzlich in try/except (`lifecycle.py:86-89`), antwortet 200, die Installation kann nie scheitern; Wächter `test_enabled_answers_200_when_the_registration_fails` | closed |
| T-04-42 | Info Disclosure | App-Secret im Registrierungs-Call | mitigate | Header-Bau via `appapi_auth_headers` (`settings_form.py:88-97`); Logzeilen nennen nur URL und Statuscode (`:104,108`), nie den Secret; Wächter `test_the_app_secret_never_reaches_a_log_record` (dreifach parametrisiert) | closed |
| T-04-43 | Tampering | Eine Checkbox, die nichts schaltet | mitigate | `"fields": []` als leere Liste (`settings_form.py:76`), der Wegweiser ist nur Link plus Beschreibung; Wächter `test_the_registered_form_carries_no_field_at_all` | closed |
| T-04-SC | Tampering | pip/npm/cargo-Installationen | accept | uv.lock unverändert. Restrisiko AR-04-05 | closed |

*Status: open, closed*
*Disposition: mitigate (implementation required), accept (documented risk), transfer (third-party)*

---

## Open Threats (BLOCKER für den Phasenabschluss)

Keine. Alle 27 Positionen des Registers sind geschlossen. Was aus dem Verifier (04-VERIFICATION.md,
"passed with concerns") und aus 04-REVIEW.md an offenen Punkten übernommen wurde, ist keine
fehlende deklarierte Gegenmaßnahme, sondern Defense-in-Depth über das Register hinaus und unten
als bewusst akzeptiertes Restrisiko AR-04-01 bis AR-04-04 geführt, jedes mit Backlog-Id.

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-04-01 | A1 (Verifier), berührt EXAPP-02 | Der gezeichnete Pixel des Settings-Wegweisers wurde nie in einem Browser gesehen. Belegt sind die ausgelieferte Form (`/ocs/v2.php/settings/api/declarative/forms`), ihre Präsenz im Anfangszustand der persönlichen Security-Seite und der Mount-Punkt `<div id="mcp_connector_mcp_connector_settings">`; nicht belegt ist der Pixel. Kein Ziel-Blocker: der Schalter und der Widerruf liegen einen Klick dahinter auf `/connections` und sind live und in-process verifiziert; der Declarative-Settings-Renderer zeichnet Titel, Beschreibung und Doc-Icon unabhängig von der leeren `fields`-Liste, schlimmster Fall ist ein fehlender Wegweiser-Link, nie ein Funktionsausfall. Braucht einen menschlichen Browser-Blick auf `/settings/user/security` vor Phase 5 | Owner, Verifier-Concern A1 | 2026-08-17 |
| AR-04-02 | ME-04 / BL-10 (Review), berührt T-04-01 bis T-04-06 | Das Gate hängt nur an `/mcp`. Ein pausiertes Konto kann `/authorize`, `/authorize/decide` und `POST /connect` weiter abschließen, und Nextcloud legt dabei ein echtes App-Passwort an; erst der spätere Tool-Aufruf läuft in R1. SC 1 wie formuliert (der nächste Tool-Aufruf des verbundenen Clients schlägt fehl) hält. **Zur UI-Text-Frage im Audit ausdrücklich geprüft und entschieden:** die Oberfläche sagt "MCP access is switched off for your account" (`strings.py:336`, ebenso `SWITCH_OFF_STATE:376`, `ACCESS_DISABLED_DESCRIPTION:478`). Unter der jetzigen Disposition "akzeptieren" übertreibt dieser Satz die Durchsetzung, weil neue Verbindungen weiter entstehen können. Ein Fix wäre klein, aber **nicht eindeutig**: die Wahl zwischen "an den Einstiegen mit durchsetzen" und "Texte präzisieren und als Restrisiko führen" ist in BL-10 ausdrücklich als eine Design-Entscheidung des Owners geführt (BACKLOG.md:220-231), und die konkrete Ersatzformulierung entscheidet mit, wie viel der Durchsetzungslücke dem Nutzer offengelegt wird. Deshalb im Audit **kein** Codeeingriff, sondern hier als Restrisiko mit Id geführt. Verbindungserzeugung braucht ohnehin die eigene HaRP-Identität des Kontos. Defense-in-Depth-Lücke, kein Ziel-Blocker | Owner, Review ME-04 → BL-10 | 2026-08-17 |
| AR-04-03 | ME-02 / BL-08 und ME-03 / BL-09 (Review), berührt T-04-30, T-04-20 | Zwei D-57/Anti-Fälschungs-Residuen. (a) Der Anti-Fälschungs-Wert ist eine reine Funktion aus Datenschlüssel, Handle und Purpose, ohne Fenster, Nonce oder Rotation (`crypto.py:150-175`, ME-02, BL-08); der Docstring nennt ihn weiter eine volle Schutzeigenschaft, gültig nur weil kein Feld heute angreiferkontrolliert ist. (b) Die Trunkierungsmarke `EXCERPT_TRUNCATION` ist In-Band-Text im Auszug (`context.py:90`), den ein geteiltes Dokument fälschen kann (ME-03, BL-09, D-57-Struktur). Beide brauchen die HaRP-Identität des Owners zum Ausnutzen und sind mit Id ins Backlog verschoben | Owner, Review ME-02/ME-03 → BL-08/BL-09 | 2026-08-17 |
| AR-04-04 | SC 5, C-01-Analogie (Verifier) | Der Ein-Roundtrip-Beleg (1,2 je Session-Call, 1,0 je authentifiziertem Request, letzterer HaRPs eigener) steht in 04-04-MEASUREMENTS.md und ist byte-gleich zu 03-VERIFICATION.md. Die exapp-Topologie ist am Ende von Plan 04-04 abgebaut (STATE.md), der Live-Beleg also nicht reproduzierbar. Die strukturelle Eigenschaft ist in-process bewiesen (ein Datenschlüssel-Fetch für drei Aufrufe, der Schalter-Read verlässt den Container nie) und in dieser Session grün gelaufen (`test_the_switch_costs_no_nextcloud_round_trip_per_request`). Gleiche Beweislage wie Phase 3 unter C-01 (AR-03-10) | Owner, Verifier-Concern AR-04-04 | 2026-08-17 |
| AR-04-05 | T-04-SC (alle vier Pläne) | Diese Phase installiert kein Paket; `uv.lock` und `pyproject.toml` sind über den Phasenbereich `e30ab81..873b381` unverändert (im Audit nachgezogen). Ein Diff auf `uv.lock` wäre ein Planbruch | Owner (Pläne 04-01 bis 04-04) | 2026-08-17 |
| AR-04-06 | LO-06 / BL-11 (Review), berührt T-04-21 | Ein Auszug von 2 KB liest intern bis `files.DEFAULT_MAX_BYTES` (512 KB) je Treffer, bei `detail="full"` bis 1,5 MB Nextcloud-Transfer je Aufruf; zeitlich durch `EXCERPT_TIMEOUT` begrenzt, mengenmäßig nicht. Kein Kontext-Problem und kein Angriff auf den Nutzer, nur mehr Verkehr als nötig; der Fix (ein `max_bytes` durch `chatgpt.fetch`) berührt die Signatur von `fetch` und ist mit Id ins Backlog verschoben | Owner, Review LO-06 → BL-11 | 2026-08-17 |

*Accepted risks do not resurface in future audit runs.*

---

## Unregistered Flags

Aus den Abschnitten `## Threat Flags` der vier SUMMARYs. Alle Threat-Flags der Pläne bilden
sich auf eine Register-Id ab; die "Beobachtungen über das Register hinaus" sind hier bewertet.

| Flag / Beobachtung | Quelle | Mapping | Bewertung |
|--------------------|--------|---------|-----------|
| `new-public-route`: `/connections` (Route 13, zweite zustandsändernde PUBLIC-Route) | 04-03-SUMMARY | T-04-30 bis T-04-37 | informativ, zugeordnet und geprüft |
| `new-tool`: `prepare_context` (16. Tool, bündelt bis 20 fremde Titel und 3 Auszüge) | 04-02-SUMMARY | T-04-20, T-04-24 | informativ, zugeordnet; die Restunsicherheit "Antwort ist Modell-Input, kein Beweis" ist D-57 und liegt bei T-04-20 |
| Client-Name aus zweiter JSON-Lesestelle: `connections.py` liest `client_name` direkt aus `clients.metadata_json` statt über `provider.get_client` | 04-03-SUMMARY (Beobachtung) | T-04-34 | **informativ, kein unregistered_flag.** Die Lesestelle wirft nie (Fallback-Wortwahl) und der Name läuft danach durch dieselbe `layout.client_name`-Reinigung und das zentrale Escaping wie überall (T-04-34). Bewusst so, damit auch die Verbindung einer gesperrten Registrierung trennbar bleibt |
| Neue Store-Abhängigkeit des AUTH-01-Zweigs: ein App-Passwort-Tool-Aufruf öffnet ab jetzt den Store und damit den OCS-Abruf des Datenschlüssels; ist er nicht lesbar, antwortet die Grenze 503 statt zu bedienen | 04-01-SUMMARY (Beobachtung) | T-04-06 | informativ, gewollte fail-closed-Richtung; ein Satz für `docs/exapp-install.md` in einem späteren Plan (kein Sicherheitsdefekt) |
| Neue ausgehende Verbindung im Lifecycle: `/enabled` spricht ab jetzt synchron mit Nextcloud | 04-04-SUMMARY (Beobachtung) | T-04-41 | informativ, zugeordnet; ein hängendes Nextcloud verzögert das Aktivieren, kann es aber nicht scheitern lassen |
| Wegweiser sichtbar für jeden Nutzer der Instanz, auch ohne je eine Verbindung | 04-04-SUMMARY (Beobachtung) | entfällt | geprüft: der Eintrag ist ein Link plus Beschreibung, nennt keinen Kontostand und keine Verbindung; gewollt |

Anmerkung zur Prozessqualität: anders als in Phase 3 tragen alle vier SUMMARYs dieser Phase
einen `## Threat Flags`-Abschnitt, jeder bildet seine Flags auf Register-Ids ab. Die
Prozesslücke aus Phase 3 (fehlender Flag-Abschnitt) ist damit geschlossen.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-08-17 | 27 | 27 | 0 | gsd-security-auditor (opus), ASVS 1, `block_on: open`. Belege: Quelltext bei `873b381`, eigener Lauf der vollen Suite (1543 passed, 82 deselected), alle sechs Gates grün (ruff check, ruff format 150 Dateien, pyright 0/0/0, vulture leer, check_tool_budget 11268/12500 16 Tools exit 0, pytest), uv.lock-Diff selbst nachgezogen |

Anmerkungen aus dem Audit:

- **Was dieses Audit nicht getan hat:** keine Suche nach neuen Schwachstellen. Grundlage sind
  die 27 Zeilen der vier threat_model-Blöcke, jede einzeln gegen den Quelltext gehalten.
  Feststellungen aus 04-REVIEW.md und 04-VERIFICATION.md erscheinen hier nur, wo sie eine
  deklarierte Gegenmaßnahme berühren, oder als benanntes Restrisiko AR-04-xx.
- **Der Kern der Phase, der pro-Konto-Schalter (EXAPP-02), ist geschlossen:** R1 ist die
  dritte und letzte Prüfung der einen Transportgrenze (`middleware.py:142`), hinter Handshake
  und Bearer, beide Anschlussarten laufen in denselben `_switch_refusal`, der Read ist lokales
  SQLite ohne Cache (D-47, D-48). Die vier Wächter dazu sind in dieser Session grün gelaufen.
- **Die drei Review-Blocker/Highs sind im Code geschlossen, nicht nur im Bericht:** BL-01
  (`_hand_back` nach `_end_connection`, `provider.py:782`, Commit 700a935), HI-01
  (`CLASS_CONNECTIONS` mit Konto-Keying, Commit 7ada840), HI-02 (`form_or_none` → generische
  Seite statt Traceback, Commits ac4015e/23df0a1). Jeder mit laufendem Wächter-Test geprüft.
- **Zur UI-Text-Frage (AR-04-02) wurde bewusst kein Codeeingriff gemacht:** der Satz "switched
  off" übertreibt unter der Disposition "akzeptieren", aber die Ersatzformulierung ist Teil der
  Design-Entscheidung BL-10 (durchsetzen vs. präzisieren+akzeptieren) und wurde nicht geraten.
  Im Audit wurde keine Implementierungsdatei geändert.
- **Kein Live-Redeploy:** die exapp-Topologie ist am Ende von Plan 04-04 abgebaut (STATE.md),
  SC 5 und A1 ruhen auf dem aufgezeichneten Lauf vom 2026-08-17 plus in-process-Wächtern,
  dieselbe Beweisform wie Phase 3 unter C-01 (AR-04-04, AR-04-01).

---

## Sign-Off

- [x] Alle 27 Positionen tragen eine Disposition (23 mitigate, 4 accept, 0 transfer)
- [x] Jede Position wurde nach ihrer Disposition geprüft, keine übersprungen
- [x] Akzeptierte Restrisiken mit Id, Begründung, Owner und Datum eingetragen (AR-04-01 bis AR-04-06)
- [x] `threats_open: 0` erreicht
- [x] Die drei Verifier-Concerns AR-04-02/03/04 explizit behandelt und als Restrisiko mit Backlog-Id geführt; die UI-Text-Frage entschieden (kein Eingriff, weil design-gebunden)
- [x] Alle sechs Gates grün, uv.lock unverändert
- [x] `status: verified` gesetzt

**Freigabe:** erteilt. Kein deklarierter Threat des Registers ist offen; alle offenen Punkte
sind bewusst akzeptierte Restrisiken AR-04-xx mit Backlog-Referenz (BL-08 bis BL-11) oder eine
ausstehende menschliche Browser-Sichtung (AR-04-01). Im Audit selbst wurde keine
Implementierungsdatei geändert.
