---
phase: 04-per-user-verwaltung-und-prepare-context
plan: 03
subsystem: exapp-ui
tags: [exapp-02, connections, switch, csrf, idor, route-13, one-revocation-path, e2e]

# Dependency graph
requires:
  - phase: 04-per-user-verwaltung-und-prepare-context
    provides: "04-01: set_access, access_disabled, authorizations_of_user und das Schalter-Gate R1 an der Transportgrenze"
  - phase: 03-oauth-2-1
    provides: "03-04/03-06: layout.page mit den fünf Pflicht-Headern, die errors-Tabelle, form_token und der Ownership-Vergleich is_user"
  - phase: 03-oauth-2-1
    provides: "03-07: provider._end_connection als die eine Schreibreihenfolge eines Widerrufs, inklusive Verifier-Cache"
provides:
  - "exapp/ui/connections.py: S5 bis S8 als reine Templates, plus Pfad-, Feld- und Ergebnis-Konstanten (der Kontrakt für 04-04)"
  - "oauth/connections.py: connections_routes als die eine Route der Seite, mit Aktionsfeld, Ownership, HMAC und fail-closed Store-Zugriff"
  - "oauth/provider.py: end_connection(auth_id) als öffentlicher, geteilter Widerrufs-Pfad"
  - "oauth/store.py: families_of_authorization als der Lesezugriff, den ein Handle-Widerruf braucht"
  - "exapp/ui/layout.py: row_list als die eine neue Primitive, plus die drei CSS-Regeln des Component Inventory"
  - "exapp/ui/errors.py: E8 als achte Tabellenzeile, mit dem {host}-Fill für jede Seite"
  - "appinfo/info.xml und scripts/bootstrap_exapp.sh: Route 13 mit Begründung, in beiden Registrierungswegen"
affects: [04-04 settings entry and live proof, 05 store submission]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Eine Route mit Aktionsfeld statt vier Routen: die Liste, die Bestätigung, der Widerruf und der Schalter sind eine Ressource"
    - "Ein Anti-Fälschungs-Wert ist zweckgebunden an seinen Handle, damit er genau ein Formular bedient"
    - "Unbekannt, fremd und schon widerrufen antworten dieselbe Seite, verglichen nach Abzug des Nonce"
    - "Ein zweiter Widerrufs-Pfad wird nicht durch Disziplin verhindert, sondern durch einen Quelltext-Wächter"

key-files:
  created:
    - src/mcp_connector/exapp/ui/connections.py
    - src/mcp_connector/oauth/connections.py
    - tests/unit/test_connections_page.py
  modified:
    - src/mcp_connector/exapp/ui/layout.py
    - src/mcp_connector/exapp/ui/strings.py
    - src/mcp_connector/exapp/ui/errors.py
    - src/mcp_connector/oauth/provider.py
    - src/mcp_connector/oauth/store.py
    - src/mcp_connector/entry_exapp.py
    - appinfo/info.xml
    - scripts/bootstrap_exapp.sh
    - tests/unit/test_exapp_env_setup.py
    - tests/unit/test_exapp_entry.py
    - tests/unit/test_oauth_ui.py
    - vulture_whitelist.py

key-decisions:
  - "Der Schalter-HMAC ist zweckgebunden: form_token('access:' + Konto). Ein Zeilen-Wert kann damit kein Konto pausieren, und der Wert eines Kontos kein fremdes; beide Fälle sind als Test belegt"
  - "end_connection(auth_id) hebt die private Sequenz an die Oberfläche, statt sie zu kopieren: _end_connection nimmt jetzt family_ids statt family_id, und beide Token-Pfade reichen ihre eine Familie als Liste durch"
  - "Der Widerruf der Seite ruft Nextcloud nicht: note_cleanup markiert das App-Passwort als Waise, und der Sweep gibt es zurück (Pitfall 13); eine Seite, die auf den langsamsten Beteiligten wartet, ist eine Seite, die hängt"
  - "Eine fünfte Aktion ACTION_KEEP, weil das UI-SPEC für S7 zwei Submit-Buttons eines Formulars verlangt: 'Keep this connection' antwortet die Liste mit 200, während eine unbekannte Aktion die Liste mit 400 bekommt"
  - "Ein gefälschter Schalter-POST antwortet die unveränderte Liste, nicht den 'Already disconnected'-Callout: nichts wurde getrennt, und der Zustandssatz über der Liste ist die Wahrheit, die der Leser braucht"
  - "Der Client-Name kommt aus der gespeicherten Registrierung; eine unlesbare Registrierung wird zur Fallback-Wortwahl und nie zu einer Ablehnung, die der Nutzer nicht beheben kann"
  - "Route 13 ist PUBLIC mit Identitätsprüfung in der App, mit dem gemessenen CR-01-Grund im Manifest-Kommentar; kein DELETE, weil jede Zustandsänderung ein POST mit Aktionsfeld und Anti-Fälschungs-Wert ist"

