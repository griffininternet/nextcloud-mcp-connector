---
phase: 05-hardening-und-store-einreichung
reviewed: 2026-08-20T10:30:00Z
depth: standard
files_reviewed: 11
files_reviewed_list:
  - src/mcp_connector/exapp/config_values.py
  - src/mcp_connector/entry_exapp.py
  - src/mcp_connector/exapp/purge.py
  - scripts/bootstrap_exapp.sh
  - tests/unit/test_exapp_config_values.py
  - tests/unit/test_exapp_entry.py
  - tests/unit/test_exapp_env_setup.py
  - tests/unit/test_exapp_purge.py
  - docs/client-setup.md
  - docs/oauth-setup.md
  - docs/uninstall.md
findings:
  critical: 0
  warning: 1
  info: 6
  total: 7
status: issues_found
---

# Phase 05: Code Review Report (Re-Review nach Gap-Closure, Pläne 05-11 bis 05-16)

**Reviewed:** 2026-08-20T10:30:00Z
**Depth:** standard
**Files Reviewed:** 11
**Status:** issues_found

## Summary

Gegenstand: das Re-Review des Diffs `eebcc4c..HEAD`, also die Gap-Closure-Läufe der Phase 5. Geprüft wurden die vier geänderten Quellmodule, das Bootstrap-Skript, die vier zugehörigen Testdateien und die drei aktualisierten Dokumente. Zusätzlich wurden die aufgerufenen Nachbarmodule (`config.normalize_base_url`, `crypto.delete_key`, `loginflow.revoke_app_password`, `registry.client_policy`, `store.store_opener`, `provider.auth_routes`) gegen die Annahmen des neuen Codes gelesen.

**Verifikation der früheren Findings, jeweils explizit nachvollzogen:**

* **CR-01 (alt, http-Crash-Loop): geschlossen, beide Hälften.** Die Prävention steht in `config_values._public_url` (Zeilen 296 bis 301): http auf einem Nicht-Loopback-Host wird verworfen, `LOOPBACK_HOSTS` ist eine exakte Mengen-Mitgliedschaft über `urlsplit(...).hostname` (lowercase, IPv6 ohne Klammern), und die Testmatrix deckt die Umgehungsversuche (`localhost.example.com`, `127.0.0.1.example.com`, private Adresse, Groß-/Kleinschreibung, IPv6-Literal) sowie die Gegenrichtung (Loopback-http bleibt nutzbar, der Default in Code überlebt die Validierung). Die Rettung steht in `entry_exapp.main` (Zeilen 338 bis 374): genau ein Retry ohne `NC_MCP_PUBLIC_URL`, ein zweiter Fehlschlag ist `SystemExit(2)`, nichts wird nach Nextcloud zurückgeschrieben, der Wert erscheint in keiner Log-Zeile (auch der Host nicht, per Test gepinnt). Der Rescue-Pfad ist zusätzlich einmal ungestubbt gegen das echte SDK getestet (`test_an_unusable_address_from_the_deploy_environment_takes_the_same_way`).
* **WR-01 (alt, Purge trotz Totalausfall der Revocations): geschlossen.** `purge.py` bricht bei `rows and revoked == 0` ab, lässt Tabellen und Schlüssel unangetastet, antwortet mit `purged: false` plus `REVOKE_HINT` und bleibt wiederholbar. Die Linie liegt bewusst bei null, nicht bei eins (Teilfehlschläge zählen und laufen weiter, per Test `test_a_partly_failed_revocation_purges_and_counts_the_failure` gepinnt); das leere Deployment als Gegenprobe ist ebenfalls getestet. `docs/uninstall.md` dokumentiert den neuen Abbruchfall samt Handlungsanweisung.
* **WR-02 (alt, zu permissive force-Erkennung): im Kern geschlossen, ein Werttyp bleibt offen.** Der Query-String-Zweig ist entfernt (Test: `?force=1`, `?force=true`, `?force=` laufen nichts), `_is_set` arbeitet für Strings mit einer Positivliste (`TRUE_WORDS`), Unbekanntes ist ein Nein plus eine Log-Zeile ohne den Wert. Für JSON-Zahlen gilt die Positivliste jedoch nicht, siehe WR-01 (neu) unten.
* **WR-03 (alt, `PUBLIC_URL` ungeprüft im Registrierungs-Payload): geschlossen.** `require_url_shape` existiert, läuft im Hauptlauf vor jeder Registrierung (per Test der Position gepinnt), verbietet `"`, `\` und Whitespace, und läuft mit `grep -z`, sodass ein Wert mit eingebetteter Newline nicht auf seiner ersten Zeile durchrutscht (Testfall vorhanden).

Neu gefunden wurde kein Blocker. Es bleibt eine Warnung (die Zahlen-Lücke in `_is_set`) und eine Reihe kleinerer Punkte, darunter zwei aus dem alten Review offen gebliebene Infos, deren Dateien in diesem Diff angefasst, deren Findings aber nicht adressiert wurden (IN-01, IN-04).

## Narrative Findings (AI reviewer)

## Warnings

### WR-01: `_is_set` wertet jede JSON-Zahl ungleich null als force-Ja und unterläuft damit die eigene Positivlisten-Regel

**File:** `src/mcp_connector/exapp/purge.py:320-353`
**Issue:** Der WR-02-Fix (alt) begründet die Positivliste damit, dass für die eine nicht rückgängig machbare Aktion "a value nobody understands is a typo, and a typo is not a security switch". Für Strings ist das umgesetzt: `"2"` und `"-1"` sind ein Nein plus Warnung (per Test gepinnt). Für JSON-Integer gilt das Gegenteil: `isinstance(value, int)` mit `value != 0` macht `{"options": {"force": 2}}` und `{"options": {"force": -1}}` zu einem Ja, ohne Log-Zeile. Das ist eine sichtbare Asymmetrie (der String `"2"` verweigert, die Zahl `2` löscht die ganze Instanz) und exakt die Restfläche, die der eigene Docstring als Angriffsfläche benennt "for the day one of the three barriers in front of this handler falls". Die gemessene AppAPI-Invocation sendet Booleans, nie Zahlen; erreichbar ist der Pfad nur mit gültigem App-Secret hinter dem `x-origin-ip`-Check, daher Warning und nicht Critical.
**Fix:**
```python
if isinstance(value, int):
    if value in (0, 1):
        return value == 1
    logger.warning(...)  # dieselbe Zeile wie fuer ein unbekanntes Wort
    return False
