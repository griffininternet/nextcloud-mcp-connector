---
phase: 08-erreichbarkeits-spike-und-tables
plan: 01
subsystem: testing
tags: [nextcloud-mail, appapi, impersonation, spike, harp, bootstrap, integration-test]

# Dependency graph
requires:
  - phase: 02-exapp-shell
    provides: HaRP-Testtopologie, AppAPI-Credential-Modus, DAV-Spike als Vorbild
provides:
  - Messung der vier Mail-Wege unter reiner AppAPI-Impersonation (accounts, mailboxes, messages, OCS-Volltext)
  - Entscheidung fuer Phase 10 und 11 als Satz: Mail ist erreichbar, MAIL-01 bis MAIL-03 bleiben wie geschnitten
  - SCOPE_IGNORE-Risiko plus Ersetzbarkeits-Ausweg im Code und in der Doku benannt
  - reproduzierbare Topologie: Bootstrap installiert tables und mail und legt das Spike-Mail-Konto idempotent an
affects: [10-mail-strikt-lesend, 11-buendelung-budget-release, tables]

# Tech tracking
tech-stack:
  added: [Nextcloud-App mail 5.11.1, Nextcloud-App tables 2.2.2]
  patterns:
    - "Spike-Test protokolliert statt zu behaupten: _probe gibt Status, Content-Type, Form, Location und 120 Zeichen Koerper zurueck"
    - "Entscheidungskriterium steht als Code (_verdict), nicht nur als Prosa"
    - "Memo-Dict haelt eine brute-force-geschuetzte Route bei genau einem Request pro Lauf"

key-files:
  created:
    - tests/integration/test_exapp_mail_reach.py
    - docs/spike-mail.md
  modified:
    - scripts/bootstrap_exapp.sh
    - scripts/bootstrap_test_nc.sh

key-decisions:
  - "MAIL-04 ist beantwortet: alle vier Mail-Wege antworten unter reiner AppAPI-Impersonation mit JSON aus App-Code, keiner mit einer HTML-Loginseite und keiner mit einem Redirect auf /login; MAIL-01 bis MAIL-03, CTX-02, SEC-01 und die Toolzahl in TOOL-15 bleiben wie geschnitten"
  - "Stufe 1 des Spikes reicht: das Spike-Mail-Konto zeigt auf imap.invalid, weil occ mail:account:create-imap die Verbindung nicht prueft und jede Antwort aus App-Code den Beweis schon traegt; GreenMail bleibt eine Vorlage in docs/spike-mail.md, compose.exapp.yml ist unveraendert"
  - "ensure_mail_account entscheidet an der Ausgabe von occ mail:account:export und nicht an dessen Exit-Code: der Befehl endet auch fuer einen Nutzer ohne Konto mit 0, ein Exit-Code-Check haette bei jedem Lauf ein zweites Konto angelegt"
  - "Der Aufruf von ensure_mail_account steht nach ensure_user und nicht neben den ensure_app-Zeilen: auf einer frischen Topologie existiert alice dort noch nicht, und create-imap fuer einen unbekannten Nutzer ist ein Fehler"
  - "Die drei Listen-Routen bleiben ersetzbar; der Ausweg ist der Suchprovider mail plus die OCS-Volltextroute, und der Hinweis wandert in Phase 10 in den Modul-Docstring von clients/mail.py"

patterns-established:
  - "Spike-Protokoll: Kopf mit Versionen aus der laufenden Instanz, Entscheidungskriterium vor der Messung, Messtabelle, Decision, beide Kontrollen, Ersetzbarkeit, Eskalationsregel, Reproduktion, 'Was diese Messung nicht beweist'"
  - "Koerperkappung auf 120 Zeichen als Sicherheitsanforderung mit benannter Begruendung (T-08-01), nicht als Kosmetik"

requirements-completed: [MAIL-04]

# Metrics
duration: 42 min
completed: 2026-08-21
---

# Phase 8 Plan 01: Erreichbarkeits-Spike Mail Summary

**Vier Mail-Wege unter reiner AppAPI-Impersonation gemessen und protokolliert: accounts 200, mailboxes 500, messages 403, OCS-Volltext 404, alle vier mit JSON aus App-Code, damit ist MAIL-04 beantwortet und der Schnitt der Phasen 10 und 11 bestaetigt.**

