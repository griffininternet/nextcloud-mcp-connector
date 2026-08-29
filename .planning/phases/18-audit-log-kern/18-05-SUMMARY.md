---
phase: 18-audit-log-kern
plan: 05
subsystem: auth
tags: [audit-log, oauth, claims, request-state, appapi, middleware]

# Dependency graph
requires:
  - phase: 18
    plan: 01
    provides: "AUDIT_STATE_ATTR als der eine Name, unter dem der Rekorder in der Anfrage liegt"
  - phase: 03
    provides: "OAuthIdentity, OAUTH_STATE_ATTR, StoreTokenVerifier und die Naht in exapp/middleware.py, an der die Identität einmal je Anfrage abgelegt wird"
provides:
  - "deps.Caller: vier Felder (nc_user, client_id, auth_id, client_name) und kein Geheimnis"
  - "deps.resolve_caller(ctx): der Aufrufer eines Werkzeugaufrufs in einem Aufruf, ohne await, ohne Netz, ohne Ausnahme"
  - "oauth.verifier.CLIENT_NAME_CLAIM: der Anspruch, in dem der Client-Name mitreist"
  - "OAuthIdentity.client_name: der bei der Registrierung genannte Name, Vorgabe leere Zeichenkette"
  - "RequireAppApi(audit_recorder=...): die Ablage des Rekorders unter AUDIT_STATE_ATTR"
  - "deps._request_of: der eine defensive Lesevorgang, den beide Leser der Anfrage teilen"
affects: [18-06, 18-07, 18-08, 19-audit-bedienung]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Ein Wert reist im claims-Feld des SDK-Tokenmodells mit, statt ihn später aufzulösen (AUTH_ID_CLAIM als Vorlage)"
    - "Zwei Auskunftsfunktionen nebeneinander: eine mit Geheimnis, die werfen darf, und eine ohne, die nicht werfen darf"
    - "Die Transportgrenze hinterlegt einen Wert vom Typ object; der Leser prüft den Typ selbst"

key-files:
  created:
    - tests/unit/test_audit_caller.py
  modified:
    - src/mcp_connector/oauth/verifier.py
    - src/mcp_connector/deps.py
    - src/mcp_connector/exapp/middleware.py
    - tests/unit/test_oauth_verifier.py

key-decisions:
  - "Der Client-Name kommt aus dem Client, den verify_token für die Sperrprüfung ohnehin schon lädt: null zusätzliche Lesevorgänge, Preis bis zu fünf Sekunden ein veralteter Name"
  - "client_name ist eine leere Zeichenkette und nie None, damit ein Leser nicht zwischen 'kein Name' und 'kein Feld' unterscheiden muss"
  - "Die drei Client-Angaben in Caller sind None statt leerer Zeichenketten: 'es gibt keinen Client' ist eine andere Aussage als 'ein Client ohne Namen'"
  - "Der Rekorder wird in __call__ hinterlegt und nicht in _deposit: _deposit läuft nur im OAuth-Zweig, der AppAPI-Weg hat aber einen Nutzernamen und gehört genauso ins Log"
  - "_request_of als gemeinsamer defensiver Lesevorgang: 'ein Kontext, den dieser Server nicht lesen kann' bedeutet für den Anmeldepfad und den Erfassungspfad dasselbe"

patterns-established:
  - "Der Erfassungspfad hat eine eigene Auskunft, die weniger weiß als der Anmeldepfad: kein Passwort, keine Ausnahme, keine Ein-/Ausgabe"
  - "Ausdrücklich nicht gelesene Quellen werden im Code benannt (params['_meta']), damit sie nicht eines Tages als Verbesserung wiederkommen"

requirements-completed: []
# AUDIT-01 bleibt Pending: der Eintrag entsteht erst mit dem Rekorder aus Plan 18-06.
# Dieser Plan liefert nur die Auskunft, aus der der Eintrag seine Angaben nimmt.
requirements-advanced: [AUDIT-01]

# Metrics
duration: 12min
completed: 2026-08-29
---

# Phase 18 Plan 05: Auskunft über den Aufrufer Summary

**Nutzer, Client-Id, Verbindungs-Id und Client-Name sind in einem synchronen Aufruf ablesbar, ohne zusätzlichen Nextcloud- oder Speicherzugriff, ohne Geheimnis und ohne Ausnahme; der Client-Name reist dafür im Anspruch des Tokens mit, und der Rekorder hat einen Platz in der Anfrage.**

## Performance

- **Duration:** 12 min
- **Started:** 2026-08-29T11:05:00Z
- **Completed:** 2026-08-29T11:15:00Z
- **Tasks:** 3 (Task 2 nach RED/GREEN)
- **Files modified:** 5 (1 neu, 4 geändert)

## Accomplishments