```
Plus ein Parametrize-Fall in `test_a_body_without_the_force_flag_changes_nothing` (`{"options": {"force": 2}}`, `{"options": {"force": -1}}`).

## Info

### IN-01: Body-Größenschranke des Purge-Handlers bleibt per Chunked-Encoding umgehbar (offen aus 05-REVIEW alt, IN-01)

**File:** `src/mcp_connector/exapp/purge.py:356-379`
**Issue:** `_payload` prüft weiterhin nur den angekündigten `Content-Length`-Header (`announced.isdigit()`). Ein Request mit `Transfer-Encoding: chunked` oder ohne bzw. mit nicht-numerischem Content-Length wird von `request.body()` vollständig und unbegrenzt in den Speicher gelesen; die Docstring-Behauptung "an announced length above MAX_BODY_BYTES ... is not parsed at all" hält nur für den Header-Fall. `purge.py` wurde in diesem Diff geändert, das alte Info-Finding aber nicht adressiert. Erreichbar nur über den authentifizierten internen AppAPI-Pfad, daher weiterhin informativ.
**Fix:** `request.stream()` aufsummieren und bei `MAX_BODY_BYTES` abbrechen, wie es die Formulare von `oauth/connections.py` tun.

### IN-02: Die Rescue-Log-Zeile behauptet auch für einen Deploy-Env-Wert, er stünde im Admin-Formular

**File:** `src/mcp_connector/entry_exapp.py:354-366`
**Issue:** Nach der Härtung von `config_values._public_url` erreicht ein unbrauchbarer Formularwert den Build gar nicht mehr; der Rescue-Zweig greift real nur noch für einen unbrauchbaren `NC_MCP_PUBLIC_URL` aus der Deploy-Umgebung (genau der Fall, den `test_an_unusable_address_from_the_deploy_environment_takes_the_same_way` baut). Die Log-Zeile sagt aber unabhängig von der Quelle "The stored value is kept, so it can be corrected where it was entered" und verweist auf das Admin-Formular, in dem in diesem Fall nichts steht. Die Anleitung funktioniert trotzdem (ein Formularwert übersteuert die Variable), die Diagnose ist aber irreführend: eine Administratorin sucht einen gespeicherten Wert, den es nicht gibt, statt die Deploy-Variable zu korrigieren.
**Fix:** In der Zeile beide Quellen nennen, z. B. "correct the deploy variable, or set the address in <Formular> (a stored value wins over the variable), then disable and enable ...".

### IN-03: Ein Mixed-Case-`public_url` wird unverändert zum Issuer

**File:** `src/mcp_connector/exapp/config_values.py:258-302`
**Issue:** `_public_url` gibt den Wert nach `normalize_base_url` unverändert zurück; `test_https_and_every_loopback_spelling_reach_the_overlay` pinnt bewusst, dass `HTTPS://Cloud.Example.COM` wortgleich ins Overlay gelangt. Dieser String wird `issuer` und `resource`-Präfix, und die eigene Doku betont an mehreren Stellen, dass Clients diese Werte zeichengenau vergleichen (Trailing-Slash-Absatz in `docs/client-setup.md` und `docs/oauth-setup.md`). Ein Nutzer, der die Adresse kleingeschrieben in den Client eingibt, während die Metadaten den Mixed-Case-Issuer nennen, scheitert an einem Vergleich, den keine Log-Zeile erklärt. Schema und Host sind per RFC 3986 case-insensitiv, das Lowercasing wäre also verlustfrei.
**Fix:** In `_public_url` Schema und Host normalisieren (`parts._replace(scheme=parts.scheme.lower(), netloc=<host lowercased, Port erhalten>)` bzw. schlicht über `urlsplit`/`urlunsplit` neu zusammensetzen); den pinnenden Test auf die normalisierte Erwartung umstellen.