## Performance

- **Duration:** 42 min
- **Started:** 2026-08-21T07:05:00Z
- **Completed:** 2026-08-21T07:47:00Z
- **Tasks:** 3
- **Files modified:** 4 (2 neu, 2 geaendert)

## Accomplishments

- Die einzige offene Unbekannte des Meilensteins ist gemessen, nicht geschaetzt: `tests/integration/test_exapp_mail_reach.py` laeuft gegen die HaRP-Topologie und protokolliert je Weg Statuscode, Content-Type, Antwortform, `Location` und 120 Zeichen Koerper.
- Das Ergebnis ist eindeutig ohne erreichbaren IMAP-Server. Das Entscheidungskriterium steht als Code (`_verdict`) und war vor der ersten Messung festgelegt, deshalb konnten die Zahlen es nicht nachtraeglich verschieben.
- Zwei Kontrollpruefungen machen die Messung beweiskraeftig: der messende Prozess traegt kein `NC_MCP_APP_PASSWORD` und keinen `NC_MCP_STATIC_BEARER`, die Datei enthaelt kein Basic-Schema (auch nicht als Zeichenkette), und ein `APP_SECRET` aus 64 Nullen wird abgewiesen.
- Das SCOPE_IGNORE-Risiko der drei internen Listen-Routen steht im Modul-Docstring des messenden Codes und als Abschnitt "Replaceability" in `docs/spike-mail.md`, samt Uebergabe an Phase 10.
- Die Topologie ist reproduzierbar: `bash scripts/bootstrap_exapp.sh` installiert `tables` und `mail` und legt das Spike-Mail-Konto idempotent an, ein zweiter Lauf aendert nichts.

## Die vier Messzeilen (woertlich)

| Weg | URL | erwarteter Status | gemessener Status | Content-Type | Form | Urteil |
|-----|-----|-------------------|-------------------|--------------|------|--------|
| accounts | `GET /index.php/apps/mail/api/accounts` | 200 | 200 | `application/json; charset=utf-8` | json | erreicht |
| mailboxes | `GET /index.php/apps/mail/api/mailboxes?accountId=1` | 500 mit JSON oder 200 mit leerer Liste | 500 | `application/json; charset=utf-8` | json | erreicht |
| messages | `GET /index.php/apps/mail/api/messages?mailboxId=0&limit=5` | 403 mit JSON | 403 | `application/json; charset=utf-8` | json | erreicht |
| ocs | `GET /ocs/v2.php/apps/mail/message/999999` | 404 im OCS-Envelope | 404 | `application/json; charset=utf-8` | json | erreicht |

Gemessen am 2026-08-21 gegen Nextcloud 34.0.3 (Build 34.0.3.2), AppAPI 34.0.0, Mail 5.11.1, HaRP-Topologie aus `compose.exapp.yml`.

## Der Entscheidungssatz (woertlich)

"Mail ist unter reiner AppAPI-Impersonation erreichbar: alle vier Wege antworten mit JSON aus
App-Code, keiner mit einer HTML-Loginseite und keiner mit einem Redirect auf `/login`.

Fuer Phase 10 und 11 folgt daraus: MAIL-01 bis MAIL-03 bleiben wie geschnitten, CTX-02, SEC-01
und die Toolzahl in TOOL-15 bleiben unangetastet."

## Task Commits

1. **Task 1: Topologie und Bootstrap fuer Tables und Mail** - `7c21b22` (chore)
2. **Task 2: Spike-Test, der protokolliert statt zu behaupten** - `07861ba` (test)
3. **Task 3: Messprotokoll, Entscheidung und Eskalationsregel** - `45df7c1` (docs)

## Files Created/Modified