patterns-established:
  - "Ein Wächter wird gegengeprüft, indem die geschützte Eigenschaft testweise entfernt wird: bleibt er grün, ist er keiner"
  - "Wo ein Akzeptanzkriterium ein grep ist, steht ein Test, der den Quelltext liest"

requirements-completed: []

# Metrics
duration: rund 70 Minuten
completed: 2026-08-17
---

# Phase 4 Plan 03: Die Connections-Seite Summary

**Ein Nutzer sieht seine verbundenen Assistenten auf einer Seite, trennt einen davon über genau den Widerrufs-Pfad, den auch `/revoke` benutzt, und legt dort den Schalter um: der unmittelbar nächste Tool-Aufruf desselben Tokens ist R1, ohne Challenge und ohne dass ein anderes Konto etwas merkt.**

## Performance

- **Completed:** 2026-08-17
- **Tasks:** 3 von 3
- **Tests:** 1447 vor dem Plan, 1507 danach (60 neue), 82 deselektiert wie vorher
- **Gates:** ruff check, ruff format --check, pyright, vulture, pytest, check_tool_budget: alle sauber
- **Tool-Budget:** unverändert 11268 von 12500 Bytes bei 16 Tools (dieser Plan registriert kein Tool)
- **uv.lock:** unverändert, keine neue Dependency (T-04-SC)

## Accomplishments