### IN-04: Werkzeugzahl 15 vs. 16 bleibt unerklärt (offen aus 05-REVIEW alt, IN-04)

**File:** `docs/oauth-setup.md:287,547` vs. `docs/client-setup.md:11,621`
**Issue:** `docs/client-setup.md` wurde in diesem Diff erweitert und verweist im MUCGPT-Protokoll ausdrücklich auf "16 at the time of writing, which is the number tests/contract/test_tool_surface.py holds", während die Evidenzblöcke in `docs/oauth-setup.md` weiterhin `tools=15` und "15 tools listed" zeigen, ohne dass die Differenz irgendwo eingeordnet wird. Die Evidenz ist datiert und wörtlich, formal also korrekt, aber ein Leser, der beide Seiten liest, hält eine der Zahlen für falsch.
**Fix:** Eine Klammerbemerkung an einer 15er-Stelle ("Stand des Laufs vom 2026-08-16; seither 16 Tools") oder die Evidenz beim nächsten Lauf erneuern.

### IN-05: Das Bootstrap-Skript benutzt `grep -Eq`/`-Eqz` auf Pipes, der eigene Guard-Test erkennt nur das Literal `| grep -q`

**File:** `scripts/bootstrap_exapp.sh:166,537,553,562,579` und `tests/unit/test_exapp_env_setup.py:1478-1491`
**Issue:** Der Kommentar über `wait_for_install` erklärt die Regel "grep on an occ pipe never uses -q here" mit dem SIGPIPE-Flake unter `pipefail`, und `test_no_grep_q_on_a_pipe_in_the_shell_scripts` erzwingt sie, prüft aber nur den Teilstring `| grep -q`. Die Validatoren (`require_host_name`, `require_hex64`, `require_port_number`, `require_registry_shape`, `require_url_shape`) pipen alle `printf`-Ausgaben in `grep -Eq` bzw. `grep -Eqz`, was der Test wegen des `-E` nicht sieht. Funktional ist das hier unkritisch (die Werte sind wenige Bytes, `printf` ist fertig, bevor `grep` beendet; das SIGPIPE-Risiko betrifft nur langlaufende Schreiber wie `docker exec`), aber Regel und Gate sind auseinandergelaufen: das nächste `| grep -Eq` an einer occ-Pipe würde der Test ebenfalls durchwinken.
**Fix:** Entweder den Test auf das Muster `\| grep -E?q` verschärfen und die Validatoren auf `grep -E ... >/dev/null` umstellen, oder die Regel im Kommentar auf "auf Pipes von langlaufenden Prozessen" präzisieren und die Ausnahme im Test dokumentieren.

### IN-06: Der Rescue in `main` behandelt jeden `ToolError` aus `build_exapp_app` als Issuer-Fall

**File:** `src/mcp_connector/entry_exapp.py:338-374`
**Issue:** Der Kommentar behauptet, der Issuer-Refusal sei "the only one of this function that is recoverable". Das stimmt heute: die einzige `ToolError`-Quelle zur Bauzeit von `build_exapp_app` ist `provider.auth_routes` (verifiziert; `client_policy`, `store_opener`, die Routen-Fabriken und die Krypto-Fehler laufen erst zur Request-Zeit). Der `except ToolError` ist aber typbreit: eine künftige zweite Bauzeit-Quelle würde still als Public-URL-Problem geloggt, die (dann möglicherweise gültige) Adresse gedroppt und der zweite Build mit einer verwirrenden Doppelmeldung beendet. Das ist keine heutige Fehlfunktion, nur eine Annahme ohne Marker.
**Fix:** Den Issuer-Refusal in `provider.auth_routes` mit einem eigenen Exception-Typ (z. B. `IssuerRefused(ToolError)`) markieren und den Rescue darauf einschränken; oder einen Kommentar-Test, der die `raise ToolError`-Stellen im Baupfad zählt.

---

_Reviewed: 2026-08-20T10:30:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
