---
phase: 09-talk
slug: talk
status: verified
threats_open: 0
asvs_level: 1
created: 2026-08-21
---

# Phase 9 , Security

> Sicherheitsvertrag dieser Phase: Bedrohungsregister, akzeptierte Risiken, Prüfprotokoll.
> Geprüfter Stand: HEAD (`f4756bc`), also nach den Review-Fixes bis `0f2603d`.
> Grundhaltung dieser Prüfung: jede Minderung gilt als abwesend, bis eine Fundstelle im
> Implementierungsstand sie belegt. Doku und Absicht allein sind kein Beweis.
> Register aufgebaut aus den fünf `<threat_model>`-Blöcken von `09-01-PLAN.md` bis
> `09-05-PLAN.md`.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Modelleingabe zu URL-Pfad (Plan 01) | Ein Konversations-Token aus einer Modellantwort wird Teil eines URL-Pfads | Pfadsegment, Query-Parameter |
| Talk-Instanz zu Serverzustand (Plan 01) | Ein Lesevorgang dieser API schreibt per Voreinstellung in den Zustand des Nutzers | Lesemarker, Benachrichtigungs-Quittung, Online-Status |
| Nextcloud-Antwort zu Parser (Plan 01) | Statuscode und Header sind Nutzlast dieser Familie, nicht nur Transport | 201, 304, `X-Chat-Last-Given` |
| Nextcloud-Admin-Formular zu ExApp (Plan 02) | Der Schalterwert kommt über HTTP aus Nextcloud in diesen Prozess | Checkbox-Wert `on`/`off` |
| Prozessumgebung zu Werkzeug (Plan 02) | `os.environ` ist ab dem Start die einzige Quelle des Sendeschalters | Ein Schlüssel: `NC_MCP_TALK_SEND` |
| Manifest zu Deploy-Daemon (Plan 02) | Eine nicht deklarierte Variable verwirft AppAPI wortlos | Variablendeklaration in `appinfo/info.xml` |
| Modellantwort zu Sendeweg (Plan 03) | Token und Nachrichtentext aus einer Modellantwort erzeugen einen für Dritte sichtbaren Schreibvorgang | Nachrichtentext, Token |
| Fremder Chattext zu Modellkontext (Plan 03) | Jeder Teilnehmer einer Konversation kann Text schreiben, den das Werkzeug in den Modellkontext legt | Nachrichtentexte, Anzeigenamen, `messageParameters` |
| Administrator zu Werkzeug (Plan 03) | Der instanzweite Schalter ist eine administrative Grenze vor dem ersten Request | Schalterzustand |
| Registry zu MCP-Client (Plan 04) | `tools/list` ist die gecachte Zusage samt Annotationen und Schemata | Werkzeugnamen, Hints, Schemagrösse |
| Quellcode zu Destruktiv-Gate (Plan 04) | Einzige Instanz, die eine neue schreibende Talk-Route bemerkt | Quelltextzeilen |
| Store-Text zu Administrator (Plan 04) | Die Store-Beschreibung ist eine Sicherheitsaussage vor der Installation | Beschreibungstext EN/DE/FR |
| Konto zu Konto (Plan 05) | Zwei Nextcloud-Nutzer auf derselben Instanz, deren Trennung die Kernzusage ist | Konversationsinhalte, Nachrichtenzahlen |
| Lesevorgang zu Nutzerzustand (Plan 05) | Die gemessene Grenze dieser Phase: ein Lesevorgang darf nichts hinterlassen | `lastReadMessage`, `unreadMessages`, `unreadMention`, `lastCommonReadMessage` |
| Testgerüst zu Produktionscode (Plan 05) | Konversationen entstehen per `occ`, weil ein Raum keine Fähigkeit dieses Servers ist | Gerüst-Requests, klar markiert |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-09-01 | Tampering | Voreinstellungen der Leseroute, `get_messages` | mitigate | `READ_ONLY_PARAMS` ist Modulkonstante mit allen vier Werten (`nextcloud/clients/talk.py:84-89`), im Request ausgerollt (Z. 174), kein Tool-Parameter. Positiv behauptet an der gebauten URL: `tests/unit/test_talk_client.py:97` (alle vier Parameter) und `:428` (Inhalt der Konstante). Live gemessen: `tests/integration/test_talk_roundtrip.py:401` | closed |
| T-09-02 | Spoofing | `_path_token`, Token aus einer Modellantwort | mitigate | `_TOKEN = re.compile(r"[a-z0-9]{4,30}")` (Z. 97), `fullmatch` vor jedem Pfadbau mit `ToolError` (Z. 217-235), aufgerufen an beiden Id-tragenden Eingängen: `get_messages` (Z. 167) und `send_message` (Z. 207). Null Requests im Ablehnungsfall: `tests/unit/test_talk_client.py:352` parametrisiert über vier Fälle (`ABC`, `abc`, `ab-cd`, 31 Zeichen), `assert len(route.calls) == 0` (Z. 367), plus Sendepfad `:372` (Z. 381) | closed |
| T-09-03 | Elevation of Privilege | Pfadformen des Talk-Clients | mitigate | Nur drei Pfadformen im Modul: `ROOM_PREFIX` (Z. 51, verwendet Z. 131), `CHAT_PREFIX` (Z. 56, verwendet Z. 172 und 211), `TALK_WEB_PREFIX` (Z. 60). Quelltext-Behauptung über elf verbotene Zeichenfolgen inklusive `"silent"`: `tests/unit/test_talk_client.py:392-415`. Kein `/room/{token}`-Einzelaufruf im ganzen `src` (`grep ROOM_PREFIX` trifft nur Z. 51 und 131) | closed |
| T-09-04 | Information Disclosure (SSRF) | `web_url` | mitigate | `web_url` baut immer aus `creds.base_url` (`nextcloud/clients/talk.py:102-104`); keine Adresse stammt aus einer Antwort. Test `tests/unit/test_talk_client.py:385`. Konsument: `tools/talk.py:239,342` | closed |
| T-09-05 | Repudiation | 201 im Erfolgsraum von `parse_ocs` | mitigate | `_OK_STATUS = frozenset({100, 200, 201})` mit Begründungskommentar über fünf Zeilen (`nextcloud/clients/ocs.py:48-57`). Unit-Test auf die geordnete Menge (`tests/unit/test_ocs_capabilities.py`, Form `sorted(...) == [100, 200, 201]`) und auf den Sendeweg (`tests/unit/test_talk_client.py:280`). Keine bestehende Prüfung umgedreht: `uv run pytest tests/contract tests/unit/test_talk_client.py tests/unit/test_talk_tools.py tests/unit/test_exapp_env_setup.py tests/unit/test_config.py -q` im Audit grün (356 Tests) | closed |
| T-09-06 | Denial of Service | Verlaufsfenster ohne Grenze | mitigate | `MAX_MESSAGES = 50` (Z. 65), `limit` ist Keyword ohne Default (Signaturtest `tests/unit/test_talk_client.py:417`), Kappung `min(max(int(limit), 1), MAX_MESSAGES)` im Client (Z. 168), zusätzlich im Tool `min(max(limit, 1), MAX_LIMIT)` (`tools/talk.py:126`). Behauptung an der URL: `tests/unit/test_talk_client.py:124` und `:139`, Cursor unter Null wird Null `:153` | closed |
| T-09-07 | Tampering | Retry auf dem Sendeweg | mitigate | Kein Retry in irgendeiner Schicht: Kette `reg_talk.talk_send` zu `tools.talk.send` (Z. 222) zu `clients.talk.send_message` (Z. 208) zu `ocs.ocs_post`, je ein `await`, keine Schleife; `grep -rn "retry"` in `src/mcp_connector` trifft ausschliesslich Docstrings mit der Aussage "one attempt, no retry". Timeout-Satz im Docstring `clients/talk.py:203-205` und `tools/talk.py:172-175`. Antwort trägt die Nachrichten-Id (`tools/talk.py:235`) | closed |
| T-09-08 | Information Disclosure | 304 als Konfigurationsfehler gemeldet | accept | Dokumentiert als AR-01. Faktisch geprüft: `_check_transport` ist unverändert und macht aus jedem 3xx eine Redirect-Meldung (`nextcloud/clients/ocs.py:203-208`); die 304 wird lokal an der einen Route abgefangen, vor `parse_ocs` (`clients/talk.py:179-180`). Tests `tests/unit/test_talk_client.py:167` (304 als leerer Erfolg, `parse_ocs` per monkeypatch als nie erreicht behauptet) und `:190` | closed |
| T-09-10 | Tampering | Wert aus dem Admin-Formular | mitigate | `_switch` lässt nur `SWITCH_ON`/`SWITCH_OFF` heraus und lehnt alles andere ab (`exapp/config_values.py:396-413`); `talk_send` steht in der Schalter-Menge (Z. 134) und in `KEY_TO_ENV` (Z. 127). Die Logzeile nennt Feldname und Grund, nie den Wert (`_rejected`, Z. 416-423, Kommentar "never the value: it came in over HTTP"). Tests `tests/unit/test_exapp_config_values.py:719,738,749` | closed |
| T-09-11 | Elevation of Privilege | Leseweg des Schalters | mitigate | Weg A umgesetzt: Auflösung beim Start (`entry_exapp.py:302`), genau ein Schlüssel zurück in die Prozessumgebung (Z. 322-323), Lesen pro Aufruf aus `os.environ` (`config.py:346-348`). Weg C ausdrücklich verworfen, mit Begründung "a header is settable from outside" (`entry_exapp.py:304-321`). Gegenprobe: `grep -rn "TALK_SEND" src` findet keinen Header- oder `ctx`-Leseweg | closed |
| T-09-12 | Tampering | Neuer Modulzustand | mitigate | Kein Policy-Modul mit Setter, kein Prozess-Cache; `ALLOWED_MODULE_STATE` trägt weiterhin genau zwei namentlich gelistete Einträge (`tests/contract/test_no_destructive_calls.py:199-202`), Gate über alle Quelldateien (Z. 494-504). Genau eine Schreibstelle auf `os.environ`, per Quelltextbehauptung fixiert: `tests/unit/test_exapp_entry.py:1459-1469` (`assert writes == ["os.environ[config.ENV_TALK_SEND] ="]`) | closed |
| T-09-13 | Denial of Service | Unverständlicher Wert schaltet still ab | mitigate | `talk_send_enabled` prüft `value not in _FALSE_VALUES` (`config.py:348`, `_FALSE_VALUES` Z. 78), mit Begründung im Docstring, warum hier nicht die Positivmenge geprüft wird (Z. 336-345). Tests `tests/unit/test_config.py:282` (wahr), `:287,:293` (falsch), `:306` (leer bleibt an), `:317` (Tippfehler bleibt an) | closed |
| T-09-14 | Information Disclosure | `sensitive`-Flag am neuen Feld | mitigate | Das Feld `talk_send` trägt nur `id`, `title`, `description`, `type: checkbox`, `default: True` (`exapp/admin_settings.py:161-172`), kein `sensitive` in irgendeiner Schreibweise; `grep -n sensitive` in der Datei trifft nur den Modul-Docstring (Z. 18). Gehalten von `tests/unit/test_exapp_admin_settings.py:167` (kein `sensitive` im Körper) und `:255` (`assert "sensitive" not in json.dumps(talk_send).lower()`) | closed |
| T-09-15 | Repudiation | Nicht deklarierte Umgebungsvariable | mitigate | Sechster `<variable>`-Block ohne `<default>`-Element (`appinfo/info.xml:385-388`, `grep -c "<name>NC_MCP" = 6`). Mengengleichheit des bestehenden Gates um `config.ENV_TALK_SEND` erweitert (`tests/unit/test_exapp_env_setup.py:1932-1939`), Default-Verbot `:1910-1912` mit Gegenprobe `:1969` | closed |
| T-09-16 | Repudiation | Aktivierungszyklus unausgesprochen | accept | Dokumentiert als AR-02. Faktisch an drei Stellen benannt: Feldbeschreibung (`exapp/ui/strings.py:632-636`, "takes effect after you disable and enable this app again"), `docs/oauth-setup.md:120-126` und Fehlersatz des Werkzeugs (`tools/talk.py:180-185`) | closed |
| T-09-20 | Information Disclosure | `send`, Ausgangskanal in fremde Hände | mitigate | `config.talk_send_enabled()` ist die erste Zeile von `send`, vor `require_app` (Z. 188) und vor jedem Client-Aufruf (`tools/talk.py:177-186`); Begründung der umgekehrten Prüfreihenfolge im Modul- und Funktions-Docstring (Z. 22-25, 142-145). Null HTTP-Aufrufe im Aus-Zustand: `tests/unit/test_talk_tools.py:818`, Reihenfolge belegt `:867`, Standardzustand `:886` | closed |
| T-09-21 | Spoofing | Adressierung mit erfundenem Token | mitigate | `_room` sucht den Token in der eigenen Konversationsliste (`tools/talk.py:509-530`) und wird auf beiden Wegen benutzt: Sendepfad Z. 216 und Lesepfad Z. 403. `GET /room/{token}` existiert nirgends (siehe T-09-03). Tests `tests/unit/test_talk_tools.py:799` und `:1074`; live `tests/integration/test_talk_roundtrip.py:509` (erfundener Token in keiner ausgehenden URL, Konversationsliste dennoch abgefragt) | closed |
| T-09-22 | Elevation of Privilege | Vorprüfung am falschen Feld | mitigate | `_may_send` liest `room.get("permissions")` (`tools/talk.py:565`), dazu `readOnly` (Z. 561) und Typ 4 (Z. 563); `attendeePermissions` steht nur im Warnkommentar (Z. 533-542). Regressionsfall `permissions=128` bei `attendeePermissions=0` sendet erfolgreich: `tests/unit/test_talk_tools.py:926-945`; Fixture-Fälle in `tests/fixtures/talk_rooms.json` (u. a. Z. 14-15, 333-334); Note-to-self nicht mitgesperrt `:950`; Ablehnung vor dem POST `:975` | closed |
| T-09-23 | Denial of Service | Sammel-Erwähnung als Verstärker | mitigate | `_MENTION_ALL = re.compile(r"@\"?(all\|here)\"?(?![\w-])", re.IGNORECASE)` (`tools/talk.py:113`), geprüft vor jedem Lesen und Senden (Z. 200-209), `mentionPermissions` im Fehlersatz (Z. 206) und im Listeneintrag (Z. 347-348). Tests `tests/unit/test_talk_tools.py:1003` (abgelehnt, bevor etwas gelesen wird) und `:1022` (`@allan` bleibt erlaubt), `:434` (Konversation mit Moderator-Erwähnungsrecht sagt es). Restrisiko zu Gruppen- und Team-Erwähnungen siehe R-1 | closed |
| T-09-24 | Tampering (Prompt Injection) | Fremder Chattext im Modellkontext | mitigate | `marks.without_marks` auf jedem Nachrichtentext (`_resolve`, `tools/talk.py:483`), auf jedem Anzeigenamen und Aktornamen (`_text`, Z. 570-577, genutzt Z. 217, 334, 412, 443) und über `_resolve` auf jedem Namen aus `messageParameters` (Z. 474-483). Kappungsmarkierung als Feld ausserhalb des Textes (Z. 446-447 und Z. 496-506, Begründung ME-03 Z. 435-437). Systemnachrichten fallen über die Positivliste `KEPT_TYPES` weg (Z. 80, `_is_kept` Z. 422-424). Tests `tests/unit/test_talk_tools.py:370,725,748,665,592,706,1138` | closed |
| T-09-25 | Tampering | Doppelte Nachricht | mitigate | Kein Retry (siehe T-09-07); die Antwort trägt `id`, `token`, `conversation`, `timestamp` und `url` (`tools/talk.py:233-240`), eine Antwort ohne Id wird gemeldet statt erfunden (Z. 224-231, Test `tests/unit/test_talk_tools.py:1091`). Erfolgsantwort geprüft `:903`, live `tests/integration/test_talk_roundtrip.py:437` | closed |
| T-09-26 | Denial of Service | Antwortgrösse | mitigate | Drei benannte Konstanten: `MAX_LIMIT = 50` (`tools/talk.py:53`), `MAX_CONVERSATIONS = 50` (Z. 58), `MAX_MESSAGE_BYTES = 800` (Z. 65). Kappung im Envelope benannt statt still (`_envelope` Z. 591-597, `truncated` Z. 596, `total` bei der Konversationsliste Z. 304-305, Byte-Cut `_capped` Z. 495-506). Tests `tests/unit/test_talk_tools.py:342,397,487,665,1129` | closed |
| T-09-27 | Repudiation | Ungelesen-Zähler als Nachrichtenzahl | accept | Dokumentiert als AR-03. Faktisch geprüft: der Wert wird durchgereicht (`tools/talk.py:336`) und im Docstring ausdrücklich als Zähler der App und nicht als exakte Nachrichtenzahl benannt (Z. 321-325); live gemessen `tests/integration/test_talk_roundtrip.py:397` | closed |
| T-09-30 | Tampering | Neue Talk-Schreibroute im Client | mitigate | Zehn `FORBIDDEN`-Nadeln auf Pfadsegmenten (`tests/contract/test_no_destructive_calls.py:78-88`: `/schedule`, `/summarize`, `/reminder`, `/pin`, `/attachment`, `/read`, `/favorite`, `/notify`, `/participants`, `/archive`; `/share` deckt die Anhangsroute, Begründung Z. 61-63), jede mit eigener Gegenprobe in `TALK_ROUTES` (Z. 108-119), parametrisiert geprüft Z. 408, Vollständigkeit der zehn Gegenproben behauptet Z. 431-438. Positive Behauptung `ALLOWED_TALK_ROUTES` über genau drei Pfadformen (Z. 126-130, geprüft Z. 440-449), weil PUT hier kein verbotenes Verb ist (Begründung Z. 51-59) | closed |
| T-09-31 | Elevation of Privilege | Geplanter Versand als Umgehung des Admin-Schalters | mitigate | Eigene Nadel `"/schedule"` mit dem Grund "walks around the administrative switch of TALK-04" (`tests/contract/test_no_destructive_calls.py:78-79`) und eigener Gegenprobe (Z. 109) | closed |
| T-09-32 | Information Disclosure | `/summarize` schickt Inhalt an einen KI-Anbieter der Instanz | mitigate | Eigene Nadel `"/summarize"` (`tests/contract/test_no_destructive_calls.py:80`) mit eigener Gegenprobe (Z. 110); kein Chatinhalt verlässt diesen Server an einen dritten Dienst | closed |
| T-09-33 | Repudiation | Annotationen von `talk_send` | mitigate | `CREATE_ONLY` mit `read_only_hint=False`, `destructive_hint=False`, `idempotent_hint=False`, `open_world_hint=False` (`server/__init__.py:55-60`), gesetzt an `talk_send` (`server/reg_talk.py:59`), `READ_ONLY` an `talk_browse` (Z. 27). Über `tools/list` behauptet: `tests/contract/test_tool_surface.py:326` (browse nur lesend), `:340-342` (die drei Hints von `talk_send`), `:356-358` (verbotene Nachbarnamen) | closed |
| T-09-34 | Denial of Service | Grösse von `tools/list` | mitigate | `MAX_TOOL_BYTES` steht unverändert bei 1400 (`scripts/check_tool_budget.py:47`, Prüfung Z. 73-79). Messlauf im Audit: `uv run python scripts/check_tool_budget.py` endet mit Exit-Code 0, "tools/list: 14312 bytes, 20 tools, budget 15000", grösstes Werkzeug 1351 Bytes, `talk_browse` 861 Bytes. Kein angehobener Deckel | closed |
| T-09-35 | Tampering | Modulweiter veränderlicher Zustand in den neuen Modulen | mitigate | `ALLOWED_MODULE_STATE` bleibt bei genau zwei namentlich gelisteten Einträgen (`tests/contract/test_no_destructive_calls.py:199-202`); das Gate liest alle Dateien unter `src` (`_source_files` Z. 214-217, Prüfung Z. 494-504) und ist im Audit grün, also tragen `clients/talk.py`, `tools/talk.py` und `server/reg_talk.py` keinen Modulzustand | closed |
| T-09-36 | Information Disclosure | Store-Beschreibung nimmt SEC-01 vorweg | accept | Dokumentiert als AR-04. Faktisch geprüft: die Store-Beschreibung nennt in allen drei Sprachen nur den Ausgangskanal und den Schalter (`appinfo/info.xml:29,42,55`), keine Exfiltrationskette | closed |
| T-09-37 | Repudiation | Datierte Doku-Messwerte alter Läufe | accept | Dokumentiert als AR-05. Der bestehende Wächter erzwingt je Zahl Aktualität oder den Zeiger auf den Contract-Test (`tests/contract/test_tool_surface.py:616`); im Review als WR-01 nachgezogen (`docs/client-setup.md`, Commit `9d67b36`), die datierte Messzeile durfte stehenbleiben | closed |
| T-09-40 | Elevation of Privilege | Zugriff auf eine fremde Konversation | mitigate | Zwei-Konten-Negativbeweis auf der Impersonation-Naht (`tests/integration/test_permission_fidelity_exapp.py:630-679`): beide Ablehnungen mit Hinweis, echter Token in der Negativhälfte, Nachrichtenzahl von alice vor und nach dem Versuch gleich (Z. 665-669) und der fremde Inhalt in keiner Nachricht (Z. 670-672). Positivkontrollen im selben Lauf: Z. 592 (alice liest ihre eigene Konversation) und Z. 616 (bob sieht sie nicht in seiner Liste). Beobachtete Statuscodes werden gemessen, nicht erwartet (Z. 657-663) | closed |
| T-09-41 | Tampering | Lesen, das den sichtbaren Lesestand ändert | mitigate | `STATE_FIELDS = ("lastReadMessage", "unreadMessages", "unreadMention", "lastCommonReadMessage")` (`tests/integration/test_talk_roundtrip.py:72`), Vorher-Nachher-Messung mit vier eigenen Behauptungen (Z. 313-357). Konstruktive Seite: `READ_ONLY_PARAMS` (T-09-01), live an der URL geprüft Z. 401 | closed |
| T-09-42 | Denial of Service | Brute-Force-Zähler durch geratene Tokens | mitigate | `tests/integration/test_talk_roundtrip.py:509-545`: der erfundene Token erscheint in keiner ausgehenden URL (Z. 538), die Ablehnung ist unser eigener Satz (Z. 536), und die Konversationsliste wurde stattdessen gelesen (Z. 541). Der Docstring sagt ausdrücklich, dass der Wächter auf dieser Topologie abgeschaltet ist und die Regel deshalb im Code stehen muss (Z. 514-519). Unit-Ebene: `tests/unit/test_talk_tools.py:1074`, Client-Ebene `tests/unit/test_talk_client.py:352` | closed |
| T-09-43 | Repudiation | Zustand außerhalb von git | mitigate | Testkonversationen entstehen idempotent nach Namen im Bootstrap (`scripts/bootstrap_test_nc.sh:184-198,275-276`; `scripts/bootstrap_exapp.sh:588-602,1006-1007`). Der Testlauf stellt fest statt anzunehmen: App (`test_talk_roundtrip.py:235`, Skip mit Grund), Gerüst (`:274`) und Schalterzustand (`:257`, beide Richtungen live plus Messzeile) | closed |
| T-09-44 | Tampering | Doppelte Testkonversationen | mitigate | Der Kommentar über `ensure_talk_room` nennt die fehlende Idempotenz von `occ talk:room:create` (`scripts/bootstrap_test_nc.sh:165-168`, `scripts/bootstrap_exapp.sh:569-572`); gesucht wird per OCS-Konversationsliste nach Namen (`bootstrap_test_nc.sh:178`, `bootstrap_exapp.sh:582`), angelegt nur, was fehlt (`:188` bzw. `:592`). Zweiter Lauf belegt in `09-05-SUMMARY.md` | closed |
| T-09-45 | Information Disclosure | Testnachrichten in einer geteilten Konversation | accept | Dokumentiert als AR-06. Faktisch geprüft: die gesendeten Texte tragen Zeitstempel plus Laufkennung (`tests/integration/test_talk_roundtrip.py:77`, genutzt Z. 337, 490) und keine echten Daten; die Konversationen gehören dem Testkonto der lokalen Topologie. Der Text des Einbruchsversuchs (`test_permission_fidelity_exapp.py:503`) wird nachweislich nie gespeichert (T-09-40) | closed |
| T-09-SC | Tampering | Paketinstallation (Pläne 01 bis 04) | accept | Dokumentiert als AR-07. Faktisch geprüft: `git diff --stat 3d75bd2..HEAD -- pyproject.toml uv.lock` ist leer, kein Phasen-Commit berührt eine der beiden Dateien; kein `uv add`, kein `pip install`, kein `npm install` | closed |
| T-09-SC-05 | Tampering | Installation der Nextcloud-App `spreed` (Plan 05) | mitigate | Installation über `occ app:install` per `ensure_app spreed`, derselbe Weg wie notes, deck, tables und mail (`scripts/bootstrap_test_nc.sh:247`, `scripts/bootstrap_exapp.sh:959`, `ensure_app` Z. 80 bzw. Z. 255). Store-Audit samt Version, Plattform-Spec und gelesenem Quelltag steht in `09-RESEARCH.md`. Die installierte Version wird im Lauf gegengeprüft und als Messwert ausgegeben (`tests/integration/test_talk_roundtrip.py:235-255`, `spreed version ...` plus Feature-Zahl und `chat max-length`). Keine Sprachabhängigkeit (siehe T-09-SC). Abweichung: die Gegenprüfung liest die `spreed`-Sektion der Capabilities statt `occ app:list`; die Aussage (installierte Version) ist dieselbe, siehe R-4 | closed |