- `CLIENT_NAME_CLAIM` legt den registrierten Client-Namen in `AccessToken.claims`, gefüllt aus dem Client, den `verify_token` für die Sperrprüfung aus AUTH-07 ohnehin schon lädt. Kein `await` mehr, kein `load_client`, keine geänderte Reihenfolge der Prüfungen: `git diff -U0 src/mcp_connector/oauth/verifier.py | grep -c "await self._store\|load_client"` meldet 0.
- `OAuthIdentity` trägt `client_name` mit Vorgabe `""` und führt ihn im maskierten `__repr__` mit; `app_password='***'` steht unverändert daneben.
- `deps.Caller` hat genau vier Felder und keines davon ist ein Geheimnis. `resolve_caller` liest zuerst die hinterlegte Identität (alle vier Felder), sonst den Nutzernamen der AppAPI-Impersonation (drei Felder `None`), und jeder fehlende Zwischenschritt ergibt `None`.
- `resolve_caller` wirft unter keiner der geprüften Eingaben, auch nicht dort, wo `resolve_credentials` im selben Kontext `MCPError` wirft; der Testfall stellt beide Antworten nebeneinander.
- `params["_meta"]` bleibt ungelesen, und der Grund steht als Kommentar an der Funktion: der dort genannte Client ist selbstdeklariert und wäre eine zweite, ungeprüfte Identität neben der aus D-08 (T-18-13).
- `RequireAppApi` nimmt `audit_recorder` und hinterlegt ihn unter `AUDIT_STATE_ATTR`, für jede Anfrage, die alle drei Prüfungen bestanden hat, den AppAPI-Weg eingeschlossen. Ohne Rekorder wird nichts hinterlegt; die Middleware importiert `mcp_connector.audit.record` nicht.

## Task Commits

1. **Task 1: client_name reist im Anspruch des Tokens mit** - `cfe5075` (feat)
2. **Task 2: resolve_caller in deps.py** - `589bafc` (test, RED), `ee988da` (feat, GREEN)
3. **Task 3: Die Transportgrenze hinterlegt den Rekorder** - `5db38c0` (feat)

## Files Created/Modified

- `src/mcp_connector/oauth/verifier.py` - `CLIENT_NAME_CLAIM`, `OAuthIdentity.client_name`, der Name im Anspruch des Tokens und die Kopie in `resolve_identity`
- `src/mcp_connector/deps.py` - `Caller`, `resolve_caller`, `_request_of`, beide neuen Namen in `__all__`
- `src/mcp_connector/exapp/middleware.py` - `audit_recorder` als Konstruktorparameter, `_deposit_recorder`
- `tests/unit/test_audit_caller.py` - acht Fälle: die zwei Wege, vier Kontexte ohne Antwort, die Stelle mit der Ausnahme, die Form der Antwort und die zwei Fälle der Ablage
- `tests/unit/test_oauth_verifier.py` - zwei neue Fälle (Client mit Namen, Client ohne Namen), `seed` nimmt die Registrierung als Parameter

## Decisions Made

- **Der Name kommt vom bereits geladenen Client:** `verify_token` prüft mit `_get_client(..., may_fetch=False)`, ob der Client noch handeln darf, und hielt das Ergebnis bisher nicht fest. Jetzt wird es an einen Namen gebunden und sein `client_name` in den Anspruch gelegt. Der Preis steht als Kommentar dort: bis zu fünf Sekunden ein veralteter Name nach einer Umbenennung, was für ein Protokoll ohne Belang ist.
- **Leere Zeichenkette gegen `None`:** `OAuthIdentity.client_name` ist `""`, wenn der Client keinen Namen registriert hat; `Caller.client_name` ist `None`, wenn es überhaupt keinen Client gibt. Die beiden Fälle sehen im Log verschieden aus, weil sie verschiedene Dinge sind.
- **Die Ablage sitzt in `__call__`:** Der Plan nennt `_deposit` als Naht, aber `_deposit` läuft nur im OAuth-Zweig. Der Rekorder wird deshalb an derselben Stelle in derselben `request.state` hinterlegt, aber nach der dritten Prüfung, damit der AppAPI-Weg ihn ebenfalls bekommt. Genau das verlangt der Plan im Fließtext ("ausdrücklich auch für Anfragen ohne OAuth-Identität").
- **`_request_of` statt zweier Lesevorgänge:** Zwei Stellen, die einen Kontext defensiv auspacken, sind zwei Stellen, die sich über die Bedeutung von "unlesbar" uneinig werden können. `_oauth_identity` benutzt jetzt dieselbe Hilfe.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] `resolve_caller` fängt zusätzlich zur defensiven Leseart eine Ausnahme des AppAPI-Zweigs**
- **Found during:** Task 2 (Verhaltenspunkt 5: der Rekorder darf nicht werfen)
- **Issue:** `appapi_user` schluckt seine eigenen zwei Zurückweisungen, aber es erwartet ein Starlette-`Request`. Ein Kontext, dessen `request` etwas anderes ist (jeder Test, der einen Kontext fälscht, und jeder künftige Transport), hätte an `request.headers` eine `AttributeError` geworfen, und zwar mitten im Erfassungspfad, der laut D-13 nichts werfen darf.
- **Fix:** Der Aufruf steht in `try/except Exception` und ergibt `None`; der Kommentar sagt, warum ein breiter Fang hier die richtige Weite hat und was er abdeckt.
- **Files modified:** src/mcp_connector/deps.py
- **Verification:** Der parametrisierte Fall mit `None`, `object()`, einem Kontext ohne Anfrage und einem ohne Identität ist grün; alle sechs Gates grün.
- **Committed in:** `ee988da` (GREEN-Commit von Task 2)

