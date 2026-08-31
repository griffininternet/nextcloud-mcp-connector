# Phase 19: Live-Messung gegen eine echte Nextcloud (Release-Gate EXAPP-12)

**Gemessen:** 2026-08-31 abends, lokale Topologie `compose.exapp.yml`
(Nextcloud 34.0.3, AppAPI/HaRP, lokale Registry), Windows 11 / Docker 29.5.2.
**Anlass:** 19-VERIFICATION.md führte drei Punkte als hergeleitet, weil keine
laufende Instanz vorlag. Alle drei sind jetzt gemessen. Damit ist das
Release-Gate für 0.1.12 (EXAPP-12) erfüllt.

## Ergebnis der Owner-Schrittliste (19-09-SUMMARY, 9 Schritte)

| Schritt | Ergebnis |
|---------|----------|
| 1+2 `app_api:app:disable` / `enable` Zyklus | bestanden, Kommandos überleben den Zyklus |
| 3 `occ list` zeigt drei Kommandos | bestanden: `audit:read`, `audit:verify`, `purge` mit vollem Beschreibungstext |
| 4 Optionskollision | keine: `--user/--since/--limit/--json` kollidieren mit keiner globalen occ-Option; `--help` rendert alle vier Optionstexte |
| 5 `audit:read` ohne Option | bestanden, korrekt leer bei Schalter aus, Deckelzeile "at most 200 per read" |
| 6 `--user alice --limit 5` | bestanden, "at most 5 per read" |
| 7 `--since 7` | bestanden |
| 8 `--json` | bestanden, `{"read":true,"count":0,"limit_applied":200,"truncated":false,...}` |
| 9 `audit:verify` | bestanden, "no break found" |

## Vollkette mit eingeschaltetem Schalter

- Schalter über `occ app_api:app:config:set mcp_connector audit_log --value yes`
  gesetzt (der occ-Weg zum Admin-Formularfeld), ExApp neu gestartet.
- Danach die vier Integrationstest-Dateien des CI-Jobs `exapp` lokal gefahren
  (DAV-Matrix, Permission-Fidelity, OAuth-Vollfluss mit echten Tool-Calls,
  AppAPI-Nutzerliste/A1): Exit 0.
- `occ mcp_connector:audit:read --limit 10`: **30 echte Einträge in 3 Ketten**
  (u:alice, u:bob, Instanz), je Zeile seq, Zeit, Konto, Werkzeug, Client-Name
  ("OAuth flow check"), Status ok/rejected mit eingefrorener Kennung
  (`unknown_id`), Dauer ms, Parameternamen (`path`, `query`), NIE Werte.
- `occ mcp_connector:audit:verify`: "checked 3 chains with 30 entries,
  no break found".
- Admin-Oberfläche visuell geprüft (Settings > Security): Checkbox "Keep a
  record of tool calls" mit der vollen Beschriftung aus 19-02 inkl.
  Mitbestimmungshinweis sichtbar. Screenshot:
  `audit-log-admin-field-live.png` (dieses Verzeichnis).

## Zwei Funde für das Release-Runbook 0.1.12

1. **Image-Push allein deployt nicht.** `bootstrap_exapp.sh` baute und pushte
   das frische Image, aber Registrierung und Enable waren idempotente No-Ops:
   der Container lief mit dem Stand vom 29.08. weiter und `occ list` zeigte
   nur `purge`. Erst `occ app_api:app:unregister mcp_connector` plus erneuter
   Bootstrap deployte den neuen Stand. Für Store-Updates gilt der normale
   Update-Pfad, aber jede lokale Nachmessung braucht Unregister+Register.
2. **`HP_SHARED_KEY` muss exportiert sein.** Jeder `docker compose`-Aufruf auf
   `compose.exapp.yml` (auch `exec`) verlangt die Variable; die Warteschleife
   von `bootstrap_exapp.sh` verschluckt den Interpolationsfehler mit
   `2>/dev/null` und meldet stattdessen "not installed". Export aus
   `.env.exapp`: `export HP_SHARED_KEY=$(tr -d '\r' < .env.exapp | sed -n 's/^HP_SHARED_KEY=//p' | head -1)`.

## Kleiner Textbefund (kein Blocker, Kandidat fuer den 0.1.12-Feinschliff)

Der Einleitungsabsatz des Admin-Formulars zählt noch "The first five fields
are about connecting an assistant app; the last one is not, it decides
whether an assistant may send a Talk message" und ignoriert das siebte Feld
(Audit-Schalter). Die Feldbeschriftung selbst ist korrekt und vollständig;
nur die Zählung im Intro ist seit Phase 18 veraltet.