*Status: open , closed*
*Disposition: mitigate (Implementierung nötig) , accept (dokumentiertes Risiko) , transfer (Dritte)*

Keine Bedrohung dieser Phase trägt die Disposition `transfer`, deshalb war keine
Übertragungsdokumentation zu prüfen.

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-01 | T-09-08 | Der geteilte `_check_transport` bleibt unverändert und meldet jedes 3xx als Redirect. Die 304 hat nur auf der Verlaufsroute eine Bedeutung und wird dort lokal abgefangen (`nextcloud/clients/talk.py:179-180`), bevor `parse_ocs` sie sieht. Ein zweiter Sonderfall im gemeinsamen Parser wäre teurer als diese eine Zeile und würde sechs bestehende Client-Familien berühren | Planner (Plan 09-01), bestätigt im Audit | 2026-08-21 |
| AR-02 | T-09-16 | Der Aktivierungszyklus (Wirkung erst nach Deaktivieren und Aktivieren der App) wird nicht beseitigt, sondern benannt: Feldbeschreibung, `docs/oauth-setup.md` und Fehlersatz des Werkzeugs. Der Preis ist derselbe wie bei den fünf bestehenden Admin-Werten; die Alternative, den Wert pro Sendevorgang aus Nextcloud zu lesen, kostet einen Roundtrip je Nachricht und müsste bei einem Lesefehler fail-closed antworten, was dem zugesagten Standardzustand "an" widerspricht (`entry_exapp.py:315-321`) | Planner (Plan 09-02), bestätigt im Audit | 2026-08-21 |
| AR-03 | T-09-27 | Der Ungelesen-Zähler der App ist keine exakte Nachrichtenzahl (eine nie geöffnete leere Konversation meldet 1). Der Wert wird durchgereicht und im Docstring als Zähler der App benannt, statt korrigiert zu werden; eine Korrektur wäre eine zweite Wahrheit über eine fremde Zahl | Planner (Plan 09-03), bestätigt im Audit | 2026-08-21 |
| AR-04 | T-09-36 | Die Store-Beschreibung nennt den Ausgangskanal und den Schalter, nicht die Exfiltrationskette. Deren Benennung ist SEC-01 in Phase 10, weil Mail-Lesen noch nicht existiert; eine Sicherheitsaussage eine Phase zu früh wäre in der Zwischenzeit unvollständig | Planner (Plan 09-04), bestätigt im Audit | 2026-08-21 |
| AR-05 | T-09-37 | Datierte Messwerte alter Läufe dürfen in `docs/` stehenbleiben, solange die Seite auf `tests/contract/test_tool_surface.py` als aktuelle Wahrheit zeigt. Bestehende Regel des Doku-Wächters (`tests/contract/test_tool_surface.py:616`), in dieser Phase nicht neu verhandelt. Fortschreibung von AR-02 der Phase 8 | Planner (Plan 09-04), bestätigt im Audit | 2026-08-21 |
| AR-06 | T-09-45 | Die von den Integrationstests gesendeten Nachrichten tragen Zeitstempel und eine Laufkennung und keine echten Daten; die Konversationen gehören dem Testkonto der lokalen Wegwerf-Topologie. Die öffentliche Staging-Instanz ist nicht Ziel dieses Plans; ohne konfigurierte Testinstanz überspringen die Tests. Bekannte Folge: ein Lauf hinterlässt Nachrichten in der Bootstrap-Konversation, das ist in `docs/conference-demo.md` nach WR-02 ausdrücklich benannt | Planner (Plan 09-05), bestätigt im Audit | 2026-08-21 |
| AR-07 | T-09-SC | Keine neue Sprachabhängigkeit in dieser Phase: `pyproject.toml` und `uv.lock` sind über alle Phasen-9-Commits unberührt (im Audit per `git diff --stat 3d75bd2..HEAD` geprüft). Die eine neue Nextcloud-App (`spreed`) ist gegen ihre offizielle Quelle verifiziert und wird als T-09-SC-05 gemindert, nicht akzeptiert | Planner (Pläne 09-01 bis 09-04), bestätigt im Audit | 2026-08-21 |

