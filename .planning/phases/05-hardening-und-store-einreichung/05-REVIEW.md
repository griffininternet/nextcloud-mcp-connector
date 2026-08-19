---
phase: 05-hardening-und-store-einreichung
reviewed: 2026-08-19T21:30:00Z
depth: standard
files_reviewed: 37
files_reviewed_list:
  - appinfo/info.xml
  - docs/client-setup.md
  - docs/exapp-install.md
  - docs/faq.md
  - docs/oauth-setup.md
  - docs/privacy.md
  - docs/store-submission.md
  - docs/uninstall.md
  - scripts/bootstrap_exapp.sh
  - src/mcp_connector/__init__.py
  - src/mcp_connector/entry_exapp.py
  - src/mcp_connector/exapp/admin_settings.py
  - src/mcp_connector/exapp/config_values.py
  - src/mcp_connector/exapp/lifecycle.py
  - src/mcp_connector/exapp/occ.py
  - src/mcp_connector/exapp/purge.py
  - src/mcp_connector/exapp/ui/connections.py
  - src/mcp_connector/exapp/ui/errors.py
  - src/mcp_connector/exapp/ui/strings.py
  - src/mcp_connector/oauth/connect.py
  - src/mcp_connector/oauth/consent.py
  - src/mcp_connector/oauth/crypto.py
  - src/mcp_connector/oauth/store.py
  - tests/contract/test_no_destructive_calls.py
  - tests/integration/test_credential_flood.py
  - tests/integration/test_permission_parity_share.py
  - tests/unit/test_connections_page.py
  - tests/unit/test_exapp_admin_settings.py
  - tests/unit/test_exapp_config_values.py
  - tests/unit/test_exapp_entry.py
  - tests/unit/test_exapp_env_setup.py
  - tests/unit/test_exapp_purge.py
  - tests/unit/test_oauth_connect.py
  - tests/unit/test_oauth_consent.py
  - tests/unit/test_oauth_crypto.py
  - tests/unit/test_oauth_store.py
  - tests/unit/test_oauth_ui.py
findings:
  critical: 1
  warning: 3
  info: 6
  total: 10
status: issues
---

# Phase 05: Code Review Report

**Reviewed:** 2026-08-19T21:30:00Z
**Depth:** standard
**Files Reviewed:** 37
**Status:** issues_found

## Summary

Gegenstand des Reviews waren die Härtungs- und Store-Artefakte der Phase 5: das Admin-Settings-Formular (BL-06) mit dem Konfigurations-Overlay, der Purge-Pfad (`occ mcp_connector:purge`), die drei Enforcement-Punkte des Konto-Schalters (BL-10), das Manifest samt Store-Text-Gates, das Bootstrap-Skript und die zugehörige Dokumentation.

Gesamteindruck: Die sicherheitskritischen Pfade (OAuth-Flows, CR-01-Relay-Abwehr, Anti-Forgery mit Purpose-Trennung, AES-GCM mit AAD-Bindung, Fail-closed-Verhalten, Lösch-Reihenfolge des Purge) sind konsequent umgesetzt und ungewöhnlich dicht getestet, inklusive Gegenproben für jedes Gate. Es gibt jedoch einen Blocker: Das Validierungsnetz der Admin-Werte lässt genau den Wert durch, den der eigene Startpfad anschließend mit `SystemExit(2)` quittiert. Damit lässt sich die Deadlock-Situation, die Plan 05-04 explizit beseitigt hat, durch eine plausible Admin-Eingabe wieder herstellen, und zwar in einer Form, die sich über die Oberfläche nicht mehr korrigieren lässt.

## Critical Issues

### CR-01: Gespeicherte `public_url` mit `http://` auf Nicht-Loopback-Host führt in eine Crash-Loop und reproduziert den Settings-Deadlock

**File:** `src/mcp_connector/exapp/config_values.py:205-235` (Validierung), `src/mcp_connector/entry_exapp.py:289-338` (Startpfad), `src/mcp_connector/oauth/provider.py:1100-1115` (Issuer-Refusal)

**Issue:** `config_values._public_url` prüft Fragment, Credentials, Host und Port, aber nicht die Regel, die der Wert als `issuer` tatsächlich erfüllen muss: https, mit Loopback-Ausnahme. `config.normalize_base_url` akzeptiert `http` auf jedem Host (verifiziert in `config.py:121-132`). Trägt eine Administratorin im Admin-Formular `http://cloud.example.com/exapps/mcp_connector` ein (naheliegender Tippfehler statt `https://`, oder eine Homelab-Instanz ohne TLS), passiert Folgendes:

1. Der Wert überlebt `_usable_value` und gewinnt per Präzedenzregel über Deploy-Umgebung und Default.
2. Beim nächsten Disable/Enable liest `entry_exapp.main` das Overlay, `build_exapp_app` ruft `auth_routes` auf, das SDK verweigert den Nicht-https-Issuer, `provider.auth_routes` übersetzt das in einen `ToolError`, und `main` beendet den Prozess mit `SystemExit(2)`.
3. Der Container geht in eine Restart-Loop (identische Mechanik wie beim dokumentierten 0.1.0-Fehlbild "Restarting (2)" in `docs/store-submission.md`). Die App wird nie wieder `enabled`, damit verschwindet das Admin-Formular (AppAPI liefert nur Formulare aktivierter Apps aus), und der fehlerhafte Wert kann über die Oberfläche nicht mehr korrigiert werden.
4. Auch der Env-Weg hilft nicht: Der gespeicherte Admin-Wert gewinnt laut Präzedenzregel über `NC_MCP_PUBLIC_URL`. Die Korrektur erfordert einen Eingriff in `oc_appconfig_ex` bzw. die AppAPI-Konfigurations-API von Hand.

Das ist exakt der Deadlock, den Plan 05-04 mit "the process stays alive on purpose, so that form exists at all" beseitigt hat, wieder erreichbar über das Formular selbst. Der Docstring von `_public_url` beansprucht, die "extra conditions" existierten, weil der Wert zum Issuer wird (T-05-01), lässt aber genau die Issuer-Bedingung aus, an der der Start scheitert. Kein Test deckt den Fall: `test_an_unusable_admin_value_changes_nothing` parametrisiert "no scheme", Fragment und Credentials, aber nicht Nicht-Loopback-`http`.

**Fix:** Beide Hälften schließen, Validierung UND Startpfad:

```python
# config_values.py, in _public_url nach dem Port-Check:
if parts.scheme != "https" and host not in ("localhost", "127.0.0.1", "::1", "[::1]"):
    return _rejected(
        "public_url",
        "is http on a host that is not loopback; the issuer of the authorization "
        "server has to be https (RFC 8414)",
    )
```

Zusätzlich in `entry_exapp.main`: Wenn `build_exapp_app` mit dem Issuer-`ToolError` scheitert, nicht `SystemExit(2)`, sondern den `NC_MCP_PUBLIC_URL`-Wert aus `resolved` entfernen, die Fehlerzeile loggen (analog zur bestehenden Setup-State-Zeile) und die App mit dem Default weiterservieren, damit das Formular korrigierbar bleibt. Testfall ergänzen: gespeicherter Wert `http://cloud.example.com/x` darf weder das Overlay erreichen noch den Start beenden.

## Warnings

### WR-01: Purge leert Tabellen und löscht den Schlüssel auch dann, wenn keine einzige Revocation gelang

**File:** `src/mcp_connector/exapp/purge.py:140-153`

**Issue:** `purge` führt `_empty(store)` und `crypto.delete_key(env)` bedingungslos nach `_hand_back_every` aus. Schlagen alle Revocations fehl (z. B. weil der Container Nextcloud in diesem Moment nicht erreicht, während der occ-Aufruf über den internen AppAPI-Pfad sehr wohl ankam, oder bei 5xx unter Last), werden trotzdem alle sieben Tabellen geleert und der Datenschlüssel gelöscht. Damit ist die einzige maschinenlesbare Zuordnung "welches App-Passwort gehört zu welcher Verbindung" zerstört, während sämtliche App-Passwörter in Nextcloud gültig bleiben, also genau das Szenario, das Pattern 4 der eigenen Recherche als Katastrophe beschreibt. Die Antwort nennt nur die Zahl (`revoke_failures`), nicht die betroffenen Konten (bewusst, V7), und ein zweiter Lauf des Kommandos kann nichts mehr nachholen, weil die Zeilen weg sind. Die Milderung existiert (Einträge heißen `MCP Connector: <client>` in `oc_authtoken`, Runbook `docs/uninstall.md` beschreibt die manuelle Bereinigung pro Nutzer), aber der Totalausfall-Fall (failures == connections > 0) signalisiert eine Störung und keinen Einzelfehler und sollte den destruktiven lokalen Teil nicht auslösen.