---

**Total deviations:** 1 auto-fixed (Rule 2)
**Impact on plan:** Keine Erweiterung des Auftrags. Die Abweichung setzt ein Kriterium des Plans um ("wirft unter keiner Eingabe"), das die vorgeschriebene Leseart allein nicht getragen hätte.

## Issues Encountered

- Der Plan verweist für die Ablage des Rekorders auf `_deposit` (`middleware.py:229-235`). Diese Methode läuft nur, wenn ein Bearer geprüft wurde; der AppAPI-Weg erreicht sie nie. Der Fließtext desselben Plans verlangt die Ablage ausdrücklich auch für diesen Weg, also entscheidet der Fließtext, und `_deposit_recorder` sitzt in `__call__` hinter der dritten Prüfung. Der Grund steht im Docstring der neuen Methode.
- `Caller` und `resolve_caller` haben bis Plan 18-06 keinen Aufrufer im Produktionscode. Anders als bei `last_entry` und `sweep` brauchte es keinen Eintrag in `vulture_whitelist.py`: beide stehen in `deps.__all__`, und das reicht Vulture, so wie es bei `should_sweep` schon gereicht hat.

## Anforderungen

AUDIT-01 bleibt in `REQUIREMENTS.md` **Pending**. Die Anforderung verlangt einen Eintrag je
Werkzeugaufruf samt Erlaubnisliste und Vertragstest; dieser Plan liefert allein die Auskunft,
aus der ein solcher Eintrag seine Angaben nimmt. Der Rekorder entsteht in Plan 18-06, die
Erlaubnisliste und ihr Vertragstest in Plan 18-03 beziehungsweise 18-06. Ein Haken hier wäre
dieselbe Art von Aussage, die dieses Projekt bei AUDIT-02 und AUDIT-03 in den Plänen 18-01
und 18-04 bewusst zurückgehalten hat.

## Threat Flags

Keine. Der Plan bringt keine Route, keinen Netzzugang und keine neue Berechtigung. Die fünf
Fäden des Bedrohungsmodells sind eingelöst: T-18-12 durch die vier Felder ohne Geheimnis und
den ausdrücklichen Verzicht auf `resolve_credentials`, T-18-13 durch das ungelesene
`params["_meta"]` samt Begründung im Code, T-18-08 durch den ungeklammerten Transport des
Namens, dessen Klammerung im Audit-Modul unmittelbar vor dem Schreiben sitzt (`_clean_client_name`
aus Plan 18-01), T-18-06 durch die `None`-Antwort statt einer Ausnahme, T-18-SC durch das
unveränderte `pyproject.toml` und `uv.lock`.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 18-06 findet `resolve_caller(ctx)`, `AUDIT_STATE_ATTR` und einen Rekorder vor, der bereits in der Anfrage liegt; der Dekorator muss nur noch lesen, was beide hinterlassen haben.
- Plan 18-07 findet den Konstruktorparameter `audit_recorder` vor, an den der Schalter aus D-14 gehängt wird: ist der Schalter aus, wird `None` übergeben, und es wird nichts hinterlegt und nichts protokolliert.
- Der Client-Name steht ab jetzt in jeder aufgelösten Identität und überlebt damit `occ mcp_connector:purge`, sobald er in einer Zeile steht.

## Verification

- `uv run --no-sync pytest tests/unit tests/contract -q`: grün.
- `uv run --no-sync ruff check .`, `ruff format --check .`, `pyright`, `vulture src scripts vulture_whitelist.py`: alle grün über das ganze Repo.
- `uv run --no-sync python scripts/check_tool_budget.py`: 15712 Bytes, 21 Werkzeuge, Budget 18000, unverändert.
- `git status --short appinfo/ pyproject.toml uv.lock`: leer.

## Self-Check: PASSED

Alle fünf Dateien liegen auf der Platte, alle vier Commits stehen im Log
(`cfe5075`, `589bafc`, `ee988da`, `5db38c0`).

---
*Phase: 18-audit-log-kern*
*Completed: 2026-08-29*