- **Die vier Screens sind eine Funktion und eine Bestätigungsseite.** `connections_page` rendert S5, S6 und S8, weil alle drei dieselbe Seite in einem anderen Zustand sind; eine zweite Funktion wäre ein zweiter Ort, an dem man den Schalter vergisst. Die Blockreihenfolge ist fest und getestet: Identität, Ergebnis-Callout, Schalter, Pause-Warnung, dann erst Abschnitt und Liste. Damit stimmen drei Regeln des UI-SPEC gleichzeitig: Ergebnis vor Warnung, Schalter direkt über der Warnung, beide Callouts über der Abschnitts-Überschrift.
- **Der Schalter trägt die benannte Akzent-Ausnahme.** An heißt `SWITCH_ON_STATE` plus Secondary-Button, aus heißt `SWITCH_OFF_STATE` plus **Primary**-Button. Ein Test hält fest, dass die Seite im Normalzustand keinen einzigen `btn-primary`-Button trägt, und ein zweiter, dass genau der paused-Zustand ihn bekommt.
- **`row_list` ist die eine neue Primitive.** `<ul class="rows">` aus `<li class="row">`, je Zeile Titel, Sekundärzeilen (`muted` oder `mono`, ein dritter Stil wirft) und ein Aktions-Fragment; escaped am einen Punkt über `_escape`. Dazu exakt die drei CSS-Regeln des Component Inventory, keine neue Farbe, Größe oder Abstufung, und `icons.py` blieb unberührt (ein Test zählt die drei Formen).
- **Der Handle ist nie sichtbarer Text.** `auth_id` steht ausschließlich in Hidden Fields, die Client-Id dagegen vollständig und nie gekürzt: sie ist das Einzige, was zwei Zeilen namens "Claude" unterscheidet. Beides ist als Test formuliert, einmal über den geparsten Text und einmal über das Markup.
- **Jede Zeile ist ihr eigenes Formular** mit `aria-label="Disconnect {client}"`. Dafür bekam `button_secondary` ein optionales `aria_label`; ein Formular um die ganze Liste hätte den abgeschickten Wert davon abhängig gemacht, welcher Button zuletzt gedrückt wurde, und genau diese Mehrdeutigkeit darf eine destruktive Aktion nicht haben.
- **E8 ist eine Tabellenzeile, kein Mechanismus.** 403, "Sign in to see your connections", der Host in Worten und kein Link zu irgendeiner Anmeldeseite. `error_page` füllt `{host}` jetzt für **jede** Seite, nicht nur für die eine, die ihn nennt: ein Body, der den Host später nennt, kann so nicht mit unaufgelöstem Platzhalter ausgeliefert werden.
- **Die Route ist eine, mit zwei Verben und einer geschlossenen Aktions-Enumeration.** `confirm`, `disconnect`, `pause`, `resume`, `keep`; alles andere ist die Liste mit 400. Identität immer aus `appapi_user`, leer ist E8 auf beiden Verben, geprüft bevor irgendetwas gelesen wird.
- **Kein Antwortunterschied verrät einem Fremden etwas.** Unbekannter Handle, fremder Handle und schon widerrufener Handle liefern dieselbe Seite; der Test vergleicht die drei Antworten nach Abzug des Nonce zeichengenau. Ein fehlender oder falscher HMAC bekommt dieselbe Antwort plus eine Logzeile.
- **Der Widerruf der Seite ist derselbe Pfad wie der von `/revoke`.** `provider.end_connection(auth_id)` lädt die Autorisierung, liefert `False` für unbekannt und schon widerrufen (und schreibt dann nichts), bestimmt die Familien der Verbindung und führt die bestehende private Sequenz in ihrer Schreibreihenfolge aus. `_end_connection` nimmt dafür `family_ids` statt `family_id`; die beiden Token-Pfade reichen ihre eine Familie als Liste durch, sodass es weiterhin genau eine Sequenz gibt.
- **Der Pitfall-3-Wächter ist nachweislich einer.** Ein Quelltext-Test liest `oauth/connections.py` und `exapp/ui/connections.py` (Kommentarzeilen gefiltert) und verlangt, dass weder `revoke_authorization` noch `revoke_family` darin vorkommen. Gegenprobe ausgeführt: eine angehängte Funktion mit `await store.revoke_authorization(auth_id)` machte den Test sofort rot, nach dem Zurücknehmen war er wieder grün.
- **Route 13 steht in beiden Registrierungswegen.** `^/connections/?$`, `GET,POST`, PUBLIC, identisches `headers_to_exclude`, im Manifest mit einem eigenen Begründungsabsatz (gemessener CR-01-Grund, HaRP-Blacklist mit 502 auf die ganze ExApp) und in `scripts/bootstrap_exapp.sh` mit `access_level 0`. Beide Zähl-Tests verlangen jetzt dreizehn.
- **Der End-to-End-Wächter der Phase besteht, und er ist einer.** Ein verbundener Nutzer legt per POST auf `/connections` den Schalter um, und der unmittelbar nächste `POST /mcp` desselben Bearers ist 403 `access_disabled`, ohne `WWW-Authenticate`, mit `no-store`; nach `resume` wieder 200. Gegenprobe ausgeführt: mit `access_check` testweise entfernt fiel genau dieser Test um (200 statt 403), danach war er wieder grün. Die Negativ-Probe hält fest, dass der Pause-POST des einen Kontos den `/mcp`-Zugriff eines anderen nicht berührt.

## Task Commits

1. **Task 1: Seiten-Bausteine, Konstanten, E8 und die Templates S5 bis S8** - `d6fdb99` (rote Tests), `ebd7061` (Implementierung)
2. **Task 2: Routen mit Aktionsfeld, Ownership, HMAC und der geteilte Widerruf** - `d8226f5` (rote Tests), `93bdbeb` (Implementierung)
3. **Task 3: Route 13, Verdrahtung und der End-to-End-Wächter** - `32c982f` (rote Tests), `9f9c2bd` (Manifest, Bootstrap, Verdrahtung, Whitelist)

## Files Created/Modified