*Akzeptierte Risiken tauchen in späteren Prüfläufen nicht erneut auf.*

---

## Unregistered Flags und Restrisiken

Warnungen, keine Blocker. Sie halten die Phase nicht auf (`block_on: high`), gehören aber ins
Protokoll.

| ID | Art | Befund | Bewertung |
|----|-----|--------|-----------|
| UF-1 | unregistered_flag (Prozess) | `09-01-SUMMARY.md` hat keinen Abschnitt `## Threat Flags`. Die vier anderen Zusammenfassungen melden ausdrücklich "keine neue sicherheitsrelevante Oberfläche" | Die Fläche von Plan 09-01 ist im Audit direkt am Code geprüft (T-09-01 bis T-09-08 alle closed), es fehlt also die Meldung und nicht die Minderung. Gleiche Beobachtung wie UF-1 der Phase 8; für kommende Phasen den Abschnitt in jeder Zusammenfassung erzwingen |
| UF-2 | Threat Flag (zugeordnet) | `09-05-SUMMARY.md` meldet, dass die Gerüst-Funktion `_talk_status` absichtlich einen Einzelkonversations-Pfad mit einem echten fremden Token baut, um den Statuscode der Instanz zu messen (`tests/integration/test_permission_fidelity_exapp.py:563-590`) | Zugeordnet zu T-09-42. Die Regel gilt für den Connector, und die belegt der Test (Z. 538). Das Gerüst läuft nur auf der Wegwerf-Topologie mit abgeschaltetem Wächter, zweimal pro Lauf, ist im Docstring als Gerüst markiert und liegt in `tests/`, also nicht unter `src`. Kein Produktionspfad, keine Massnahme |
| UF-3 | Threat Flag (zugeordnet) | `09-03-SUMMARY.md` meldet eine Abweichung in Richtung mehr Schutz: die Vorprüfung über die eigene Konversationsliste wirkt jetzt auch auf dem Lesepfad (`tools/talk.py:403`) und nicht nur beim Senden | Zugeordnet zu T-09-21, verstärkt die dortige Minderung. Preis ist ein zusätzlicher Request pro Verlaufslesen, im Docstring benannt (Z. 374-380) |
| R-1 | Restrisiko zu T-09-23 | Gruppen- und Team-Erwähnungen (`@"group/<id>"`, `@"team/<id>"`) fallen nicht unter `_MENTION_ALL`. Review-Befund IN-02 ist bewusst zurückgestellt (`09-REVIEW.md:124-129`) | Die deklarierte Minderung ist wörtlich "`@all` und `@here` mit Wortgrenze", und sie ist erfüllt und getestet. Die enger gefasste Restklasse benachrichtigt eine Gruppe statt aller Teilnehmer und braucht eine eigene Aufgabe mit Owner-Entscheid samt Positiv- und Negativtests. Kein offener Threat, Kandidat für eine geplante Änderung |
| R-2 | Restrisiko zu T-09-26 | `scripts/check_tool_budget.py` misst das Gesamtbudget in Bytes, das Pro-Tool-Limit in Zeichen (Befund IN-03, zurückgestellt) | Die Minderung von T-09-34 (Deckel bleibt bei 1400, Messung vor jeder Anhebung) ist erfüllt; der Messlauf steht bei 14312 von 15000 Bytes und das grösste Werkzeug bei 1351 von 1400. Ein Werkzeug mit vielen Nicht-ASCII-Zeichen würde pro Tool unterzählt, aktuell ohne Wirkung, weil die Beschreibungen ASCII sind |
| R-3 | Restrisiko zu T-09-26 | Ein `cursor` auf `level=conversations` wird stillschweigend ignoriert (Befund IN-04) und die Längen-Vorprüfung zählt Zeichen, während Talk serverseitig möglicherweise anders zählt (Befund IN-06); beide zurückgestellt | Keine der beiden Stellen berührt eine deklarierte Minderung: die Kappung der Konversationsliste ist benannt (`truncated` plus `total`), und Talks eigene 400 bleibt der Rückhalt und wird mit eigener Meldung durchgereicht (`tests/unit/test_talk_tools.py:1110`). Redaktionell offen, sicherheitlich unauffällig |
| R-4 | Hinweis zu T-09-SC-05 | Der Plan nennt eine Gegenprüfung der installierten Talk-Version gegen `occ app:list`; der Lauf liest sie stattdessen aus der `spreed`-Sektion der Capabilities (`tests/integration/test_talk_roundtrip.py:250-255`). `occ app:list` wird im Bootstrap nur für notes und deck geprüft (`scripts/bootstrap_test_nc.sh:314`) | Die geschützte Eigenschaft, die installierte Version wird gemessen statt angenommen, ist erfüllt und erscheint als Messzeile im Lauf. Der Weg unterscheidet sich vom Plantext. Da Talk etwa monatlich veröffentlicht, bleibt die Messzeile die Stelle, an der eine Versionsdrift auffällt |

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-08-21 | 39 | 39 (32 mitigate verifiziert, 7 akzeptiert) | 0 | gsd-security-auditor |

