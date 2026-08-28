# Phase 17: openDesk-Spike - Context

**Gathered:** 2026-08-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Diese Phase erzeugt Erkenntnis und einen Nachweis, keinen Produktionscode. Sie beantwortet
gemessen, ob und wie diese ExApp in einer openDesk-Umgebung installierbar ist (OD-01), stellt
Weg 0 (`integration_openproject` als Zugriffsweg) und Weg 1 (eigener OAuth-Autorisierungscode
je Nutzer gegen OpenProject) mit Messwerten nebeneinander (OD-02) und legt die Fragenliste
für den ISV-Call am 14.09. vor (OD-03).

Der ausgelieferte Produktionsbaum bleibt unverändert: kein neues Werkzeug, kein neuer Client
im Paket, Werkzeugoberfläche und Budget-Gate (15712 von 18000 Bytes) stehen still. Zulässig
sind Dateien in `docs/` und `.planning/`, weil `docs/` nicht Teil des Store-Assets ist.

</domain>

<decisions>
## Implementation Decisions

### Messumgebung und Kosten
- **D-01:** OD-01 wird ausschließlich aus Quellen belegt, ohne Kubernetes-Cluster: openDesk-Helmfile
  (`helmfile/apps/nextcloud/values-nextcloud-management.yaml.gotmpl`), AppAPI-Dokumentation zu
  Deploy-Daemons, Nextcloud-Dokumentation zu `manual_install`. Jede der drei Hürden (abgeschalteter
  App Store, keine AppAPI auf Kubernetes, Pin auf Nextcloud 33.0.7 gegen unsere Nachweise auf
  34.0.3) bekommt ein Quellenzitat oder wird ausdrücklich als offene ISV-Call-Frage markiert.
- **D-02:** OD-02 wird lokal in Docker gemessen, mit gepinnten Versionen: Nextcloud **33.0.7**
  (der openDesk-Stand, nicht 34.0.3) plus `integration_openproject`, dazu OpenProject Community
  **17.7.x**. Kein `latest`.
- **D-03:** In dieser Phase entsteht **keine gemietete Box**. Was lokal nicht messbar ist, wird im
  Bericht als "ungemessen" geführt, nie als "verworfen".

### Messtiefe Weg 1 (eigener OAuth-Fluss gegen OpenProject)
- **D-04:** Weg 1 wird mit vollem Consent-Flow gemessen, nicht nur angeklopft: OAuth-Anwendung in
  OpenProject anlegen, Autorisierungscode einmal durch den Browser holen, dann echte Werte
  festhalten: nimmt `/oauth/authorize` PKCE an, obwohl die Metadaten es nicht bewerben, welche
  `expires_in`, und trägt die Erneuerung ohne Browsersitzung.
- **D-05:** Der Negativbeweis mit **zwei Nutzerkonten** (Nutzer B sieht das Arbeitspaket von A
  nicht) ist auf **beiden** Wegen Pflicht, nicht nur auf dem gewinnenden.
- **D-06:** Die SSRF-Grenze aus v1.1 wird **gemessen**, nicht aus dem Code hergeleitet: lässt die
  Prüfung einen Nachbardienst unter internem Docker-Dienstnamen durch oder sperrt sie ihn
  fälschlich aus, mit den Fällen aus dem bestehenden Negativkatalog.

### OIDC-Bruchstelle S5 (die Stelle, an der Weg 0 kippt)
- **D-07:** S5 wird gemessen, nicht behauptet: Keycloak plus `user_oidc` kommen lokal dazu, damit
  geprüft ist, ob die serverseitige Token-Erneuerung von `integration_openproject` auch im
  OIDC-gebundenen Betrieb hält oder nach Ablauf des zwischengespeicherten Tokens auf 401 fällt.