- `src/mcp_connector/exapp/ui/connections.py` (neu) - Pfad-, Feld- und Ergebnis-Konstanten, `Connection` als Zeilenform, `connections_page` (S5/S6/S8) und `confirm_page` (S7). Kein String-Literal in einer Template-Funktion, Datum als "12 August 2026" aus dem Unix-Timestamp in UTC, Host über den `_host`-Helfer aus der konfigurierten Public-URL.
- `src/mcp_connector/oauth/connections.py` (neu) - `connections_routes`, der Aktions-Dispatch, `_owned` (Ownership plus lebendig, drei Fälle eine Antwort), `_confirmed` (`compare_digest`), `_list` als der eine Ausgang jeder Antwort, `_store_or_page`/`_generic` nach dem `connect.py`-Vorbild.
- `src/mcp_connector/oauth/provider.py` - `end_connection(auth_id) -> bool` als öffentlicher Pfad, `_end_connection` nimmt `family_ids`.
- `src/mcp_connector/oauth/store.py` - `families_of_authorization`: `UNION` über `refresh_tokens` und `access_tokens`, weil eine Familie ohne Refresh-Zeile noch ein lebendes Access-Token haben kann.
- `src/mcp_connector/exapp/ui/layout.py` - `row_list`, `ROW_MUTED`/`ROW_MONO`, die drei CSS-Regeln, `aria_label` an `button_secondary` und `_button`.
- `src/mcp_connector/exapp/ui/strings.py` - die komplette Konstantenliste des UI-SPEC-Abschnitts "New string constants" (`CONNECTIONS_*`, `DISCONNECT_*`, `SWITCH_*`, `ERROR_SIGN_IN_*`, `SETTINGS_TITLE`, `SETTINGS_DESCRIPTION`), alle in `__all__`, ohne `CONNECTIONS_ADD_ACTION` und ohne den gestrichenen Zeiger-Satz in `CONNECTIONS_PAUSED_BODY`.
- `src/mcp_connector/exapp/ui/errors.py` - E8 als Tabellenzeile vor der generischen, `_host` und der `{host}`-Fill.
- `src/mcp_connector/entry_exapp.py` - `connections_routes` in derselben Anhäng-Schleife, mit dem Store-Opener dieser Anwendung und `provider.end_connection`.
- `appinfo/info.xml`, `scripts/bootstrap_exapp.sh` - Route 13 samt Begründung; die Zähl-Kommentare beider Dateien auf dreizehn gezogen.
- `tests/unit/test_connections_page.py` (neu) - 52 Tests: die acht Verhaltenspunkte aus Task 1, die zehn aus Task 2, dazu Escaping über Elementanzahl, Callout-Reihenfolge, Datumsformat, die drei identischen Antworten, der Verifier-Cache und der Quelltext-Wächter.
- `tests/unit/test_exapp_entry.py` - drei neue Tests: der End-to-End-Wächter, die Negativ-Probe des zweiten Kontos und die Verdrahtung Seite-zu-Store.
- `tests/unit/test_exapp_env_setup.py` - dreizehn statt zwölf, zwei neue Tests (deklarierte Seite gleich registrierte Route, Verben ohne DELETE), und `declared_connect_paths` prüft jetzt auf Segmentgrenze.
- `tests/unit/test_oauth_ui.py` - E8 in der `ERROR_PAGES`-Tabelle, damit die drei parametrisierten Phase-3-Tests auch die neue Seite prüfen.
- `vulture_whitelist.py` - der Phase-4-Block ist leer: `set_access` und `authorizations_of_user` haben mit diesem Plan ihre Aufrufer bekommen, `families_of_authorization` kam gleich mit ihrem.

## Deviations From Plan