- `tests/integration/test_exapp_mail_reach.py` (neu, 345 Zeilen) - Messung der vier Wege unter Impersonation, `_probe` mit 120-Zeichen-Kappung, `_verdict` als Entscheidungskriterium, beide Kontrollpruefungen, Protokolltabelle als letzter Test
- `docs/spike-mail.md` (neu, 177 Zeilen) - Messprotokoll mit Versionen aus der laufenden Instanz, Entscheidungskriterium, Messtabelle, Decision, "The two controls", "Replaceability", Eskalationsregel mit GreenMail-Vorlage, Reproduktion, Grenzen der Messung
- `scripts/bootstrap_exapp.sh` (geaendert) - `ensure_app tables`, `ensure_app mail`, neue idempotente Funktion `ensure_mail_account` nach dem Muster von `ensure_user`, Aufruf fuer alice mit `alice@example.test`
- `scripts/bootstrap_test_nc.sh` (geaendert) - `ensure_app tables`, bewusst kein Mail-Konto und kein `ensure_app mail`

`compose.exapp.yml` ist unveraendert, wie das Erfolgskriterium es fuer den eindeutigen Fall verlangt.

## Decisions Made

- **Stufe 1 genuegt.** Das Spike-Konto zeigt auf `imap.invalid`. `occ mail:account:create-imap` prueft die Verbindung nicht (`CreateImapAccount`), und jede Antwort aus App-Code beweist den erreichten Controller. Der 500er von `mailboxes` ist deshalb ein Messwert und kein Fehlschlag: `MailManager::getMailboxes` erzwingt den IMAP-Sync unbedingt (K7), `#[TrapError]` macht daraus JSON.
- **Ein Memo statt einer Fixture.** Die OCS-Volltextroute traegt `#[BruteForceProtection('mailGetMessage')]`, und Nextcloud zaehlt pro Quell-IP, was fuer eine ExApp eine IP fuer alle Nutzer ist. Ein modulweites Dict haelt die Zeile bei genau einem Request pro Lauf, obwohl sie von zwei Tests gelesen wird. Die Regel steht als Kommentar am Test und nicht in der Topologie, weil sie in Phase 10 in Produktionscode wandert.
- **Ids werden ein zweites Mal gelesen, statt die Kappung zu lockern.** `_account_id` stellt eine eigene Anfrage an die Kontenroute, weil `_probe` nur 120 Zeichen behaelt. Die Kappung fuer eine Bequemlichkeit zu weiten haette genau die Eigenschaft aufgegeben, die T-08-01 verlangt; die Kontenroute liest nur die Datenbank und traegt keinen Brute-Force-Zaehler.
- **Kein `assert status == 200` an keiner Stelle.** Falle 8 der Recherche: ein Spike, der ohne IMAP-Server auf 200 prueft, meldet "Mail unerreichbar" und kippt den Schnitt der Phasen 10 und 11 faelschlich.

## Deviations from Plan

### Auto-fixed Issues

**1. [Regel 3 - Blockierend] Aufrufreihenfolge von `ensure_mail_account` korrigiert**

- **Found during:** Task 1
- **Issue:** Der Plan verlangt den Aufruf "direkt nach den `ensure_app`-Zeilen". An dieser Stelle existiert der Nutzer `alice` auf einer frischen Topologie noch nicht (`ensure_user` laeuft erst danach), und `occ mail:account:create-imap` fuer einen unbekannten Nutzer ist ein Fehler, kein No-op. Der erste Bootstrap-Lauf auf einer leeren Instanz waere reproduzierbar rot geworden.
- **Fix:** Der Aufruf steht jetzt direkt hinter `ensure_user alice` / `ensure_user bob`, mit einem Kommentar, der die Reihenfolge begruendet. Die `ensure_app`-Zeilen liegen unveraendert dort, wo der Plan sie verlangt.
- **Files modified:** `scripts/bootstrap_exapp.sh`
- **Verification:** Zwei vollstaendige Bootstrap-Laeufe mit Exit-Code 0, der zweite meldet "mail account alice: exists"
- **Committed in:** `7c21b22`

**2. [Regel 1 - Bug] Existenzpruefung liest die Ausgabe, nicht den Exit-Code**