- **D-08:** Derselbe Aufbau liefert die Live-Reproduktion für `nextcloud/user_oidc#925`. Das Issue
  geht **nur** mit geglückter Repro raus; der Entwurf liegt im Repo und **der Owner sendet**.
  Ohne Repro bleibt der Entwurf liegen (Regel aus context_agent#230).

### Ablage von Bericht, Fragenliste und Kanälen
- **D-09:** Der Spike-Bericht wird `docs/spike-opendesk.md`, nach dem Muster von `docs/spike-dav.md`,
  `docs/spike-discovery.md` und `docs/spike-mail.md`; die Rohmesswerte stehen als eigener Abschnitt
  darin. Reihenfolge im Bericht: erst Installierbarkeit, dann Auth, dann API-Form.
- **D-10:** Die ISV-Fragenliste (OD-03) wird in `Desktop/ISV-Call-Dossier-2026-09-14.md` ergänzt
  **und** als Abschnitt in den Spike-Bericht aufgenommen, damit sie versioniert ist.
- **D-11:** Zum Forumsbeitrag über die OCS-Routen: `christianlupus` hat am 28.08. geantwortet, im
  Community-Chat selbst keine Antwort erhalten und rät zu einem Konto in der OpenProject-Community.
  Die Phase erzeugt zwei **Entwürfe**: eine kurze Antwort an christianlupus im Nextcloud-Forum und
  eine Konto-Anfrage an die OpenProject-Community (Selbstregistrierung dort liefert HTTP 400
  "Registration not allowed"). Owner-Zusage 28.08.: "ich würde ein community account beantragen
  wenn es sein muss". **Gesendet wird ausschließlich vom Owner.**
- **D-12:** Auch wenn die Messung Weg 0 als tragend zeigt, entsteht in dieser Phase **kein Code**:
  kein Client-Modul, kein Werkzeug, kein Prototyp im Paketbaum. Der Weg-0-Client ist OD-04 und
  wartet auf v2.0 nach dem ISV-Call.

### Claude's Discretion
- Aufteilung der Messungen in Pläne und Wellen, Form der Docker-Compose-Dateien und wo sie liegen
  (außerhalb von `src/`), Aufbau der Messprotokolle, Reihenfolge innerhalb von OD-02, Wortwahl der
  Entwürfe.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Anforderungen und Milestone-Entscheide
- `.planning/REQUIREMENTS.md`: OD-01/02/03 im Wortlaut, die vier Owner-Entscheide D-v1.5-01..04,
  Out-of-Scope-Tabelle (kein Dienstkonto, kein eigener Keycloak-Client für OpenProject, kein
  Weiterreichen des MCP-Tokens)
- `.planning/ROADMAP.md` §Phase 17: die fünf Erfolgskriterien, insbesondere Kriterium 5
  (Produktionsbaum unverändert) und Kriterium 3 ("ungemessen" statt "verworfen")

### Der zu messende Widerspruch
- `.planning/research/SUMMARY.md` §"Der zentrale Widerspruch": Weg-0-gegen-Weg-1-Tabelle,
  Behauptungen S1-S6, Bewertung
- `.planning/research/SUMMARY.md` §"Die Gating-Frage": die drei Installierbarkeits-Befunde
- `.planning/research/ARCHITECTURE.md`: Weg 0 samt den 15 OCS-Routen von
  `integration_openproject` (keine Route für ein einzelnes Arbeitspaket, keine für Kommentare,
  keine für "meine Arbeit")
- `.planning/research/STACK.md` §A.8: die vier Fragen zu Weg 1, PKCE trotz fehlender Ankündigung
- `.planning/research/PITFALLS.md`: Pitfall 1 (Dienstkonto bricht das Versprechen unauffällig)

### Bestehende Muster im Repo
- `docs/spike-mail.md`: Formvorbild für den Bericht: Behauptung, Messweg, Messwert, Gegenprobe
- `docs/spike-dav.md`, `docs/spike-discovery.md`: dieselbe Reihe
- `docs/oauth-setup.md`: wie OAuth-Messungen hier bisher belegt wurden (CIMD-Messweg A,
  Loopback-Portregel, Gegenproben)
- `docs/privacy.md`, `docs/uninstall.md`: Aussagen, die diese Phase **nicht** anfasst (das ist
  Phase 19)

### Termin und Verhandlung
- `Desktop/ISV-Call-Dossier-2026-09-14.md`: Ziel der Fragenliste aus OD-03
- `Desktop/openDesk-Anfragen-2026-08-28.md`: die vier Anfragetexte samt Belegtabelle und
  Versandstatus (app_api-Issue #1013 raus, ZenDiS-Mail gesendet, Forumsbeitrag raus,
  user_oidc#925 zurückgehalten)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `docs/spike-*.md`: drei Vorlagen für Messprotokolle mit Behauptung, Messweg, Messwert, Gegenprobe
- SSRF-Prüfung und Negativkatalog aus v1.1 (Phase 6): existiert samt Testfällen, wird hier nur
  gegen einen neuen Fall gefahren, nicht geändert
- Docker plus WSL2 lokal vorhanden, aus früheren Phasen für Test-Nextcloud und GreenMail erprobt

### Established Patterns
- Nachweise werden wörtlich genommen: ein Nachweis auf der falschen Hauptversion gilt nicht.
  Deshalb Nextcloud 33.0.7 statt 34.0.3 in der Messumgebung
- Kein `latest` in Messumgebungen, immer gepinnte Versionen
- Externe technische Behauptungen erst nach Code-Beleg **und** Live-Repro (Lehre aus
  context_agent#230)
- `uv run pytest -q` schließt Integrations- und Matrix-Tests aus (`addopts`); Spike-Messungen
  laufen ohnehin außerhalb der Suite

### Integration Points
- Kein Eingriff in `src/`. Berührt werden nur `docs/`, `.planning/` und, für die Messumgebung,
  Dateien außerhalb des Paketbaums
- Ergebnis speist OD-04 (Werkzeug `openproject_browse`) in v2.0, nicht diese Phase

</code_context>

<specifics>
## Specific Ideas

- Der Bericht führt Weg 0 **zuerst** und mit den Behauptungen S1-S6, davon S4 (Token-Erneuerung
  ohne Browsersitzung) und S5 (Verhalten im OIDC-Modus nach Tokenablauf) als die entscheidenden
  Messungen; Weg 1 steht daneben, nicht darunter
- Ein Weg, der nicht gemessen werden konnte, steht als "ungemessen" da, mit dem Grund, warum die
  Messung nicht möglich war
- Für OD-01 gilt: der Leser erfährt die Installierbarkeit, bevor er irgendeine API-Frage liest
- Die Talk- und Kontakte-Abschaltung in openDesk betrifft zwei der neun Werkzeugfamilien und
  gehört ausdrücklich auf die ISV-Fragenliste, nicht nur in den Bericht

</specifics>

<deferred>
## Deferred Ideas

- **Weg-0-Client als Code** (`nextcloud/clients/integration_openproject.py`) und das Werkzeug
  `openproject_browse` samt `wp:<id>` für `fetch`: OD-04, v2.0, nach dem ISV-Call
- **Wegwerf-Prototyp außerhalb des Paketbaums**, der den gewinnenden Weg einmal echt durchspielt:
  vom Owner am 28.08. abgelehnt zugunsten "nur berichten"
- **k3s- oder Cloud-Installationsversuch für openDesk**: bewusst nicht in dieser Phase; wenn der
  ISV-Call einen Installationsweg nennt, wird er dort geprüft
- **Antwort auf die OCS-Frage über die OpenProject-Community**: Konto-Anfrage entsteht als Entwurf,
  der Rückkanal läuft nach dieser Phase weiter

</deferred>

---

*Phase: 17-opendesk-spike*
*Context gathered: 2026-08-28*