- **[Rule 2 - Fehlende kritische Funktion] Eine fünfte Aktion `ACTION_KEEP`.** Das UI-SPEC verlangt für S7 zwei Submit-Buttons **eines** Formulars, unterschieden durch den Wert des Aktionsfeldes; der interfaces-Block des Plans nennt nur vier Werte. "Keep this connection" mit einer unbekannten Aktion und damit 400 zu beantworten wäre falsch, also ist `keep` ein benannter fünfter Wert, der die Liste mit 200 rendert. Die geschlossene Enumeration bleibt geschlossen. Commit `ebd7061`/`93bdbeb`.
- **[Rule 3 - Blockierend] `store.families_of_authorization` musste dazu.** `end_connection(auth_id)` soll laut Plan "alle zugehörigen Refresh-Familien bestimmen", und die öffentliche Store-API konnte das nicht: `revoke_family` nimmt eine Familien-Id, und keine Methode listete sie zu einem Handle. Der Lesezugriff ist ein `SELECT ... UNION` und steht deshalb in `store.py`, obwohl die Datei nicht in `files_modified` des Plans stand. Commit `93bdbeb`.
- **[Rule 2] `aria_label` an `button_secondary`.** Der Accessibility-Vertrag verlangt je Zeile `aria-label="Disconnect {client}"`, und `layout` hatte keinen Weg, ein Attribut an einen Button zu schreiben. Ein optionales Keyword an `button_secondary` und `_button` ist die kleinste Änderung; der sichtbare Text bleibt unberührt. Commit `ebd7061`.
- **[Rule 3 - Blockierend] `declared_connect_paths` in `test_exapp_env_setup.py` musste auf Segmentgrenze umgestellt werden.** Der Helfer filterte mit `url.startswith("^/connect")`, und `^/connections/?$` beginnt mit denselben acht Zeichen: die Onboarding-Familie hätte die neue Seite mitgezählt und der Mengenvergleich wäre umgefallen. Jetzt zählt nur `/connect` selbst und alles unter `/connect/`, mit einer neuen Familie `declared_connections_paths` daneben. Commit `9f9c2bd`.
- **[Rule 3 - Blockierend] `ERROR_PAGES` in `test_oauth_ui.py` musste E8 aufnehmen.** Der Phase-3-Test `test_the_table_has_exactly_the_seven_pages_of_the_contract` vergleicht die Tabelle mit `errors.CODES`. Mit E8 heißt er jetzt `..._eight_pages_...`, und die drei parametrisierten Tests (Problem plus nächster Schritt, Security-Header, kein Hinweis auf die gefeuerte Prüfung) laufen ab sofort auch gegen die neue Seite. Commit `ebd7061`.
- **Abweichung in der Antwort auf einen gefälschten Schalter-POST.** Der Plan sagt für Disconnect "antwortet wie 'Already disconnected'"; für Pause und Resume wäre dieser Callout eine falsche Aussage (es wurde nichts getrennt). Ein gefälschter Schalter-POST bekommt deshalb die unveränderte Liste plus eine Logzeile. Verraten wird dadurch nichts: ein Fälscher sieht die Antwort ohnehin nicht, und der Zustandssatz über der Liste ist in beiden Fällen die Wahrheit. Zwei Tests halten fest, dass weder ein Zeilen-Wert noch der Wert eines fremden Kontos den Schalter bedient.
- **Der Wächter benutzt `initialize` als den nächsten Tool-Aufruf.** Der Plan schreibt "der unmittelbar nächste `POST /mcp` desselben Tokens"; ein echter `tools/call` bräuchte die vollständige MCP-Sitzung und einen erreichbaren Nextcloud. Die Grenze entscheidet vor dem Transport, also ist jeder MCP-Request die gleiche Probe, und der Test benutzt denselben `INITIALIZE`-Body wie die bestehenden Boundary-Tests von 04-01.
- **Kein Nextcloud-Aufruf im Seiten-Widerruf.** `end_connection` gibt das App-Passwort nicht an Nextcloud zurück, sondern schreibt `note_cleanup`; das Zurückgeben erledigt `sweep_abandoned`. Das folgt dem Plan wörtlich und ist dieselbe Begründung wie auf dem Token-Pfad (Pitfall 13): eine Seite, die auf den langsamsten Beteiligten wartet, ist eine Seite, die hängt.

## Threat Flags