- **Found during:** Task 1
- **Issue:** Der Plan schlaegt `occ mail:account:export <uid>` als Pruefung vor, "ein Kommando, dessen Nicht-Null-Exit 'existiert nicht' bedeutet". Live gegen Mail 5.11.1 gemessen: der Befehl endet auch fuer einen Nutzer ohne jedes Konto mit Exit-Code 0 und gibt nichts aus. Eine Exit-Code-Pruefung waere immer "existiert" gewesen und die Funktion damit nie erreicht worden; umgekehrt haette eine invertierte Pruefung bei jedem Lauf ein zweites Konto fuer dieselbe Adresse angelegt (Account 1, Account 2, ...).
- **Fix:** Die Pruefung sucht die Mailadresse in der Ausgabe von `mail:account:export` (`... | grep "${email}" >/dev/null`, ohne `-q` wegen der SIGPIPE-Regel des Repos), mit einem Kommentar, der den Exit-Code-Befund festhaelt.
- **Files modified:** `scripts/bootstrap_exapp.sh`
- **Verification:** Zweiter Bootstrap-Lauf meldet "mail account alice: exists" und legt nichts an; `occ mail:account:export alice` zeigt genau ein Konto
- **Committed in:** `7c21b22`

**3. [Regel 2 - Fehlende Kritikalitaet] IMAP-Passwort als benannte Variable plus WR-06-Begruendung**

- **Found during:** Task 1
- **Issue:** `occ mail:account:create-imap` nimmt das IMAP-Passwort nur als positionales Argument und hat keine stdin-Form. Das Repo verbietet mit WR-06 jedes Geheimnis auf einer Kommandozeile, und ein hart eingetipptes Passwort ohne ein Wort dazu haette diese Regel stillschweigend gebrochen.
- **Fix:** `ALICE_IMAP_PASSWORD` steht als benannte, ueber `NC_EXAPP_ALICE_IMAP_PASSWORD` ueberschreibbare Variable neben den anderen Testpasswoertern, und ein Kommentarblock haelt fest, warum dieser Wert keine Autoritaet traegt: er gehoert zu einem Konto auf einem Host, den kein Resolver je beantwortet, und verlaesst diese Wegwerf-Topologie nicht.
- **Files modified:** `scripts/bootstrap_exapp.sh`
- **Verification:** `uv run pytest tests/unit/test_exapp_env_setup.py -q` gruen (146 Tests), inklusive `test_no_secret_travels_through_the_process_list` und `test_no_grep_q_on_a_pipe_in_the_shell_scripts`
- **Committed in:** `7c21b22`

**4. [Regel 1 - Bug] `httpx.BasicAuth` aus dem Docstring entfernt**

- **Found during:** Task 2
- **Issue:** Das Abnahmekriterium verlangt `grep -c "BasicAuth" == 0`. Der aus dem DAV-Spike woertlich uebernommene Docstring-Satz enthaelt genau diese Zeichenkette ("There is no `httpx.BasicAuth` anywhere in this file") und haette das Gate rot gemacht, obwohl die Aussage stimmt.
- **Fix:** Der Satz sagt dasselbe ohne die verbotene Zeichenkette und benennt zusaetzlich, dass die Schreibweise selbst nicht vorkommt.
- **Files modified:** `tests/integration/test_exapp_mail_reach.py`
- **Verification:** `grep -c "BasicAuth" tests/integration/test_exapp_mail_reach.py` ist 0
- **Committed in:** `07861ba`

**5. [Regel 3 - Blockierend] Bootstrap braucht `HP_SHARED_KEY` im Environment**

- **Found during:** Task 1
- **Issue:** `bash scripts/bootstrap_exapp.sh` ohne geladenes `.env.exapp` scheitert nicht am Skript, sondern an der Compose-Interpolation (`required variable HP_SHARED_KEY is missing a value`), und das aeussert sich als 60 Runden "waiting for the Nextcloud installation to finish" plus Abbruch. Das ist keine Aenderung am Skript wert, aber es ist die Reihenfolge, in der das Kommando laeuft.
- **Fix:** Der Lauf wird mit `set -a && . ./.env.exapp && set +a` davor ausgefuehrt, so wie es der Reproduktionsblock in `docs/spike-mail.md` und der Modul-Docstring des Tests jetzt beide auffuehren.
- **Files modified:** keine (Aufrufreihenfolge, dokumentiert)
- **Verification:** Zwei Laeufe mit Exit-Code 0
- **Committed in:** dokumentiert in `45df7c1`

---