**Fix:** Vor `_empty` unterscheiden: Wenn `rows` nicht leer ist und `revoked == 0` (kompletter Fehlschlag, typisch Transportfehler), mit `{"purged": false, "hint": ...}` abbrechen und den Store unangetastet lassen, damit der Lauf nach Behebung der Störung wiederholbar ist. Teilfehlschläge können wie bisher gezählt und fortgesetzt werden. Tests `test_a_failed_revocation_does_not_stop_the_purge_and_is_a_number` und `test_a_revocation_that_never_reaches_nextcloud_is_a_number_too` entsprechend anpassen (sie pinnen das aktuelle Verhalten).

### WR-02: `--force`-Erkennung ist für eine irreversible Aktion zu permissiv

**File:** `src/mcp_connector/exapp/purge.py:228-280`

**Issue:** Zwei Aufweichungen an der Stelle, an der die Doku "checked here as well, because what AppAPI hands over is input" verspricht:

1. `_forced` akzeptiert das Flag auch als Query-Parameter (`?force=...`), obwohl die vermessene AppAPI-Invocation das Flag ausschließlich im JSON-Body (`{"occ": {"options": {...}}}`) transportiert. Ein `?force=` mit leerem Wert zählt über `_is_set("")` als gesetzt (leerer String ist nicht in `FALSE_WORDS`).
2. `_is_set` behandelt jeden unbekannten String als Ja ("Only a spelled out no is a no"). Für einen Symfony-Flag im Modus `none` ist das begründbar, aber es invertiert für die destruktivste Aktion der App die sonst überall gelebte Fail-closed-Regel (`registry._switch` und `config_values._switch` verweigern Unbekanntes ausdrücklich). `{"options": {"force": "maybe"}}` löst den Purge aus.

Die Erreichbarkeit ist durch den AppAPI-Handshake, die fehlende Route im Manifest und den `x-origin-ip`-Check stark eingeschränkt, deshalb Warning und nicht Critical. Trotzdem ist jede zusätzliche akzeptierte Form Angriffsfläche für den Tag, an dem eine der drei Schranken bröckelt.

**Fix:** Query-Parameter-Zweig entfernen (AppAPI sendet ihn nie; `test_every_shape_of_the_flag_appapi_may_send_is_accepted` deckt ihn nicht ab, es bricht also kein Test). In `_is_set` nur `True`, `None`, `1`/`"1"`/`"true"`/`"yes"`/`"on"` als gesetzt werten und Unbekanntes mit `purged: false` plus Log-Zeile beantworten, analog zu `_switch`.

### WR-03: `PUBLIC_URL` wird ungeprüft in den JSON-Registrierungs-Payload interpoliert (gleiche Fehlerklasse wie IN-07)

**File:** `scripts/bootstrap_exapp.sh:145, 723-728`

**Issue:** IN-07 hat `APP_PORT`, `MANUAL_APP_PORT` und `REGISTRY` per `require_port_number`/`require_registry_shape` gepinnt, weil sie unquotiert bzw. in einen String der `json_info`-Payload interpoliert werden und aus der aufrufenden Shell überschreibbar sind. `PUBLIC_URL="${NC_EXAPP_PUBLIC_URL:-...}"` hat exakt dieselben Eigenschaften: aus der Shell überschreibbar, landet als `"value":"${PUBLIC_URL}"` unescaped im JSON, wird aber von keinem der Validatoren geprüft. Ein Wert mit `"` erzeugt bestenfalls ungültiges JSON, schlimmstenfalls zusätzliche Felder, die AppAPI stillschweigend übernimmt, das ist wortgleich die Begründung von IN-07. Auch das Staging-Profil validiert nur `NC_STAGING_DOMAIN`, nicht die `NC_EXAPP_PUBLIC_URL`-Übersteuerung.