| Threat ID | Ist-Zustand | Belegt durch |
|-----------|-------------|--------------|
| T-04-30 (Tampering, CSRF auf Disconnect und Schalter) | Geschlossen. Zustandsänderung nur per POST, verstecktes `form_token` unter dem Installations-Datenschlüssel, Vergleich mit `compare_digest`, `form-action 'self'` aus `layout.page`; der Schalter-Wert ist an `access:` plus Konto gebunden. | `test_a_disconnect_without_the_anti_forgery_value_changes_nothing` (drei Fassungen), `test_the_row_value_of_one_connection_does_not_disconnect_another`, `test_a_row_value_cannot_pause_the_account`, `test_the_switch_value_of_one_account_does_not_pause_another`, `test_a_get_never_changes_anything` |
| T-04-31 (Elevation of Privilege, geratene auth_id / IDOR) | Geschlossen. `is_user` gegen die HaRP-Identität je Zeile, und die drei Fälle unbekannt/fremd/widerrufen antworten nach Abzug des Nonce zeichengenau dieselbe Seite. | `test_an_unknown_a_foreign_and_a_revoked_handle_answer_the_same_page`, `test_the_page_lists_the_connections_of_the_account_behind_the_browser`, `test_a_disconnect_leaves_every_other_connection_alone` |
| T-04-32 (Information Disclosure, PHP-Proxy cacht die Kontoseite) | Geschlossen. `Cache-Control: no-store` auf jeder Antwort über `layout.page`, zusammen mit den vier anderen Pflicht-Headern. | `test_every_page_of_this_family_carries_the_five_required_headers`, dazu die Header-Assertion im End-to-End-Wächter |
| T-04-33 (Denial of Service, HaRP-Blacklist bei access_level USER) | Geschlossen. Route 13 ist PUBLIC mit Identitätsprüfung in der App; der gemessene CR-01-Grund steht als eigener Absatz im Manifest-Kommentar und im Kommentar der Bootstrap-Registrierung. | `test_the_manifest_declares_exactly_the_thirteen_routes_of_this_phase`, `test_the_bootstrap_registration_declares_the_same_thirteen_routes`, `test_the_manifest_passes_its_own_gate` |
| T-04-34 (Tampering, bösartiger Client-Name im Markup) | Geschlossen. Jeder Name läuft durch `layout.client_name` und dann durch das zentrale Escaping, auf der Zeile, in der Überschrift von S7 und im Ergebnis-Callout. | `test_a_hostile_client_name_does_not_add_a_single_element`, `test_a_hostile_client_name_is_readable_as_text`, `test_a_hostile_client_name_stays_text_on_every_screen_of_this_family`, `test_a_nameless_registration_is_shown_as_the_fallback_wording` |
| T-04-35 (Elevation of Privilege, zweiter Widerrufs-Pfad driftet) | Geschlossen. Der Zeilen-Widerruf läuft ausschließlich über `provider.end_connection`, inklusive Verifier-Cache-Invalidierung; ein Quelltext-Wächter hält `revoke_authorization` und `revoke_family` aus beiden neuen Modulen heraus und wurde durch einen probeweisen Direktaufruf gegengeprüft. | `test_the_page_never_ends_a_connection_on_a_path_of_its_own`, `test_a_disconnect_stops_the_token_of_that_connection_at_once`, `test_a_disconnect_revokes_the_refresh_family_of_that_connection` |
| T-04-36 (Spoofing, Routenmuster ohne Endanker) | Geschlossen. `^/connections/?$` vollständig verankert, `GET,POST` ohne DELETE, `headers_to_exclude` wie die anderen zwölf; die Zähl-Tests halten Manifest und Bootstrap deckungsgleich. | `test_the_connections_route_declares_both_verbs_and_no_third`, `test_the_declared_connections_page_is_the_registered_one`, `test_the_manifest_passes_its_own_gate` (Endanker-Prüfung des Gates) |
| T-04-37 (Denial of Service, Formular-Flut) | Geschlossen. Die Route hängt in `Throttled` mit der bestehenden refusal-gezählten Browser-Klasse `CLASS_AUTHORIZE`; keine neue Klasse und keine neue Drossel-Mechanik. | `test_the_page_is_throttled_as_the_browser_class_it_belongs_to` |
| T-04-SC (Tampering, Paket-Installationen) | Nicht eingetreten. Kein Paket installiert, `git diff --stat uv.lock` ist leer. | Gate-Lauf am Planende |