**Total deviations:** 5 auto-behoben (2 blockierend, 2 Bugs, 1 fehlende Kritikalitaet)
**Impact on plan:** Alle fuenf betreffen die Ausfuehrbarkeit, nicht den Umfang. Die drei Artefakte, die der Plan verlangt, sind unveraendert im Umfang; `compose.exapp.yml` bleibt wie vorgesehen unangetastet, weil alle vier Messzeilen eindeutig sind. Kein Scope Creep.

## Issues Encountered

Keine offenen. Die drei Ueberraschungen waehrend der Ausfuehrung (Exit-Code von `mail:account:export`, Reihenfolge des Kontoaufrufs, Compose-Interpolation) sind oben als Abweichungen dokumentiert und behoben.

## Verification

| Prueffung | Ergebnis |
|-----------|----------|
| `bash scripts/bootstrap_exapp.sh` zweimal hintereinander | Exit-Code 0, zweiter Lauf meldet "app tables: enabled", "app mail: enabled", "mail account alice: exists" |
| `occ app:list` nennt `mail` und `tables` als enabled | mail 5.11.1, tables 2.2.2, beide im Abschnitt Enabled |
| `uv run pytest tests/integration/test_exapp_mail_reach.py -m integration -q` | 7 passed, kein Skip |
| `uv run ruff check .` und `uv run ruff format --check .` | All checks passed, 175 files already formatted |
| `uv run pytest -q` (Default-Auswahl) | gruen, kein Produktionscode geaendert |
| `docs/spike-mail.md`: vier Messzeilen, Decision, beide Kontrollen, Ersetzbarkeits-Hinweis | vorhanden; kein Em-Dash, kein En-Dash, verbotenes Vokabular nicht enthalten |
| `bash -n` fuer beide Bootstrap-Skripte | ohne Syntaxfehler |

## Known Stubs

Keine. Dieser Plan liefert eine Messung und ihr Protokoll, keinen Produktionscode; es gibt keinen Datenpfad, der noch verdrahtet werden muesste.

## Threat Flags

Keine neue Sicherheitsflaeche ausserhalb des Threat Models des Plans. `ensure_mail_account` legt per `occ` ein Konto in der lokalen Wegwerf-Topologie an (T-08-04, mitigiert durch die Idempotenz und die gefangene Kommandoausgabe), und der einzige neue Wert im Repository ist das IMAP-Passwort eines Kontos auf einem nicht existierenden Host (siehe Abweichung 3).

## User Setup Required

Keine. Es ist kein externer Dienst und kein Schluessel zu konfigurieren; die Topologie richtet sich per Bootstrap selbst ein.

## Next Phase Readiness

- MAIL-04 ist abgehakt, damit ist die blockierende Unbekannte des Meilensteins v1.2 vom Tisch und Phase 10 kann mit dem Schnitt geplant werden, den die Roadmap vorsieht.
- Offene Uebergabe an Phase 10, ausdruecklich und nicht still: der Ersetzbarkeits-Hinweis (`SCOPE_IGNORE`, Ausweg Suchprovider `mail` plus OCS-Volltextroute) gehoert ein zweites Mal in den Modul-Docstring von `src/mcp_connector/nextcloud/clients/mail.py`, und Stufe 2 des Spikes (GreenMail, echte Envelope- und Volltextformen) ist der benannte, ausgeklammerte Folgeschritt, wenn Phase 10 Feldformen braucht statt sie anzunehmen.
- Die naechsten Plaene dieser Phase (Tables) koennen sofort starten: `tables` 2.2.2 ist in beiden Topologien installiert, und Tables haengt an diesem Spike nicht.

## Self-Check: PASSED

- `tests/integration/test_exapp_mail_reach.py` vorhanden (345 Zeilen, min_lines 120 erfuellt)
- `docs/spike-mail.md` vorhanden (177 Zeilen, min_lines 60 erfuellt)
- Commits `7c21b22`, `07861ba`, `45df7c1` in `git log --all` gefunden
- Alle Abnahmekriterien der drei Tasks nachgerechnet (siehe Abschnitt Verification)

---
*Phase: 08-erreichbarkeits-spike-und-tables*
*Completed: 2026-08-21*