Geprüfter Commit: `f4756bc` (nach den Review-Fixes bis `0f2603d`). ASVS-Level 1,
`block_on: high`.

Im Audit ausgeführte Gegenproben: `uv run python -m pytest tests/contract
tests/unit/test_talk_client.py tests/unit/test_talk_tools.py tests/unit/test_exapp_env_setup.py
tests/unit/test_config.py -q` (356 Tests grün), `uv run python scripts/check_tool_budget.py`
(Exit-Code 0, 14312 von 15000 Bytes, 20 Werkzeuge),
`git diff --stat 3d75bd2..HEAD -- pyproject.toml uv.lock` (leer).

Geprüfte Implementierungsdateien: `src/mcp_connector/tools/talk.py`,
`src/mcp_connector/nextcloud/clients/talk.py`, `src/mcp_connector/nextcloud/clients/ocs.py`,
`src/mcp_connector/nextcloud/capabilities.py`, `src/mcp_connector/server/reg_talk.py`,
`src/mcp_connector/server/__init__.py`, `src/mcp_connector/config.py`,
`src/mcp_connector/entry_exapp.py`, `src/mcp_connector/exapp/admin_settings.py`,
`src/mcp_connector/exapp/config_values.py`, `src/mcp_connector/exapp/ui/strings.py`,
`appinfo/info.xml`, `tests/contract/test_no_destructive_calls.py`,
`tests/contract/test_tool_surface.py`, `tests/unit/test_talk_client.py`,
`tests/unit/test_talk_tools.py`, `tests/unit/test_config.py`,
`tests/unit/test_exapp_entry.py`, `tests/unit/test_exapp_env_setup.py`,
`tests/unit/test_exapp_admin_settings.py`, `tests/unit/test_exapp_config_values.py`,
`tests/integration/test_talk_roundtrip.py`,
`tests/integration/test_permission_fidelity_exapp.py`, `tests/fixtures/talk_rooms.json`,
`scripts/bootstrap_exapp.sh`, `scripts/bootstrap_test_nc.sh`, `scripts/check_tool_budget.py`,
`docs/oauth-setup.md`.
Keine Implementierungsdatei wurde in diesem Lauf verändert.

---

## Sign-Off

- [x] Alle Bedrohungen tragen eine Disposition (mitigate / accept / transfer)
- [x] Akzeptierte Risiken im Accepted Risks Log dokumentiert (AR-01 bis AR-07)
- [x] `threats_open: 0` bestätigt
- [x] `status: verified` in der Frontmatter gesetzt

**Approval:** verified 2026-08-21