**Neue Angriffsfläche, ausdrücklich gemeldet:** `/connections` ist die dreizehnte deklarierte Route und die zweite PUBLIC-Route, hinter der ein Formular Zustand ändert (die erste ist `/authorize/decide`). Sie ist ohne Nextcloud-Konto erreichbar und antwortet dann E8 mit 403; jede zustandsändernde Aktion verlangt zusätzlich einen Anti-Fälschungs-Wert, den nur diese Installation erzeugen kann, und einen Ownership-Vergleich gegen die HaRP-Identität. Der offene Punkt WR-12/AR-03-08 aus Phase 3 (ein POST ohne Anti-Fälschungs-Merkmal) wiederholt sich hier nicht: `confirm` ändert nichts, und die vier Aktionen, die etwas ändern, tragen den Wert.

Zwei Beobachtungen über das Register hinaus, beide bewusst so:

- **Der Client-Name der Zeile kommt aus einer zweiten JSON-Lesestelle.** `oauth/connections.py` liest `client_name` direkt aus `clients.metadata_json`, statt `provider.get_client` zu benutzen: die Factory bekommt laut Kontrakt nur Store und `end_connection`, und die Liste soll auch die Verbindung einer inzwischen gesperrten Registrierung zeigen, damit man sie trennen kann. Die Lesestelle wirft nie, sie fällt auf die Fallback-Wortwahl zurück, und der Name läuft danach durch dieselbe `client_name`-Reinigung wie überall.
- **Der Widerruf lässt das App-Passwort vorerst bei Nextcloud.** `note_cleanup` markiert es; `sweep_abandoned` gibt es zurück. Für den Nutzer endet die Verbindung trotzdem sofort, weil jeder Token an der Autorisierung hängt, die widerrufen ist.

## What the next plans inherit

- **Plan 04-04 (Settings-Eintrag und Live-Beweis):** `strings.SETTINGS_TITLE` und `strings.SETTINGS_DESCRIPTION` (mit `{connections_url}`) stehen bereit, ebenso `ui/connections.CONNECTIONS_PATH` als das Ziel des `doc_url`. Offen bleibt der Registrierungs-Aufruf bei `/enabled`, der Live-Beweis der Topologie und die aus 04-01 übergebene SC-5-Messung (`uv run --no-sync python scripts/oauth_flow_check.py http://127.0.0.1:8081/exapps/mcp_connector --measure`, Sollwert: genau ein Nextcloud-Roundtrip je MCP-Aufruf). Beim Neubau der Topologie fällt der Live-Beweis dieses Plans mit ab: Seite öffnen, pausieren, ein Tool-Aufruf, R1 im Log.
- **Doku:** `docs/client-setup.md` (Zeile 339) und `docs/oauth-setup.md` (Zeile 572) versprechen bereits "the app's own connections page"; ab jetzt existiert sie unter `{public_url}/connections`. Ein Satz mit der Adresse und dem Schalter gehört in beide Dateien, zusammen mit dem Settings-Eintrag von 04-04 in einem Zug.
- **EXAPP-02 bleibt offen.** Dieser Plan liefert die Hand am Steuer (SC 1 in-Prozess und SC 2 vollständig); der Wegweiser in den Nextcloud-Settings und die Live-Abnahme gehören zu 04-04. `REQUIREMENTS.md` wurde deshalb nicht abgehakt.

## Self-Check: PASSED

- `src/mcp_connector/exapp/ui/connections.py`, `src/mcp_connector/oauth/connections.py`, `tests/unit/test_connections_page.py`: vorhanden.
- `src/mcp_connector/exapp/ui/layout.py`, `strings.py`, `errors.py`, `oauth/provider.py`, `oauth/store.py`, `entry_exapp.py`, `appinfo/info.xml`, `scripts/bootstrap_exapp.sh`, `vulture_whitelist.py`, die drei Testdateien: vorhanden und geändert.
- Commits `d6fdb99`, `ebd7061`, `d8226f5`, `93bdbeb`, `32c982f`, `9f9c2bd`: alle in `git log`.
- Keine Stubs, keine Platzhalter, keine TODO- oder FIXME-Marker in den geänderten Dateien.