**Fix:** Einen `require_url_shape`-Validator ergänzen (z. B. `^https?://[A-Za-z0-9._:-]+(/[A-Za-z0-9._/-]*)?$`, insbesondere ohne `"` und `\`) und im Hauptlauf vor `json_info` auf `${PUBLIC_URL}` anwenden, daneben eine Zeile in `test_the_bootstrap_calls_both_registration_validators` bzw. einen eigenen Parametrize-Fall in `test_the_registration_inputs_are_pinned_before_json_info`.

## Info

### IN-01: Body-Größenschranke des Purge-Handlers ist per Chunked-Encoding umgehbar

**File:** `src/mcp_connector/exapp/purge.py:283-306`

**Issue:** `_payload` prüft nur den angekündigten `Content-Length`-Header. Ein Request mit `Transfer-Encoding: chunked` (oder nicht-numerischem Content-Length) hat keinen bzw. keinen digit-Header und wird von `request.body()` vollständig und unbegrenzt in den Speicher gelesen. Erreichbar nur über den authentifizierten internen AppAPI-Pfad, daher informativ.

**Fix:** Statt der Header-Prüfung den Stream begrenzt lesen (z. B. `request.stream()` aufsummieren und bei `MAX_BODY_BYTES` abbrechen), wie es `oauth/connections.py` laut LO-08 für seine Formulare tut.

### IN-02: `connect_routes` dupliziert die Opener-Logik von `store.store_opener`

**File:** `src/mcp_connector/oauth/connect.py:127-146` vs. `src/mcp_connector/oauth/store.py:1275-1310`

**Issue:** Der Fallback-Zweig (Double-checked Locking, Schlüssel zuerst, `purge_expired` beim ersten Öffnen, Cache im Closure) existiert zweimal wortgleich. Im ExApp-Deployment ist die Kopie tot (Entry übergibt `store_provider`), sie läuft nur, wenn `connect_routes` ohne Provider gebaut wird. Eine künftige Änderung an einer Stelle (z. B. eine zusätzliche Prüfung beim Öffnen) verfehlt die andere.

**Fix:** `store_provider = store_provider or store_opener(env)` am Anfang von `connect_routes`, die lokale Kopie entfernen.

### IN-03: `doc_url` des Admin-Formulars zeigt auf einer unkonfigurierten Installation auf `http://127.0.0.1:8765/connections`

**File:** `src/mcp_connector/exapp/admin_settings.py:80-89`

**Issue:** `form_scheme` baut `doc_url` aus `config.public_url(env)`. Auf einer frischen Store-Installation (kein Wert gesetzt) ist das der Loopback-Default, also ein toter Link, ausgerechnet in dem Formular, mit dem der Zustand behoben wird. Kein Sicherheitsproblem (T-04-40 wird eingehalten, kein interner Host), aber verwirrend.

**Fix:** Bei `config.public_url(env) == config.DEFAULT_PUBLIC_URL` das Feld `doc_url` weglassen oder auf die Repository-FAQ zeigen.

### IN-04: Werkzeugzahl inkonsistent dokumentiert (15 vs. 16 Tools)

**File:** `docs/oauth-setup.md:263, 522` vs. `docs/client-setup.md:11` und `docs/store-submission.md:90`

**Issue:** Die Evidenzblöcke vom 2026-08-16 nennen `tools=15` bzw. "15 tools listed", die übrigen Dokumente durchgehend 16 Tools. Die Evidenz ist als wörtliche Kopie datiert und daher formal korrekt, aber nichts erklärt die Differenz; ein Leser, der die Zahl nachzählt, hält eine der beiden Angaben für falsch.

**Fix:** Eine Klammerbemerkung an einer der 15er-Stellen ("Stand 0.1.0; seit ... sind es 16") oder die Evidenz beim nächsten Lauf erneuern.

### IN-05: privacy.md behauptet, "issued secrets" der Clients würden gespeichert

**File:** `docs/privacy.md:38`

**Issue:** Die Tabellenzeile "Client registrations | clients | the assistant apps, their redirect targets and issued secrets" liest sich, als lägen Client-Secrets im Klartext in der Datenbank. Tatsächlich speichert `clients.client_secret_hash` nur den SHA-256-Digest (`store.py:145-152`). Für ein Dokument, das sich an Datenschutzbeauftragte richtet, ist die Formulierung unnötig ungenau, in die falsche Richtung.

**Fix:** "issued secrets (stored as a hash only, never in the clear)" oder die Zeile in die Hash-Zeile der Tokens integrieren.

### IN-06: Konsens-Screen wird einem pausierten Konto beim Reload noch gerendert

**File:** `src/mcp_connector/oauth/consent.py:302-304`

**Issue:** `_screen` springt bei bereits existierender Authorization-Zeile (`load_authorization(flow_id) is not None`) direkt zu `_decision`, ohne den Konto-Schalter zu lesen. Ablauf: Sign-in beendet (Zeile existiert), Konto pausiert in anderem Tab, Consent-Screen neu geladen: die Approve/Deny-Buttons erscheinen, obwohl E9 der vertraglich zugesagte Zustand wäre. Kein Grant ist möglich (Enforcement-Punkt 3 in `_decide` fängt den Klick mit E9 und Withdraw ab), daher nur eine UX-Inkonsistenz gegenüber den drei dokumentierten Enforcement-Punkten.

**Fix:** In dem `signed_in is not None`-Zweig `_access_disabled` lesen und bei `True` denselben `_refuse_paused`-artigen Pfad antworten wie nach dem Poll.

---

_Reviewed: 2026-08-19T21:30:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
