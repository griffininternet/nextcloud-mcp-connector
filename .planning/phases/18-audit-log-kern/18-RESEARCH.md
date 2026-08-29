# Phase 18: Audit-Log Kern - Recherche

**Recherchiert:** 2026-08-29
**Domäne:** Erfassung im MCP-Dekorator, zweite SQLite-Ablage, Hash-Kette, occ-Kommando über AppAPI
**Confidence:** HIGH für alles, was am eigenen Code und an gemessenen Läufen hängt; MEDIUM für die Kostenzahlen (auf Windows/NTFS gemessen, nicht im Linux-Container); LOW für nichts, das die Planung trägt

---

<user_constraints>
## Nutzer-Vorgaben (aus 18-CONTEXT.md)

### Feste Entscheide

- **D-01:** Das Log liegt in einer **zweiten SQLite-Datei** neben `store.sqlite3` im selben
  Volume, mit eigener Verbindung und eigenem WAL, nach dem Muster von
  `src/mcp_connector/oauth/store.py`. Begründung: Prüfkommando, Aufbewahrung und
  Nutzerbereinigung sind damit SQL statt Dateiakrobatik. Die Trennung vom OAuth-Speicher ist
  eine Trennung der Dateien und der Verbindungen, nicht der Volumes: gegen ein volles Volume
  hilft die Obergrenze aus D-08, nicht die Dateiform. Ein eigenes Verzeichnis für getrenntes
  Einhängen wurde erwogen und verworfen (ein Pfad mehr in der Konfiguration ohne Gewinn für
  die geforderten Kriterien).
- **D-02:** **Eine Kette je Nutzer.** Die Löschung eines Nutzers in Nextcloud entfernt dann
  eine ganze Kette am Stück, ohne die Ketten der übrigen Nutzer zu brechen (D-v1.5-01
  verlangt genau diese Löschung). Der bewusst getragene Preis: das Verschwinden eines
  kompletten Nutzerstrangs fällt dem Prüfkommando nicht auf. Eine globale Kette wurde
  verworfen, weil ein regulärer Vorgang sie dauerhaft gebrochen zurückließe.
- **D-03:** Instanzereignisse (D-15) laufen in einer **eigenen zweiten Kettenart**, getrennt
  von den Nutzerketten.
- **D-04:** Erfasst wird im vorhandenen **`@graceful`-Dekorator** in
  `src/mcp_connector/server/__init__.py`, der bereits an allen 21 Werkzeugen hängt und
  Ergebnis wie Fehler sieht. "Kein Werkzeug kann daran vorbei" wird nicht behauptet, sondern
  von einem **Vertragstest** gehalten, der jedes registrierte Werkzeug gegen den Dekorator
  prüft; ein künftiges Werkzeug ohne Dekorator lässt diesen Test fehlschlagen. Eine
  Server-Middleware wurde verworfen, weil sie an dem hängt, was mcp 2.x an dieser Stelle
  anbietet, und Werkzeugnamen und Fehlerklassen ungenauer sieht.
- **D-05:** **Ein Eintrag nach dem Aufruf**, mit Ergebnisstatus und Dauer, eine Zeile je
  Aufruf. Bewusst getragen: ein Absturz mitten im Aufruf hinterlässt keinen Eintrag, der
  Aufruf bleibt unsichtbar. Start- und Ende-Paare wurden verworfen, weil sie die Zeilenzahl
  und damit den Verbrauch der Obergrenze verdoppeln.
- **D-06:** Ein Eintrag trägt: Nutzer, Werkzeugname, Zeitpunkt, aufrufenden Client,
  Ergebnisstatus, Dauer, Hash des Vorgängers und eigenen Hash. **Von den Parametern nur die
  gesetzten Namen aus einer Erlaubnisliste je Werkzeug, niemals ein Wert.** Ein Vertragstest
  nach dem Muster des Budget-Gates (`scripts/check_tool_budget.py`,
  `tests/contract/test_tool_surface.py`) schlägt fehl, sobald ein Werkzeug diese Grenze
  überschreitet. Grobe Formangaben wie Wertlängen wurden verworfen: eine Länge ist bereits
  ein schwaches Leck.
- **D-07:** Der Ergebnisstatus ist eine **Klasse** (gelungen, abgelehnt, fehlgeschlagen);
  bei einer Ablehnung kommt der Grund als **feste Kennung** dazu (fehlende Berechtigung,
  unbekannte Id, Zeitüberschreitung, Sicherung gegriffen). Kein Freitext und kein Fehlersatz
  der Werkzeugantwort, denn das wäre Ergebnisinhalt und verstieße gegen AUDIT-01.
- **D-08:** Der aufrufende Client steht als **Client-Id, Verbindungs-Id und der bei der
  Registrierung genannte Client-Name** aus dem OAuth-Speicher. **Keine IP-Adresse und kein
  User-Agent**: das machte das Log zu einem Bewegungsprofil und verschärfte die
  Mitbestimmungsfrage aus AUDIT-05 unnötig.
- **D-09:** Vorgabewerte: **Aufbewahrungsfrist 180 Tage, Obergrenze 100 MB**, beide
  einstellbar. Die Frist liegt damit genau auf der geforderten Untergrenze, die Größe
  großzügig, so dass in der Praxis die Frist greift und nicht die Größe.
- **D-10:** Ist die Obergrenze erreicht, weichen die **ältesten Einträge, und ein Grabstein**
  hält Zeitpunkt, Anzahl und Endhash fest, damit das Prüfkommando die Lücke erklären kann
  statt sie als Bruch zu melden. Ein Schreibstopp wurde verworfen: das Log verstummte genau
  dann, wenn niemand hinsieht.
- **D-11:** Abgelaufene Einträge räumt der **Schreibpfad selbst gebündelt ab** (jeder n-te
  Eintrag prüft nebenbei Frist und Obergrenze). Kein Cron, kein Hintergrunddienst, wirksam
  auch auf einer Instanz, die nie ein occ-Kommando sieht. Der Preis, dass gelegentlich ein
  Aufruf die Aufräumkosten trägt, ist bewusst getragen.
- **D-12:** Von der **Löschung eines Nutzers in Nextcloud** erfährt das Modul über denselben
  gebündelten Aufräumlauf: für Nutzer, deren letzter Eintrag älter als eine Schwelle ist,
  wird geprüft, ob das Konto noch existiert; fehlt es, fällt die ganze Kette samt Grabstein.
  Ein Weg, keine neue Route. Bewusst getragen: die Löschung verzögert sich bis zum nächsten
  Lauf. Ein Ereignisweg über AppAPI wurde nicht gewählt, weil er erst gemessen werden müsste
  und im Fehlschlag doch auf diesen Weg zurückfiele.
- **D-13:** **Fail-open mit Alarm.** Kann das Log nicht schreiben (Volume voll, Datei
  defekt), läuft der Werkzeugaufruf trotzdem; der Fehlschlag geht ins Nextcloud-Log und wird
  vom Prüfkommando als Lücke sichtbar. Nextcloud bleibt bedienbar, das Log ist dann
  nachweislich unvollständig. Fail-closed wurde verworfen: ein volles Volume legte sämtliche
  KI-Zugriffe still.
- **D-14:** Der Kern liegt **schon in dieser Phase hinter dem Schalter, ab Werk aus**, als
  Konfigurationswert nach dem Muster von `src/mcp_connector/exapp/config_values.py`. Phase 19
  hängt nur noch Bedienoberfläche und Beschriftung daran. Kein Zwischenstand, in dem ein
  nutzerbezogenes Protokoll ungefragt mitläuft.
- **D-15:** Das **Ein- und Ausschalten des Logs wird selbst protokolliert**, als eigene
  Eintragsart in der Kette der Instanzereignisse (D-03), mit Zeitpunkt, Richtung und dem
  handelnden Administrator. Sonst ließe sich das Log abschalten, handeln und wieder
  einschalten, ohne dass die Lücke einen Namen hat.

### Claudes Ermessen

- Das Hash-Verfahren und die Kanonisierung der Felder (naheliegend SHA-256 über eine
  festgelegte Feldreihenfolge, wie `store.py` es für Token-Digests hält).
- Tabellenschnitt, Indizes und Pragmas der neuen Datei, solange sie dem Muster von
  `store.py` folgen (WAL, `busy_timeout`, Arbeit in `asyncio.to_thread`).
- Name und genaue Form des Prüfkommandos. Der Weg steht fest: über AppAPI-`PublicFunctions`
  wie `occ mcp_connector:purge`, **ohne neue Route im Manifest** (`exapp/purge.py` erklärt,
  warum eine deklarierte Route eine instanzweite Wirkung ins Internet stellte).
- Die Schwelle in D-12 und das Bündelungsintervall in D-11.
- Der Zuschnitt der Erlaubnislisten je Werkzeug, solange kein Wert und kein Inhalt darin
  landet.
- Die Aufteilung in Pläne und Wellen.

### Zurückgestellt (NICHT IM UMFANG)

- Ausgabe und Export des Logs für Administratoren, AUDIT-04, Phase 19.
- Sichtbare Admin-Beschriftung samt Mitbestimmungshinweis, AUDIT-05, Phase 19. Der Schalter
  selbst entsteht schon hier (D-14), nur ohne Oberfläche.
- Textnachzug in `docs/privacy.md`, `docs/uninstall.md` und im Enterprise-Absatz, AUDIT-06,
  Phase 19.
- Auslieferung als Release 0.1.12, EXAPP-12, bewusst ausserhalb des Milestones v1.5.
- Ein Ereignisweg über AppAPI für die Nutzerlöschung, verworfen für diese Phase (D-12).
- IP-Adresse oder User-Agent im Eintrag, verworfen (D-08), nicht wieder aufmachen ohne
  ausdrücklichen Owner-Entscheid.
</user_constraints>

---

<phase_requirements>
## Anforderungen dieser Phase

| Id | Beschreibung | Wo diese Recherche trägt |
|----|--------------|--------------------------|
| AUDIT-01 | Jeder Werkzeugaufruf erzeugt einen Eintrag mit Nutzer, Werkzeugname, Zeitpunkt, aufrufendem Client und Ergebnisstatus, ohne Parameterwerte und ohne Ergebnisinhalte; Erlaubnisliste je Werkzeug, Vertragstest nach dem Muster des Budget-Gates | §1 (Erfassungspunkt, Identität, gesetzte Parameternamen), §2 (Vertragstest), §5 (Statusklassen und Gründe) |
| AUDIT-02 | Jeder Eintrag ist mit seinem Vorgänger hash-verkettet, ein Prüfkommando bestätigt die ungebrochene Kette oder benennt die erste gebrochene Stelle | §4 (Kettenbau und Prüfalgorithmus), §6 (occ-Weg und die Ausgabe-Falle) |
| AUDIT-03 | Eigene Ablage neben dem OAuth-Speicher, Obergrenze, Aufbewahrungsfrist ab 180 Tagen, kann den OAuth-Speicher nicht schreibunfähig machen | §3 (SQLite-Muster und Pfad), §8 (Größenmessung, die einzige, die stimmt) |

</phase_requirements>

---

## Zusammenfassung

Die Phase ist besser aufgestellt, als sie aussieht. Die drei teuersten Unbekannten sind
gemessen und ausgeräumt: **die gesetzten Parameternamen sind im Dekorator sauber zu bekommen**
(nicht über `kwargs`, sondern über `ctx.request_context.params["arguments"]`, gemessener Beweis
in §1), **das Konto-Existenz-Problem aus D-12 hat einen fertigen AppAPI-Endpunkt** ohne neue
Berechtigung (`GET /ocs/v2.php/apps/app_api/api/v1/users`, verifiziert im Quelltext von
app_api v34.0.3, §7), und **die Obergrenze aus D-09 lässt sich nur auf genau eine Art
verlässlich messen** (`(page_count - freelist_count) * page_size`, alles andere schrumpft nach
einem `DELETE` nicht, gemessener Beweis in §8). Alle 21 Werkzeuge tragen den `@graceful`-Wrapper
heute schon (gemessen, §2), und der Dekorator berührt die `tools/list`-Fläche nicht, weil das
SDK das Schema über `__wrapped__` aus der ursprünglichen Signatur baut. Das Budget bleibt bei
15712 von 18000 Bytes über 21 Werkzeuge stehen (frisch nachgemessen, §10).

Drei Entscheide laufen in der Umsetzung an eine Wand, und alle drei sind mit Beleg benannt statt
stillschweigend umgebogen. **D-15 kann den handelnden Administrator nicht nennen**: AppAPIs
`SetValueListener` verwirft `$event->getUser()` für Admin-Formulare und speichert nur den Wert
(Quelltext app_api v34.0.3, §9). **D-07 hat heute keine Fehlerklassen zum Ablesen**: rund 230
Stellen werfen einen flachen `ToolError` mit Freitext, und `graceful` kann 403 nicht von 404
unterscheiden; der billige Ausweg sind rund sieben Statusabbildungen, die eine feste Kennung
mitgeben (§5). Und **das Erfolgskriterium 5 der Roadmap ist in seiner zweiten Hälfte nicht
haltbar**: `occ app_api:app:unregister mcp_connector --rm-data` entfernt das Volume, und in dem
liegt nach D-01 auch das Audit-Log (`docs/uninstall.md:19`, `:229-235`); es überlebt den Purge
und den Entfernen-Knopf von Nextcloud 34, aber keine Volume-Löschung (§11).

**Primäre Empfehlung:** Ein neues Paket `src/mcp_connector/audit/` mit drei Dateien
(`store.py` nach dem Muster von `oauth/store.py`, `record.py` für Kettenbau und Erfassung,
`allowlist.py` für die Parameternamen je Werkzeug), ein Aufruf im `finally`-Zweig von
`graceful`, der Rekorder über `request.state` aus derselben Middleware, die schon die
OAuth-Identität hinterlegt, ein zweites occ-Kommando neben `purge` und drei neue Vertragstests
neben den drei bestehenden. Standardbibliothek, kein neues Paket, keine neue Route.

---

## Architektonische Zuständigkeiten

| Fähigkeit | Primäre Schicht | Sekundär | Begründung |
|-----------|-----------------|----------|------------|
| Erfassung eines Aufrufs | `server/__init__.py` (`graceful`) | -- | D-04; der Wrapper sieht Rückgabe und Ausnahme und hängt an allen 21 Werkzeugen (gemessen) |
| Identität des Aufrufers | `exapp/middleware.py` + `oauth/verifier.py` | `deps.py` | Die Identität wird pro Anfrage einmal aufgelöst und in `request.state` hinterlegt (`middleware.py:234`); der Aufrufpfad liest, statt aufzulösen |
| Ablage, Kette, Aufräumen | neues `audit/store.py` | -- | D-01; erbt Pragmas, `asyncio.to_thread` und Transaktionsform von `oauth/store.py` |
| Erlaubnisliste je Werkzeug | neues `audit/allowlist.py` | `tests/contract/` | Konstante Daten plus Gate; das Gate gehört zu den Verträgen, nicht zum Laufzeitpfad |
| Schalter (ab Werk aus) | `exapp/config_values.py` + `exapp/admin_settings.py` | `entry_exapp.py` | D-14; die Kette Admin-Wert, Deploy-Variable, Vorgabe im Code steht schon (`config_values.py:54-57`) |
| Prüfkommando | neues Handler-Modul + `exapp/occ.py` | `appinfo/info.xml` (nur der Kommentar) | Muster `exapp/purge.py`; kein `<route>` im Manifest |
| Anbindung an die Anwendung | `entry_exapp.build_exapp_app` | -- | Ein Opener je Anwendung, kein Modulzustand (D-20) |

---

## Frage 1: Was sieht `@graceful`, und woher kommt die Identität

### Der Dekorator heute

`src/mcp_connector/server/__init__.py:68-99`:

```python
def graceful[T](fn: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
    @functools.wraps(fn)
    async def wrapper(*args: Any, **kwargs: Any) -> T:
        try:
            return await fn(*args, **kwargs)
        except ToolError as exc:
            raise ValueError(f"{exc.message} Hint: {exc.hint}") from None
        except httpx.TimeoutException:
            ...
        except httpx.RequestError:
            ...
```

Die Reihenfolge der Dekoratoren ist in jeder `reg_*.py` gleich (Beispiel
`server/reg_files.py:17-19`):

```python
@mcp.tool(annotations=READ_ONLY, structured_output=False)
@graceful
async def files_search(...)
```

`@graceful` liegt also **unter** `@mcp.tool`. Damit ist `Tool.fn` genau dieser Wrapper.
Gemessen (eigener Probelauf über `mcp._tool_manager.list_tools()`, 2026-08-29): alle 21
Werkzeuge haben `fn.__code__.co_name == "wrapper"` und `hasattr(fn, "__wrapped__") is True`,
und alle 21 haben `context_kwarg == "ctx"`.

### Werkzeugname

`functools.wraps` überträgt `__name__`, deshalb ist `fn.__name__` im Closure der Werkzeugname.
Kein einziges Werkzeug wird heute mit `name=` registriert (geprüft über alle
`server/reg_*.py`: 21 Treffer `@mcp.tool(`, keiner mit `name=`), also gilt heute
`Tool.name == Tool.fn.__name__`. Das ist eine Eigenschaft von heute, keine Garantie.

**Empfehlung:** Den Namen aus `ctx.request_context.params["name"]` nehmen und auf
`fn.__name__` zurückfallen. `params["name"]` ist der Name, unter dem der `ToolManager`
aufgelöst hat (`mcp/server/mcpserver/tools/tool_manager.py:31-33`), kann also nie ein
unbekannter Name sein. Zusätzlich ein Vertragstest, der `tool.name == tool.fn.__name__`
für alle Werkzeuge behauptet, damit die beiden Wege nicht auseinanderlaufen.

### Argumentnamen: `kwargs` ist die falsche Quelle

`Tool.run` ruft die Funktion ausschliesslich mit Schlüsselwortargumenten auf
(`mcp/server/mcpserver/utilities/func_metadata.py:106`: `return await fn(**arguments_parsed_dict)`),
`args` ist im Wrapper also immer leer. Der Inhalt entsteht aus
`FuncMetadata.validate_arguments` (`func_metadata.py:73-80`), und das ruft
`model_dump_one_level()` (`func_metadata.py:50-61`), welches **über alle `model_fields`
iteriert**. Vorgabewerte sind darin also materialisiert.

**Folge:** `kwargs` kann "vom Aufrufer gesetzt" nicht von "Vorgabewert" unterscheiden. D-06
verlangt aber genau "nur die gesetzten Namen".

**Der Weg, der es kann** (eigene Messung 2026-08-29, In-Memory-`Client`, Aufruf mit nur
einem von zwei Parametern):

```
ctx.request_context.params
  == {'name': 'probe_tool',
      'arguments': {'a': 'SECRETVALUE'},
      '_meta': {'io.modelcontextprotocol/protocolVersion': '2026-07-28',
                'io.modelcontextprotocol/clientInfo': {'name': 'mcp', 'version': '0.1.0'},
                'io.modelcontextprotocol/clientCapabilities': {}}}
```

`params["arguments"]` enthält genau die gesetzten Schlüssel, `b` fehlt. `ServerRequestContext`
ist ein Datenklassenfeld des Kontexts (`mcp/server/context.py:31-49`, Feld `params`) und wird
transportunabhängig aus der JSON-RPC-Nachricht gefüllt, der Probelauf lief ohne HTTP.

**Zwei Regeln für die Umsetzung, beide load bearing:**
1. Nur `.keys()` lesen, niemals `.values()`. Die Werte liegen in derselben Struktur.
2. Zusätzlich mit der Erlaubnisliste des Werkzeugs schneiden (`set(keys) & ALLOWLIST[tool]`),
   damit ein Aufrufer keinen erfundenen Schlüsselnamen ins Log schreiben kann. Die Argumente
   sind Eingabe von außen; ein unbekannter Schlüssel wird von pydantic zwar verworfen, steht
   aber trotzdem in `params["arguments"]`.

**Ausdrücklich nicht verwenden:** `_meta["io.modelcontextprotocol/clientInfo"]`. Das ist
selbstdeklariert vom Client und wäre eine zweite, ungeprüfte Client-Identität neben der aus
D-08. Nennen und liegen lassen.

### Nutzer, Client-Id und Verbindungs-Id

Es gibt fünf Anmeldearten (`deps.py:1-36`). Für das Log zählen zwei:

| Weg | Nutzer | Client-Id | Verbindungs-Id | Client-Name |
|-----|--------|-----------|----------------|-------------|
| OAuth (AUTH-03) | `OAuthIdentity.nc_user` | `OAuthIdentity.client_id` | `OAuthIdentity.auth_id` | siehe unten |
| AppAPI-Impersonation (AUTH-01) | Nutzer-Id aus `AUTHORIZATION-APP-API` | keine | keine | keine |
| stdio / statischer Bearer / HTTP-Passthrough | aus Umgebung bzw. Basic-Header | keine | keine | keine |

`OAuthIdentity` (`oauth/verifier.py:102-119`) trägt heute `nc_user`, `app_password`, `auth_id`,
`client_id`, `revoked`. Sie wird pro Anfrage einmal in der Middleware aufgelöst und unter
`OAUTH_STATE_ATTR = "oauth_identity"` in `request.state` hinterlegt
(`exapp/middleware.py:234`, Konstante in `oauth/verifier.py:90`). `deps._oauth_identity`
(`deps.py:230-246`) liest sie von dort. **Kein zusätzlicher Nextcloud-Aufruf**, kein
zusätzlicher Speicher-Lesevorgang.

Der Nutzername kommt also **ohne Nextcloud-Aufruf** zustande, auf jedem der fünf Wege:
`deps.resolve_credentials(ctx)` ist synchron und rein lokal (Basis64-Dekodierung plus
`secrets.compare_digest` in `exapp/auth.py:52-78`, Umgebungslesen in `config.py`). Es gibt
keinen Netzaufruf darin.

**Empfehlung:** Eine neue, öffentliche Funktion in `deps.py`, etwa
`resolve_caller(ctx) -> Caller`, die genau die vier Felder ohne Geheimnis zurückgibt.
`resolve_credentials` selbst darf der Erfassungspfad nicht nehmen, weil das Ergebnis das
Nextcloud-Passwort trägt (`nextcloud/credentials.py`, maskiertes `repr`) und weil es bei
fehlendem Kontext `MCPError` wirft. Ein Rekorder darf nichts werfen (D-13).

### Client-Name: der Weg, der nichts kostet

`OAuthIdentity` hat den Namen nicht. `oauth/connections.py:384-405` zeigt, wie er heute geholt
wird (`store.load_client(client_id)`, `json.loads(row.metadata_json)`, Schlüssel `client_name`).
Das wäre ein dritter Speicherzugriff pro Anfrage, und der Modul-Docstring von
`oauth/verifier.py` verspricht ausdrücklich, dass der Speicher nicht im heißen Pfad sitzt.

Es gibt einen Weg ohne jede zusätzliche Ein-/Ausgabe: `StoreTokenVerifier.verify_token` lädt
den Client **bereits** (`oauth/verifier.py:229`, `await self._get_client(..., may_fetch=False)`,
Rückgabe `OAuthClientInformationFull`, und dieses Modell hat das Feld `client_name`, geprüft
über `model_fields`). Das Ergebnis wandert ohnehin in den Fünf-Sekunden-Prozesscache. Also:

1. `verify_token` legt den Namen in `AccessToken.claims` (das Modell hat genau dieses Feld,
   und `AUTH_ID_CLAIM` nutzt es schon so, `oauth/verifier.py:84-87`).
2. `resolve_identity` kopiert ihn in ein neues Feld `OAuthIdentity.client_name`.
3. Der Erfassungspfad liest ihn aus `request.state`.

Kosten: null zusätzliche Lesevorgänge. Preis: bis zu fünf Sekunden ein veralteter Name nach
einer Umbenennung, was für ein Protokoll ohne Belang ist.

**Warum der Name überhaupt in die Zeile gehört, statt beim Lesen aufgelöst zu werden:**
D-v1.5-01 verlangt, dass das Log den Purge überlebt. `occ mcp_connector:purge` leert die
Client-Tabelle (`oauth/store.py:1334`, `DELETE FROM clients`). Ein später aufgelöster Name
wäre danach weg. Der Name muss in der Zeile stehen.

**Falle, die dabei mitkommt:** Der Client-Name ist vom Angreifer gewählt (er kommt aus der
dynamischen Client-Registrierung). `exapp/ui/layout.py:506-522` entschärft ihn für die
Anzeige: nicht druckbare Zeichen raus, Leerraumfolgen zusammen, auf `CLIENT_NAME_LIMIT`
gekürzt. Der Erfassungspfad braucht dieselbe Behandlung, darf aber `exapp/ui` nicht
importieren (Schichtung: `server/` und `audit/` liegen unter der ExApp-Schale). Also eine
eigene, kurze Klammerung im Audit-Modul, mit einer eigenen Längenkonstante.

### Ausnahmeklassen, die der Wrapper sieht

| Was ankommt | Woher | Was `graceful` heute tut |
|-------------|-------|--------------------------|
| `ToolError` (und `AppMissingError`, `ConflictError`) | `errors.py:9-23`, rund 230 Wurfstellen | wird zu `ValueError(message + hint)` |
| `httpx.TimeoutException` | Nextcloud antwortet nicht | wird zu `ValueError` |
| `httpx.RequestError` | Nextcloud nicht erreichbar | wird zu `ValueError` |
| `MCPError` | `deps.resolve_credentials` bei fehlendem Nutzerkontext (`deps.py:205-219`) | läuft ungefangen durch |
| alles andere | Programmierfehler | läuft ungefangen durch, `Tool.run` verpackt es (`tools/base.py:191-192`) |

Für die Erfassung heißt das: `try / except / else / finally` mit einem breiten
`except BaseException` **nur zum Merken der Klasse**, danach `raise`. Der Erfolgsfall gehört
in den `else`-Zweig oder wird am Rückgabewert erkannt.

---

## Frage 2: Der Vertragstest "kein Werkzeug kann vorbei"

### Wie man an die Werkzeuge kommt

Zwei Wege, beide gemessen:

| Weg | Liefert | Für was |
|-----|---------|---------|
| `mcp._tool_manager.list_tools()` | `Tool`-Objekte mit `.fn`, `.name`, `.parameters` (JSON-Schema), `.fn_metadata.arg_model.model_fields`, `.context_kwarg` | den Dekorator-Nachweis, weil nur hier `.fn` steht |
| `async with Client(mcp) as c: await c.list_tools()` | `MCPTool`-Drahtmodell mit `inputSchema` | Parameternamen, wie `scripts/check_tool_budget.py:121-122` und `tests/contract/test_tool_surface.py:84-86` sie schon holen |

`_tool_manager` ist privat. Der Boundary-Gate `tests/contract/test_module_boundaries.py` prüft
ausschliesslich Zugriffe auf Privates **von Modulen unter `tools/`** und betrifft
`tests/` gar nicht (der Gate läuft nur über `src/mcp_connector`). Der Zugriff auf
`mcp._tool_manager` in einem Vertragstest ist damit erlaubt, und die 53 `SLF`-Treffer in
`tests/` werden im Docstring desselben Gates ausdrücklich als "Quell-Gates, die ihre Arbeit
tun" benannt.

### Wie man "trägt den Dekorator" erkennt

`fn.__code__.co_name == "wrapper"` funktioniert (heute 21 von 21), ist aber zerbrechlich:
jeder Dekorator, dessen innere Funktion `wrapper` heißt, käme durch.

**Empfehlung:** Ein ausdrücklicher Marker auf dem Wrapper, gesetzt in `graceful`:

```python
wrapper.__mcp_audited__ = True   # oder ein Sentinel-Objekt statt True
```

und im Vertragstest `getattr(tool.fn, "__mcp_audited__", False) is True` für jedes
registrierte Werkzeug. Ein neues Werkzeug ohne `@graceful` lässt den Test rot werden, und der
Gegenbeweis dazu ist billig: eine Funktion im Test ohne Dekorator registrieren und prüfen,
dass der Marker fehlt (die Zählprüfung des Testfiles muss dann in einer Fixture wieder
aufgeräumt werden, siehe unten).

**Achtung bei der Zählprüfung:** `tests/contract/test_tool_surface.py:39-59` vergleicht die
Werkzeugmenge gegen ein eingefrorenes Literal `EXPECTED_TOOLS` (Mengenvergleich, kein Teilmengen-
Test). Ein Testwerkzeug, das dauerhaft am Modulsingleton `mcp` hängen bliebe, macht diese Datei
rot. `ToolManager.remove_tool` existiert (`tool_manager.py:69-73`) und ist der saubere Abbau.
Besser noch: den Gegenbeweis ohne Registrierung führen, direkt gegen eine dekorierte und eine
undekorierte Funktion.

### Wie man an die Parameternamen kommt

Drei gleichwertige Quellen, für den Gate am besten die erste (kein Client, kein Ereignisschleifen-
Aufbau):

- `tool.parameters["properties"].keys()` (JSON-Schema, `by_alias=True`, `tools/base.py:99`)
- `tool.fn_metadata.arg_model.model_fields` (Feldnamen plus Alias plus Vorgabewert)
- `inputSchema` des Drahtmodells über den `Client`

Gemessene Fläche 2026-08-29, alle 21 Werkzeuge mit ihren Eigenschaften:

```
calendar_create_event  all_day, calendar, description, end, location, start, summary, timezone
calendar_list_events   calendar, end, limit, start, timezone
contacts_search        limit, query
deck_browse            board_id, level, limit, stack_id
deck_create_card       board_id, description, duedate, stack_id, title
fetch                  id
files_list             cursor, limit, path
files_read             offset, path
files_search           cursor, folder, limit, query
files_upload           content, path
mail_browse            account_id, cursor, filter, level, limit, mailbox_id
notes_create           category, content, title
notes_read             note_id
notes_search           limit, query
prepare_context        detail, query
search                 query
tables_browse          cursor, level, limit, table_id
tables_create_row      table_id, values
talk_browse            cursor, level, limit, token
talk_send              message, token
unified_search         limit, providers, query
```

`ctx` erscheint in keiner Liste: der Kontextparameter ist aus dem Schema herausgenommen
(`tools/base.py:88-95`, `skip_names`).

### Die drei Behauptungen, die der Gate halten muss

Nach dem Muster von `check_tool_budget.py` (eine Messung über alle, keine Stichprobe):

1. **Vollständigkeit:** Jedes registrierte Werkzeug hat einen Eintrag in der Erlaubnisliste.
   Ein Werkzeug ohne Eintrag ist ein Fehlschlag, kein stiller leerer Eintrag.
2. **Keine Erfindungen:** Jeder Name in der Erlaubnisliste eines Werkzeugs steht auch in
   dessen `properties`. Sonst zeigt die Liste auf einen Parameter, den es nicht mehr gibt,
   und niemand merkt es.
3. **Keine Verräter:** Kein Name der Erlaubnisliste steht auf einer Sperrliste. Kandidaten für
   die Sperrliste sind die Namen, deren blosse Nennung schon Inhalt verrät. Der klarste Fall
   ist `content` bei `files_upload` und `notes_create` sowie `message` bei `talk_send`: dass
   ein Inhalt mitgegeben wurde, ist bei diesen drei Werkzeugen ohnehin trivial wahr, der Name
   trägt also keine Information und steht nur da, um eines Tages versehentlich mit einem Wert
   zu wachsen. Der Zuschnitt selbst ist Claudes Ermessen (siehe CONTEXT), aber der Gate muss
   die Grenze halten, nicht die Disziplin.

`FORBIDDEN_PROPERTIES` in `tests/contract/test_tool_surface.py:79` ist das vorhandene Vorbild
für eine solche Sperrliste.

---

## Frage 3: Das SQLite-Muster, das die zweite Datei erbt

### Was `oauth/store.py` vormacht

| Sache | Stelle | Was übernommen wird |
|-------|--------|---------------------|
| Dateiname | `oauth/store.py:83` | `STORE_FILENAME = "oauth.sqlite3"`. **Achtung:** CONTEXT.md und mehrere Planungstexte sagen `store.sqlite3`; der Code sagt `oauth.sqlite3`. Der Code gilt. Analog etwa `AUDIT_FILENAME = "audit.sqlite3"` |
| Verbindung | `oauth/store.py:1447-1466` | `sqlite3.connect(path, isolation_level=None, timeout=_BUSY_TIMEOUT_SECONDS)`, danach die drei Pragmas |
| Pragmas | `oauth/store.py:1460-1462` | `journal_mode = WAL`, `foreign_keys = ON`, `busy_timeout = 5000` (`:1532-1533`). `foreign_keys` nur, wenn das Audit-Schema Fremdschlüssel hat; ohne sie kann es entfallen, aber es schadet nichts |
| Nebenläufigkeit | `oauth/store.py:1344-1354` | drei Hüllen `_read`, `_write`, `_transaction`, jede in `asyncio.to_thread(self._call, work, ...)` |
| Transaktion | `oauth/store.py:1356-1406` | `BEGIN IMMEDIATE` am Anfang, nicht am Ende; `ROLLBACK` als best effort |
| Schema | `oauth/store.py:1373-1387` | Skript läuft beim ersten Öffnen dieses Objekts **und** wenn die Datei fehlt; Flag am Objekt, nicht am Modul |
| Migration | `oauth/store.py:1469-1499` | `CREATE TABLE IF NOT EXISTS` plus `_add_missing_columns` mit `PRAGMA table_info` und einem `ALTER TABLE ADD COLUMN` |
| Kein Modulzustand | `oauth/store.py:1409-1444` | `store_opener(env)` gibt eine Closure zurück, keine globale Variable |

### Wo genau die Datei liegt

`config.persistent_storage(env)` (`config.py:240-283`):

- ExApp-Betrieb: das Verzeichnis aus `APP_PERSISTENT_STORAGE` (`ENV_APP_PERSISTENT_STORAGE`).
  Fehlt es, ist es kein Verzeichnis oder ist es nicht beschreibbar, wird `ToolError`
  geworfen (fail closed, `config.py:269-283`). Die Schreibbarkeit wird geprüft, indem eine
  Datei geschrieben und wieder entfernt wird (`config.py:286-299`), nicht mit `os.access`.
- Sonst: `Path.cwd() / DEV_STORAGE_DIR` mit einer WARNING-Zeile (`config.py:257-267`).

`entry_exapp.main` ruft `config.persistent_storage(resolved)` schon beim Start
(`entry_exapp.py:332`), also existiert und trägt das Verzeichnis, bevor die erste Anfrage
kommt. Die Audit-Datei liegt daneben: `config.persistent_storage(env) / AUDIT_FILENAME`.

### Anbindung an die Anwendung

`build_exapp_app` baut heute genau einen Speicher-Opener und reicht ihn an fünf Routenfabriken
(`entry_exapp.py:91`, `:169-181`). Der Audit-Opener gehört an dieselbe Stelle. Der
Erfassungspfad kann ihn aber nicht importieren, weil er in `server/__init__.py` sitzt und
keinen Zugriff auf die Anwendungsobjekte hat (und ein Modulglobal ist durch D-20 verboten,
siehe §12).

**Empfohlener Weg, weil er die vorhandene Naht benutzt:** `exapp/middleware.py::RequireAppApi`
hinterlegt schon die OAuth-Identität in `request.state` (`middleware.py:234`). Sie bekommt den
Audit-Rekorder mitgegeben und hinterlegt ihn unter einer zweiten Konstante, etwa
`AUDIT_STATE_ATTR = "audit_recorder"`. `graceful` liest über `ctx.request_context.request.state`;
fehlt der Rekorder, passiert nichts. Das macht die Erfassung automatisch zu einer
Eigenschaft des ExApp-Betriebs und lässt stdio und den freistehenden HTTP-Modus unberührt,
was auch inhaltlich richtig ist: dort gibt es keinen Administrator, keinen Nextcloud-
Konfigurationswert und damit keinen Schalter, der nach D-14 ab Werk aus stehen kann.

---

## Frage 4: Hash-Kette je Nutzer

### Empfohlene Bauform

Eine Tabelle, zwei Kettenarten, unterschieden durch die Kettenkennung:

```sql
CREATE TABLE IF NOT EXISTS entries (
  seq        INTEGER PRIMARY KEY AUTOINCREMENT,  -- global monoton, siehe unten
  chain      TEXT NOT NULL,      -- 'u:<nc_user>' oder 'i:instance' (D-02, D-03)
  kind       TEXT NOT NULL,      -- 'call' | 'tombstone' | 'switch'
  at         INTEGER NOT NULL,   -- Unix-Sekunden
  nc_user    TEXT,               -- NULL in der Instanzkette
  tool       TEXT,
  client_id  TEXT,
  auth_id    TEXT,
  client_name TEXT,
  outcome    TEXT,               -- D-07: ok | rejected | failed
  reason     TEXT,               -- D-07: feste Kennung, nur bei rejected
  duration_ms INTEGER,
  params     TEXT NOT NULL,      -- JSON-Liste von Namen, sortiert, nie ein Wert
  removed    INTEGER,            -- Grabstein: Anzahl der gewichenen Zeilen
  prev_hash  BLOB NOT NULL,      -- 32 Byte
  hash       BLOB NOT NULL       -- 32 Byte
);
CREATE INDEX IF NOT EXISTS entries_chain_seq ON entries(chain, seq);
CREATE INDEX IF NOT EXISTS entries_at ON entries(at);
```

`AUTOINCREMENT` ist hier nicht Zierde: es garantiert, dass eine `seq` nie wiederverwendet
wird, auch nicht nach dem Löschen der höchsten Zeile. Ohne das Schlüsselwort vergibt SQLite
`max(rowid)+1`, und nach einem Grabstein-Lauf, der die neuesten Zeilen träfe, käme eine Nummer
zweimal vor. Der Preis ist die interne Tabelle `sqlite_sequence`.

Ein globaler `seq` statt eines Zählers je Kette, weil er das Bündelungsintervall aus D-11 ohne
jeden Zustand liefert (siehe §8) und weil die Reihenfolge innerhalb einer Kette über
`ORDER BY seq` eindeutig bleibt.

### Kanonisierung

`json.dumps(felder_in_fester_reihenfolge, separators=(",", ":"), ensure_ascii=False)` über die
UTF-8-Bytes, dann `hashlib.sha256`. JSON entwertet Trennzeichen innerhalb der Werte, deshalb
kann kein Feldinhalt eine Feldgrenze vortäuschen. Das ist dieselbe Serialisierung, die
`server/__init__.py:63-65` als `compact` schon benutzt, aber das Audit-Modul schreibt sie
selbst hin: ein Import von `server` in `audit` wäre ein Ringschluss, weil `server` den
Rekorder aufruft.

```
hash = sha256(canonical([seq, chain, kind, at, nc_user, tool, client_id, auth_id,
                         client_name, outcome, reason, duration_ms, params, removed])
              + prev_hash)
```

`seq` gehört in die Kanonisierung. Ohne sie liesse sich eine Zeile innerhalb ihrer Kette
umnummerieren, ohne dass ein Hash bricht.

`prev_hash` als roher `BLOB` (32 Byte) statt Hexzeichenkette (64 Byte) spart bei zwei Hashes
pro Zeile 64 Byte, das sind gemessen rund 28 Prozent der Zeilengröße (siehe §8). `store.py`
schreibt Hex (`token_hash`, `oauth/store.py:251-258`), aber dort ist der Digest ein
Suchschlüssel; hier ist er es nicht. Beides ist vertretbar, die Bytes sprechen für `BLOB`.

Die erste Zeile einer Kette bekommt `prev_hash = b"\x00" * 32` als benannte Konstante.

### Der Prüfalgorithmus, der die **erste** gebrochene Stelle benennt

Je Kette, `ORDER BY seq`, ein Durchlauf, und beim ersten Fund abbrechen:

```
erwartet = GENESIS
für jede Zeile in der Kette:
    wenn zeile.prev_hash != erwartet:
        wenn die vorige Zeile ein Grabstein war und zeile.prev_hash == grabstein.hash:
            -> erklärte Lücke, weiter
        sonst:
            -> BRUCH: "in Kette <chain> fehlt oder wurde geändert zwischen seq <a> und <b>"
    wenn sha256(canonical(zeile) + zeile.prev_hash) != zeile.hash:
        -> BRUCH: "Zeile seq <n> in Kette <chain> wurde nachträglich verändert"
    erwartet = zeile.hash
```

Die zwei Fehlerarten sind bewusst getrennt und beide gefordert:

| Befund | Ursache | Meldung |
|--------|---------|---------|
| `hash` passt nicht zum Inhalt | eine Zeile wurde nachträglich verändert | benennt genau diese `seq` |
| `prev_hash` passt nicht zum Vorgänger | eine Zeile wurde entfernt oder eingeschoben | benennt das Paar `seq` davor und danach |

**Grabsteine als erklärte Lücke.** Ein Grabstein (D-10, D-12) ist selbst eine Zeile der Kette
und trägt `removed` (Anzahl) und in `prev_hash` den Endhash des Blocks, der gewichen ist. Die
Zeile nach ihm zeigt auf den Hash des Grabsteins. Damit ist die Lücke erklärt und nicht
gebrochen, ohne dass die Prüfung eine Sonderregel braucht: der Grabstein schliesst die Kette
über die Lücke hinweg.

**Bei D-12 (Nutzerlöschung) verschwindet die Kette komplett.** Ein Grabstein je gelöschter
Nutzerkette gehört dann in die **Instanzkette** (D-03), nicht in die verschwundene Nutzerkette,
sonst hätte er niemanden mehr, an den er anschliesst. Das ist eine Folgerung aus D-02 plus
D-03 und in CONTEXT.md nicht ausgeschrieben; sie ist die einzige Lesart, die beide Entscheide
gleichzeitig erfüllt.

### Ehrliche Grenze, die dazugehört

D-v1.5-02 verlangt eine Grenzbeschreibung "was es nicht leistet" als Pflichtbestandteil. Diese
Kette schützt gegen die **unbemerkte** Änderung einer Zeile durch jemanden, der die Datei
öffnet. Sie schützt **nicht** gegen jemanden, der die Datei schreiben und die Kette neu rechnen
kann: alle Bestandteile liegen in derselben Datei, es gibt keinen externen Anker, keine
Signatur mit einem Schlüssel ausserhalb des Volumes und keinen zweiten Ort, gegen den geprüft
wird. Ein selbst gefälschter Grabstein ist von einem echten nicht zu unterscheiden. Das gehört
so in den Modul-Docstring und in Phase 19 in den Text. Die vier verbotenen Wörter
(revisionssicher, AI-Act-konform, DSGVO-konform, SIEM-zertifiziert) gelten schon hier für
Kommentare und Doku dieser Phase.

### Nebenläufigkeit

Zwei gleichzeitige Aufrufe desselben Nutzers wollen dieselbe Kette verlängern. Lesen und
Schreiben müssen in **einer** Transaktion liegen:

```sql
BEGIN IMMEDIATE;
SELECT hash, seq FROM entries WHERE chain = ? ORDER BY seq DESC LIMIT 1;
INSERT INTO entries (...) VALUES (...);
COMMIT;
```

Das ist genau die Regel aus `oauth/store.py:1366-1371` (Fallstrick 10): `BEGIN IMMEDIATE`, weil
zwei Schreiber sich am Anfang ihrer Arbeit treffen sollen und nicht an deren Ende. Ein
Lesen-dann-Schreiben in zwei Transaktionen erzeugt zwei Zeilen mit demselben `prev_hash` und
damit eine gegabelte Kette, die die Prüfung als Bruch meldet.

**Folge für die Erfassung:** Der Schreibvorgang muss `await`-et werden, nicht als
`asyncio.create_task` abgesetzt. Eine abgesetzte Aufgabe hätte keine definierte Reihenfolge
und würde ihre Ausnahme verschlucken, was D-13 gerade verbietet (der Fehlschlag soll ins
Nextcloud-Log).

---

## Frage 5: Ergebnisstatus und Gründe (D-07)

### Was heute abzulesen ist, und was nicht

Die drei Klassen sind aus dem `graceful`-Rahmen sauber zu bilden:

| Klasse | Bedingung |
|--------|-----------|
| `ok` | die Funktion kehrt zurück |
| `rejected` | `ToolError` (inklusive `AppMissingError`, `ConflictError`), `httpx.TimeoutException`, `httpx.RequestError`, `MCPError` |
| `failed` | jede andere Ausnahme |

Die vier festen Kennungen sind **heute nicht ablesbar**. `errors.py:9-23` kennt genau drei
Klassen, und die Statusabbildung wirft überall einen flachen `ToolError` mit Freitext.
Beispiele mit Beleg: `nextcloud/clients/ocs.py:282-285` (403 wird `ToolError("No permission
for ...")`), `ocs.py:287-291` (404 und 998 werden `ToolError("Nextcloud did not find ...")`),
`nextcloud/clients/dav.py:526-530` (403), `dav.py:531-536` (404 und 409). Gezählt über
`src/`: 237 Vorkommen der drei Fehlerklassen, davon rund 230 Wurfstellen.

**Der teure Weg wäre**, für jede Kennung eine Unterklasse einzuführen und alle Wurfstellen
umzustellen. Das ist für diese Phase unverhältnismäßig.

**Der billige Weg, empfohlen:** `ToolError.__init__` bekommt ein optionales
Schlüsselwortargument `reason: str = REASON_UNSPECIFIED`, und die Kennung wird nur an den
**Statusabbildungen** gesetzt. Davon gibt es sehr wenige:

| Datei | Funktion / Zeilen | Deckt ab |
|-------|-------------------|----------|
| `nextcloud/clients/ocs.py` | `_status_error`, ab `:266` | die gesamte OCS-Familie: Deck, Notes, Tables, Talk, Mail, unified search |
| `nextcloud/clients/dav.py` | Schreibpfad `:505-556`, Lesepfad `:567-601` | Dateien |
| `nextcloud/clients/caldav.py` | `:445-479`, `:488-523` | Kalender |
| `nextcloud/clients/carddav.py` | `:375-404` | Kontakte |

Das sind rund sieben Funktionen. Damit sind `permission_denied` (403) und `unknown_id`
(404, 409, 998) für praktisch die ganze Oberfläche abgedeckt. `timeout` liest `graceful` direkt
aus `httpx.TimeoutException`. Für `guard_tripped` gibt es drei klar benennbare Orte:

- der Talk-Sendeschalter, `tools/talk.py:250-258`
- die Handhabungsprüfungen der Blätterung, `paging.py:47-88` (sieben Wurfstellen)
- die Kennungsprüfungen, `ids.py` (14 Wurfstellen)

Diese setzen die Kennung an der Wurfstelle, weil es dort wenige sind und weil sie inhaltlich
etwas anderes sagen als ein HTTP-Status.

`graceful` liest dann `getattr(exc, "reason", REASON_UNSPECIFIED)`. Alles, was keine Kennung
gesetzt hat, bekommt die unbestimmte, und das ist ehrlich: es steht dann `rejected` ohne Grund
im Log, statt eines geratenen Grundes.

**Was ausdrücklich nicht ins Log darf:** `exc.message` und `exc.hint`. Die tragen Pfade,
Dateinamen, Kalendernamen und Kennungen (`dav.py:527`: `f"No permission to write to {path}."`).
Das wäre Ergebnisinhalt und verstiesse gegen AUDIT-01. Ein Vertragstest, der die
Kennungsmenge gegen ein eingefrorenes Literal prüft, hält diese Grenze auf Dauer.

---

## Frage 6: Das occ-Kommando ohne Manifest-Route

### Wie `purge.py` es macht, in vier Teilen

1. **Registrierung** (`exapp/occ.py:95-130`): ein `POST` auf
   `/ocs/v2.php/apps/app_api/api/v1/occ_command` (`occ.py:49`, gegen app_api 34.0.3 verifiziert)
   mit dem Kommandoschema als JSON-Rumpf, mit OCS-Kopfzeilen plus AppAPI-Identität im
   App-Kontext (leere Nutzer-Id, `occ.py:110-119`). Wirft nie, protokolliert nur.
2. **Aufhängung** (`exapp/lifecycle.py:103-110`): im Zweig `enabled=1`, in einem eigenen
   `try`, weil ein nicht leeres `error`-Feld AppAPI dazu bringt, die App sofort wieder
   abzuschalten (Fallstrick 11 aus Phase 2). Abgemeldet wird nichts:
   `ExAppService::unregisterExApp` ruft `unregisterExAppOccCommands($appId)` selbst
   (`occ.py:16-19`).
3. **Der Handler** (`exapp/purge.py:133-212`): eine Starlette-`Route`, die von einer Fabrik
   ausgegeben und in `entry_exapp.py:180` an die Anwendung gehängt wird, nie am
   MCP-Serverobjekt registriert. `execute_handler` wird aus `PURGE_PATH` abgeleitet
   (`occ.py:57`), damit Route und Registrierung nicht auseinanderdriften.
4. **Die Doppelprüfung** (`exapp/purge.py:259-272`): erst `x-origin-ip` im Kopf, was den
   PHP-Proxy bedeutet und mit 404 beantwortet wird, dann `require_appapi`. Beides ohne
   Auskunft darüber, welche der Prüfungen abgelehnt hat.

### Was für ein zweites Kommando zusätzlich nötig ist

`OccCommandController::registerCommand` nimmt **genau ein** Kommando pro `POST`
(Signatur `registerCommand(string $name, string $description, string $execute_handler, int $hidden = 0, array $arguments = [], array $options = [], array $usages = [])`, app_api v34.0.3).
Also:

- `exapp/occ.py::command_scheme()` wird zu `command_schemes() -> list[dict[str, Any]]`, und
  `register_occ_commands` schleift darüber mit **einem `try` je Kommando**, damit ein
  Fehlschlag des einen nicht das andere kostet. Das ist dieselbe Begründung, mit der
  `lifecycle.py:93-102` die zweite Formularregistrierung in einen eigenen `try` gestellt hat.
- Ein zweites Handler-Modul mit eigener Pfadkonstante, eigener Fabrik und derselben
  Doppelprüfung. Es an `purge.py` anzuhängen wäre falsch: `purge` ist zerstörend und trägt
  eine Pflicht-Option, die Prüfung ist lesend und darf keine haben.
- Ein Eintrag in `entry_exapp.build_exapp_app`, in derselben Aufzählung wie `purge_routes`
  (`entry_exapp.py:169-181`).
- Der grosse Kommentar in `appinfo/info.xml:260-284` nennt heute vier bewusst abwesende Pfade
  (`/heartbeat`, `/init`, `/enabled`, `/purge`). Er muss den fünften nennen. Es gibt einen
  Test, der behauptet, dass `/purge` in keiner `<url>` auftaucht (`info.xml:283-284`); der
  neue Pfad braucht denselben.

### Die Falle in der Ausgabe, und sie entscheidet über die Form des Prüfkommandos

`ExAppOccService::buildCommand` (app_api v34.0.3, `lib/Service/ExAppOccService.php:159-213`):

```php
$response = $this->service->exAppRequest(..., options: ['stream' => true, 'timeout' => 0]);
if ($response->getStatusCode() !== Http::STATUS_OK) {
    $output->writeln(sprintf('[%s] command executeHandler failed', ...));
    return 1;
}
$body = $response->getBody();
while (!feof($body)) { $output->write(fread($body, 1024)); }
return 0;
```

Drei Folgerungen, alle drei planungsrelevant:

1. **Der Rumpf wird wörtlich ausgegeben.** Das Prüfkommando darf also lesbaren Text
   zurückgeben (`Response(..., media_type="text/plain")`) statt JSON, und ein Administrator
   liest das direkt. `purge.py` gibt JSON zurück, weil dessen Felder maschinell gelesen werden
   (`docs/uninstall.md:170-171`); für eine Kettenprüfung, die "die erste gebrochene Stelle
   benennt", ist Text die bessere Wahl. Eine Option `--json` kann beides anbieten.
2. **Ein Status ungleich 200 verwirft den Rumpf.** Wer den Bruch mit einem Fehlerstatus melden
   wollte, verlöre genau den Satz, der die Stelle benennt. Also: **immer 200 antworten**, das
   Urteil in den Rumpf. Der Preis ist, dass der Rückgabewert des Kommandos immer 0 ist, eine
   gebrochene Kette also von einem Überwachungsskript am Text und nicht am Rückgabewert erkannt
   wird. Das ist eine bewusste Abwägung und gehört in den Docstring.
3. **`timeout => 0`.** Eine Prüfung über ein 100-MB-Log darf lange laufen, AppAPI wartet.
   Trotzdem sollte der Handler streamen oder mindestens je Kette arbeiten, statt alles in den
   Speicher zu ziehen: bei 100 MB sind das nach der Messung in §8 rund 440.000 Zeilen.

### Optionen und ihre Drahtform

`purge.py:68-76` hat gemessen, wie AppAPI eine Option überträgt: der Rumpf ist
`{"occ": {"arguments": null, "options": {"force": true}}}`, das Flag liegt eine Ebene unter
der Spitze. `purge.py:296-317` liest alle Formen, in denen es ankommen kann. Ein Prüfkommando
mit Optionen (etwa `--user <id>` oder `--json`) erbt diese Leseform; ohne Optionen braucht es
sie nicht.

---

## Frage 7: Existiert dieses Nextcloud-Konto noch? (D-12)

### Der Weg, der ohne neue Berechtigung da ist

AppAPI stellt selbst einen Endpunkt bereit, der die Nutzerliste der Instanz zurückgibt:

```php
// app_api v34.0.3, appinfo/routes.php:72
['name' => 'OCSApi#getNCUsersList', 'url' => '/api/v1/users', 'verb' => 'GET'],
```

```php
// app_api v34.0.3, lib/Controller/OCSApiController.php:81-86
#[AppAPIAuth]
#[PublicPage]
#[NoCSRFRequired]
public function getNCUsersList(): DataResponse {
    return new DataResponse($this->exAppService->getNCUsersList(), Http::STATUS_OK);
}
```

```php
// app_api v34.0.3, lib/Service/ExAppService.php:199-203
public function getNCUsersList(): ?array {
    return array_map(function (IUser $user) {
        return $user->getUID();
    }, $this->userManager->searchDisplayName(''));
}
```

`#[AppAPIAuth]` heisst: die vier Kopfzeilen aus `nextcloud/credentials.py:96-122` reichen, im
App-Kontext (leere Nutzer-Id), genau wie `exapp/occ.py:110-119` und
`exapp/config_values.py:426-438` es schon tun. **Keine Impersonation, keine neue Berechtigung,
keine neue Route, kein `provisioning_api`.** Der Pfad ist unter `'ocs' =>` registriert, also
sowohl über `/ocs/v1.php/...` als auch über `/ocs/v2.php/...` erreichbar; dieses Projekt
benutzt überall `/ocs/v2.php`.

Verifiziert an den Tags `v34.0.3` und `v34.0.0` von `nextcloud/app_api`, also genau der
Fassung, gegen die `exapp/occ.py:11` und `exapp/config_values.py:18-22` ihre eigenen Pfade
verifiziert haben. `nc_py_api` fährt denselben Weg (`NextcloudApp.users_list()` ruft
`GET {ae_url}/users` mit `ae_url = "/ocs/v1.php/apps/app_api/api/v1"`).

### Was er kostet, und was er antwortet

- **Er gibt die ganze Liste zurück**, nicht die Antwort auf eine Ja-Nein-Frage.
  `searchDisplayName('')` ohne Limit läuft über alle Nutzer. Auf einer Instanz mit zehntausend
  Konten sind das zehntausend Kennungen in einer Antwort. Der Lauf aus D-11 findet deshalb
  besser **alle** fraglichen Nutzer in einem Durchgang und stellt sie gegen eine einmal
  geholte Liste, statt je Nutzer zu fragen.
- **Für ein gelöschtes Konto fehlt die Kennung schlicht in der Liste.** Es gibt keinen
  eigenen Status, keine 404, keine Unterscheidung zwischen "gelöscht" und "nie dagewesen".
- **Ungeklärt und ausdrücklich als Annahme markiert:** ob `searchDisplayName('')` auf einem
  LDAP- oder Verzeichnis-Backend vollständig antwortet und ob deaktivierte Konten enthalten
  sind. `IUserManager::searchDisplayName` sucht über den Anzeigenamen; ein Backend mit
  Suchgrenze oder ein Konto ohne Anzeigenamen könnte fehlen. **Ein fehlendes Konto in dieser
  Liste löscht nach D-12 eine ganze Kette.** Das ist die gefährlichste Annahme dieser Phase.

**Empfohlene Absicherung, unabhängig vom Ausgang der Messung:**
1. **Fail-safe in die Löschrichtung.** Ein Lesefehler, eine leere Liste oder eine Antwort, die
   nicht als Liste lesbar ist, bedeutet "das Konto existiert", niemals "löschen". Genau die
   Asymmetrie, die `config_values.py:254-259` für die Admin-Werte schon formuliert: eine
   unlesbare Hülle ist nie eine leere.
2. **Eine leere Liste ist immer ein Fehler**, nie eine Instanz ohne Nutzer: das Log kann keine
   Einträge haben, wenn es keine Nutzer gibt.
3. **Die Schwelle aus D-12 grosszügig setzen.** Ein Konto, dessen letzter Eintrag jünger als
   die Schwelle ist, wird nicht einmal gefragt. 30 Tage sind eine Grössenordnung, die die
   Frage selten macht und trotzdem lange vor der 180-Tage-Frist greift.

**Vorgeschlagene Messaufgabe für die Planung** (eine Aufgabe, kein eigener Plan): gegen die
laufende HaRP-Topologie aus `compose.exapp.yml` den Endpunkt aufrufen, für einen existierenden
und einen gelöschten Nutzer, und die Antwort samt Statuscode in eine Beleg-Zeile schreiben.
Die Topologie steht in CI schon (`.github/workflows/ci.yml`, Job `exapp`), und
`tests/integration/test_exapp_dav_matrix.py` ist die Vorlage für einen Test, der `.env.exapp`
liest und sich sonst überspringt.

---

## Frage 8: Grenzen, Größe und das gebündelte Abräumen

### Die Größenmessung, und warum die naheliegende falsch ist

Eigene Messung, 2026-08-29, Python 3.13 mit SQLite 3.50.4, WAL, realistisches Zeilenschema:

| Schritt | `page_count*page_size` | Dateigrösse | WAL | `freelist_count` |
|---------|------------------------|-------------|-----|------------------|
| 20.000 Zeilen eingefügt | 4.534.272 | 4.526.080 | 4.148.872 | 0 |
| nach `wal_checkpoint(TRUNCATE)` | 4.579.328 | 4.579.328 | 0 | 0 |
| nach `DELETE` von 10.000 Zeilen | 4.579.328 | 4.579.328 | 2.496.752 | 532 |
| nach `DELETE` + Checkpoint | 4.579.328 | 4.579.328 | 0 | 532 |

**Das ist der wichtigste Befund der Phase.** Nach dem Löschen der Hälfte aller Zeilen fällt
weder `page_count*page_size` noch `os.stat(...).st_size`. Die Seiten wandern in die Freiliste.
Eine Schleife "solange Datei grösser als 100 MB, lösche die ältesten" würde deshalb **jedes
Mal weiterlöschen, bis die Tabelle leer ist**. Das ist die Falle, die diese Phase kaputt macht,
wenn sie nicht benannt wird.

**Die eine Zahl, die stimmt:**

```python
used_bytes = (page_count - freelist_count) * page_size
```

Sie fällt sofort nach dem `DELETE` (in der zweiten Messreihe von 3.928.064 auf 1.974.272), sie
braucht keinen Dateisystemzugriff, sie kostet drei billige Pragmas auf der ohnehin offenen
Verbindung, und die Freiliste wird von den nächsten `INSERT`s wiederverwendet, so dass die
Datei nicht weiter wächst. **Empfehlung: Die Obergrenze aus D-09 wird gegen `used_bytes`
gefahren.**

### Wenn die Datei selbst zurückgegeben werden soll

Zweite Messung, dieselbe Sitzung:

| Schritt | Seiten | `used` | Datei | WAL | frei |
|---------|--------|--------|-------|-----|------|
| 20.000 eingefügt | 959 | 3.928.064 | 3.780.608 | 4.124.152 | 0 |
| `DELETE` 10.000 | 959 | 1.974.272 | 3.928.064 | 5.574.392 | 477 |
| `PRAGMA incremental_vacuum(10000)` mit `.fetchall()` | 481 | 1.970.176 | 3.928.064 | 5.574.392 | 0 |
| `PRAGMA wal_checkpoint(TRUNCATE)` | 481 | 1.970.176 | **1.970.176** | 0 | 0 |

Drei Stolpersteine darin, alle drei gemessen:

1. **`PRAGMA auto_vacuum = INCREMENTAL` muss vor der ersten Tabelle laufen.** In der Messreihe
   ohne diese Zeile blieb `auto_vacuum` auf 0 und `incremental_vacuum` bewirkte nichts. Für
   `oauth/store.py` ist das ohne Belang, für die neue Datei entscheidet es sich beim allerersten
   Öffnen und ist danach nur noch mit einem vollen `VACUUM` änderbar. **Das gehört in
   `_connect` der neuen Datei, vor `executescript(SCHEMA)`.**
2. **`PRAGMA incremental_vacuum(N)` muss durchgeschritten werden.** Ohne `.fetchall()` gab
   dieselbe Anweisung genau eine Seite zurück (959 auf 958), mit `.fetchall()` alle 478
   (959 auf 481). Das ist eine Eigenheit des `sqlite3`-Moduls, kein SQLite-Verhalten. Kosten:
   6,4 ms für 478 Seiten.
3. **Die Datei schrumpft erst nach einem Checkpoint.** `page_count` fällt sofort,
   `os.stat(...).st_size` erst nach `PRAGMA wal_checkpoint(TRUNCATE)`.

**Empfehlung:** Beides. `used_bytes` regiert die Obergrenze, und `auto_vacuum = INCREMENTAL`
plus ein durchgeschrittenes `incremental_vacuum` im Aufräumlauf gibt den Platz auch dem
Dateisystem zurück. Das zweite ist es, was AUDIT-03 ("kann den OAuth-Speicher nicht
schreibunfähig machen") tatsächlich einlöst: die Obergrenze allein verhindert nur, dass wir
weiter wachsen, nicht dass wir bereits belegten Platz halten.

### WAL, und wie viel es zusätzlich braucht

Die WAL-Datei wuchs in beiden Messreihen auf rund 4,1 MB und wurde vom automatischen
Checkpoint (Vorgabe `wal_autocheckpoint = 1000` Seiten, hier 4096 Byte je Seite) dort gehalten.
Innerhalb einer offenen Schreibtransaktion kann kein Checkpoint laufen, deshalb wuchs sie beim
Löschen von 10.000 Zeilen in einer Transaktion auf 5,5 MB.

**Folge:** Das Abräumen löscht in begrenzten Stapeln (etwa 5.000 Zeilen je Transaktion) und
nicht in einem Zug. Und die 100 MB aus D-09 brauchen im Volume rund 6 MB Luft für WAL und SHM.
Ob die Obergrenze die WAL-Datei mitzählt, ist eine Entscheidung; die klarere Regel ist,
`used_bytes` allein zu zählen und die Luft in der Dokumentation zu nennen.

### Wie gross ist eine Zeile

Aus der ersten Messreihe mit dem realistischen Schema (dreizehn Spalten, zwei Hex-Hashes,
ein Index auf `(chain, seq)`): 4.534.272 Byte für 20.000 Zeilen, also **rund 227 Byte je
Eintrag**. 100 MB fassen damit rund **440.000 Einträge**. Mit `BLOB`-Hashes statt Hex
(2 mal 32 statt 2 mal 64 Byte) fallen rechnerisch rund 64 Byte weg, also rund 163 Byte je
Zeile und rund 640.000 Einträge. (Die zweite Zahl ist gerechnet, nicht gemessen.)

### Was ein Eintrag im Schreibpfad kostet

Gemessen, Windows/NTFS, Python 3.13:

| Form | Kosten je Eintrag |
|------|-------------------|
| eine offene Verbindung, Autocommit | 1,05 ms |
| frische Verbindung, `BEGIN IMMEDIATE`, `COMMIT`, `close` (das Muster von `oauth/store.py::_call`) | **7,2 ms** |

Der Unterschied ist das Öffnen der Verbindung plus ein `fsync` je Transaktion. 7,2 ms je
Werkzeugaufruf, in `asyncio.to_thread` und damit ohne Blockade der Ereignisschleife, gegen
Nextcloud-Antwortzeiten im zweistelligen bis dreistelligen Millisekundenbereich. Das ist
vertretbar und muss trotzdem als Zahl im Plan stehen.

**Wichtige Einschränkung:** Diese Zahl ist auf Windows/NTFS gemessen, die ExApp läuft in einem
Linux-Container auf einem Docker-Volume. Dort ist das Öffnen einer SQLite-Datei erfahrungsgemäss
deutlich billiger. Die Zahl ist also eine **Obergrenze**, keine Vorhersage. Eine Nachmessung im
Container gehört als Aufgabe in einen Plan, nicht als Vorbedingung.

### Das Bündelungsintervall aus D-11 ohne jeden Zustand

Ein Zähler im Modul ist verboten (D-20, §12). Der eingefügte `seq` ist die Antwort:

```python
if new_seq % SWEEP_EVERY == 0:
    ... Frist, Obergrenze, und alle SWEEP_USER_CHECK_EVERY Läufe auch die Kontoprüfung
```

Deterministisch, prüfbar in einem Test (Zeilen einfügen, bis `seq` das Vielfache trifft, und
den Lauf beobachten), ohne Zustand zwischen zwei Anfragen. Ein Vorschlag für die Zahlen:
`SWEEP_EVERY = 500` (bei 227 Byte je Zeile also rund alle 110 KB, was bei 100 MB Obergrenze
knapp 900 Läufe über die Lebensdauer bedeutet) und die Kontoprüfung aus D-12 nur bei jedem
zwanzigsten davon, weil sie als einzige einen Nextcloud-Aufruf kostet. Beide Zahlen sind
Claudes Ermessen und gehören als benannte Konstanten mit einer Begründungszeile in den Code,
nach dem Muster der Lebensdauern in `oauth/store.py:85-121`.

---

## Frage 9: Der Schalter, und die Wand, an die D-15 läuft

### Wie ein Admin-Wert heute gelesen wird

Die Kette ist: Admin-Wert, dann `NC_MCP_*` aus der Deploy-Umgebung, dann Vorgabe im Code
(`config_values.py:54-57`).

1. `CONFIG_KEYS` (`config_values.py:110-117`) sind gleichzeitig die Feldkennungen des
   Admin-Formulars und die Konfigurationsschlüssel, weil AppAPIs `SetValueListener` den Wert
   ohne Präfix unter der Feldkennung ablegt (`config_values.py:18-22`, im Quelltext bestätigt,
   siehe unten).
2. `KEY_TO_ENV` (`:121-128`) bildet jeden Schlüssel auf den Namen der Deploy-Variablen ab.
3. `SWITCH_KEYS` (`:133-135`) sind die Kästchen; `_switch` (`:396-413`) normiert auf `"on"`
   oder `"off"` und **verweigert einen Wert, den es nicht versteht**, statt eine Vorgabe zu
   raten.
4. `read_values` holt alle Schlüssel in einem `POST` auf
   `/ocs/v2.php/apps/app_api/api/v1/ex-app/config/get-values` (`:201-209`).
5. `entry_exapp._resolved_env` (`:239-281`) legt die Werte einmal beim Start über die
   Prozessumgebung und reicht die Abbildung an alle Fabriken.
6. `exapp/admin_settings.py:117-173` erklärt dieselben Kennungen als Formularfelder.

Ein neuer Wert heisst also: ein Eintrag in `CONFIG_KEYS`, einer in `KEY_TO_ENV`, einer in
`SWITCH_KEYS`, eine neue `ENV_*`-Konstante mit Leser in `config.py`, und ein Feld in
`admin_settings.form_scheme` mit `"default": False`. Es gibt einen Test, der Formular und
Lesepfad gleich hält (`admin_settings.py:12-14`, "ein Test hält diese Gleichheit").

**Zwei Fallen aus `admin_settings.py:17-26`, beide im fremden Quelltext verifiziert:**
`sensitive: true` lässt AppAPI den Wert mit dem Serverschlüssel verschlüsseln, so dass die
ExApp einen Klumpen zurückliest, den sie nicht öffnen kann. Und Declarative Settings kennen
keinen Knopf, weshalb Aktionen bei diesem Projekt immer occ-Kommandos sind.

### Der bekannte 401 beim Startzeit-Lesen

`config_values.py:215-239` beschreibt ihn ausführlich und gemessen
(05-12-MEASUREMENTS.md, M3b, M3c): `AppAPIService::validateExAppRequestToNC` nimmt das
App-Geheimnis an und fällt dann über `!$exApp->getEnabled()`; nur `ex-app/state` ist davon
ausgenommen. Der erste Start nach einer Installation liegt immer in diesem Fenster, weil
`enable` nach `init` kommt.

**Für einen ab Werk ausgeschalteten Schalter ist das genau richtig:** Ein 401 gibt `{}`
zurück, kein Wert kommt, die Vorgabe im Code gilt, und die ist "aus". Das ist die
fail-closed-Richtung. Die Zeile bleibt ein INFO, kein ERROR.

**Der Preis, den D-14 damit erbt:** Ein geänderter Wert wirkt erst, nachdem die App einmal
deaktiviert und wieder aktiviert wurde (`entry_exapp.py:255-259`). Das ist in der
Feldbeschreibung, in `docs/oauth-setup.md` und im Einrichtungszustand der Verbindungsseite
schon dokumentiert und gilt für alle sechs bestehenden Werte gleichermaßen. Es gilt dann auch
für den Audit-Schalter, und das ist kein Sonderfall, sondern der Hausstil.

### Die Wand: D-15 kann den handelnden Administrator nicht nennen

`app_api v34.0.3, lib/Listener/DeclarativeSettings/SetValueListener.php`:

```php
if ($formSchema['section_type'] === DeclarativeSettingsTypes::SECTION_TYPE_ADMIN) {
    $this->configService->setAppConfigValue($event->getApp(), $event->getFieldId(), $value);
} else {
    $this->preferenceService->setUserConfigValue(
        $event->getUser()->getUID(), $event->getApp(), $event->getFieldId(), $value
    );
}
```

Für ein **Admin**-Formular wird `$event->getUser()` verworfen. Die ExApp bekommt keinen
Rückruf, keine Benachrichtigung und keinen Namen. Der Wert wird abgelegt, mehr nicht. Ein
occ-Weg hilft nicht: `occ` läuft ohne Nutzersitzung.

D-15 verlangt "Zeitpunkt, Richtung und den handelnden Administrator". Zwei Drittel sind zu
haben, das dritte nicht auf diesem Weg.

**Empfohlene Umsetzung, die den Entscheid so weit einlöst, wie er einlösbar ist:**

Beim Start liest die ExApp den Schalter ohnehin (`entry_exapp._resolved_env`). Das Audit-Modul
hält den zuletzt bekannten Zustand in der Instanzkette. Weicht der gelesene Zustand davon ab,
wird ein Eintrag der Art `switch` in die Instanzkette geschrieben, mit Zeitpunkt und Richtung
und einem ausdrücklichen `actor = "unknown"`. Das ist kein Behelf, sondern die einzige mögliche
Form: da der Wert ohnehin erst mit einem Neustart wirkt, ist der Start der Moment, in dem die
Änderung wirksam wird, und genau der ist protokollierbar.

Der Grund für "unknown" gehört in den Docstring, mit dem Zitat oben, damit niemand ihn später
für Nachlässigkeit hält.

**Zwei Wege zu einem echten Namen, beide ausserhalb dieser Phase:**
- Phase 19 könnte den Schalter zusätzlich als ExApp-Seite bauen. HaRP löst das Nextcloud-Konto
  auf einer Route auf (`appinfo/info.xml:355-365`), und `exapp/auth.py::appapi_user` liest es.
  Das Feld `actor` im Schema wäre dann füllbar. Die belastbare Admin-Erkennung in einer
  ExApp-Seite ist allerdings in REQUIREMENTS.md ausdrücklich als ungelöst und ausserhalb des
  Umfangs geführt ("Eine Weboberfläche für das Audit-Log", Out of Scope).
- Ein occ-Kommando zum Umlegen des Schalters. Es hätte ebenfalls keinen Namen, aber es hätte
  eine Zeile im Nextcloud-Log mit dem, was der Systembetreiber ohnehin protokolliert.

**Für die Planung:** Das Feld `actor` gehört ins Schema. Es wird in dieser Phase mit einer
festen Kennung für "unbekannt" gefüllt. Das kostet nichts und macht Phase 19 oder später
möglich, ohne die Datei zu migrieren.

---

## Frage 10: Das Werkzeug-Budget

Frisch gemessen, 2026-08-29, `uv run --no-sync python scripts/check_tool_budget.py`:

```
tools/list: 15712 bytes, 21 tools, budget 18000
  mail_browse: 1376 bytes
  calendar_create_event: 1351 bytes
  calendar_list_events: 951 bytes
  search: 924 bytes
  talk_browse: 912 bytes
```

Deckungsgleich mit dem, was ROADMAP.md und REQUIREMENTS.md behaupten (15712 von 18000 über
21 Werkzeuge). `MAX_TOOL_BYTES = 1400` ist mit 1376 knapp bedient
(`scripts/check_tool_budget.py:117`).

**Berührt der Dekorator die `tools/list`-Fläche? Nein.** `Tool.from_function` baut das Schema
aus `func_metadata(fn, ...)` (`tools/base.py:90-99`), und `func_metadata` liest die Signatur
über `inspect`, das `__wrapped__` folgt, welches `functools.wraps` setzt. Der Beweis liegt im
laufenden Stand: alle 21 Werkzeuge tragen den Wrapper heute schon und haben trotzdem
vollständige Parameterschemata (gemessene Liste in §2). Ein Rumpf, der im Wrapper wächst,
ändert weder Signatur noch Docstring noch Annotationen und damit kein Byte der Fläche.

Dieselbe Mechanik trägt `find_context_parameter` (`tools/base.py:81`), weshalb `ctx` weiterhin
injiziert wird (gemessen: `context_kwarg == "ctx"` bei allen 21).

**Empfohlener Vertragsnachweis für die Phase:** Der Plan lässt `check_tool_budget.py` vor und
nach der Änderung laufen und schreibt beide Zahlen in eine Beleg-Zeile. Erwartet: 15712 vor und
15712 nach. Kein Grenzwert wird angefasst, und das ist auch die Rahmenbedingung, die
ROADMAP.md für alle vier Phasen des Meilensteins festhält.

---

## Frage 11: Was `purge` und die Deinstallation mit dem Log machen

### Purge: das Log bleibt, ohne dass etwas geändert werden muss

`exapp/purge.py:144-212` tut genau drei Dinge: App-Passwörter zurückgeben
(`_hand_back_every`), Tabellen leeren (`_empty` ruft `store.wipe_all()`), Datenschlüssel
löschen (`crypto.delete_key`). `wipe_all` (`oauth/store.py:1306-1340`) führt sieben
`DELETE FROM` auf den sieben OAuth-Tabellen aus, die Datei bleibt stehen und benutzbar. **Keine
dieser drei Handlungen berührt eine zweite Datei im selben Verzeichnis.** D-v1.5-01 ist damit
für den Purge ohne Codeänderung erfüllt.

**Zwei Bedingungen, die trotzdem eingehalten werden müssen:**

1. **Das Audit-Log darf nicht mit dem Datenschlüssel verschlüsselt werden.**
   `crypto.delete_key` löscht ihn, und ein damit verschlüsseltes Log wäre nach dem Purge zwar
   vorhanden, aber unlesbar. Das Log trägt ohnehin keine Geheimnisse (D-06: keine Werte, keine
   Inhalte), es braucht keine Verschlüsselung.
2. **Ein Test muss es festhalten.** `tests/unit/test_exapp_purge.py` gibt es schon; ein Fall
   darin, der eine Audit-Datei neben dem Speicher anlegt, den Purge laufen lässt und die Datei
   samt Zeilenzahl danach wiederfindet, ist der Beleg, den CONTEXT.md unter Integration Points
   verlangt ("das ist eine Änderung an der Aufräumlogik, die belegt werden muss"). Es ist
   genau genommen keine Änderung, sondern eine Behauptung, die niemand hält, solange sie
   niemand prüft.

### Deinstallation: hier stimmt Erfolgskriterium 5 nicht

`docs/uninstall.md` sagt, gemessen und mit Zeilen:

- Zeile 19 und 223-235: `occ app_api:app:unregister mcp_connector --rm-data` **entfernt das
  Volume**. Zeile 229-230 zitiert den Hilfetext des Gegenstücks: ohne das Flag bleibt das
  Volume.
- Zeile 48: Auf Nextcloud 34 gibt es keinen Entfernen-Knopf für ExApps; der Weg, den die
  Oberfläche früher rief, ist `disableExApp`, und dabei bleibt alles stehen.
- Zeile 47: Auf Nextcloud 32 und 33 gibt es ein Kästchen "Delete data on remove"; mit Haken
  geht das Volume.

Nach D-01 liegt die Audit-Datei in genau diesem Volume. **Also überlebt das Audit-Log:**

| Vorgang | Log überlebt? | Beleg |
|---------|---------------|-------|
| `occ mcp_connector:purge --force` | ja | `purge.py:187-190`, berührt nur OAuth-Tabellen und Schlüssel |
| Verbindung trennen, Pausieren | ja | ändert nur Zeilen in `oauth.sqlite3` |
| Entfernen-Knopf Nextcloud 34 (`disableExApp`) | ja | `docs/uninstall.md:48` |
| Nextcloud 32/33 Entfernen ohne Haken | ja | `docs/uninstall.md:47` |
| Nextcloud 32/33 Entfernen mit Haken | **nein** | `docs/uninstall.md:47`, Volume geht |
| `occ app_api:app:unregister --rm-data` | **nein** | `docs/uninstall.md:19, 229-235` |
| Aufbewahrungsfrist abgelaufen | nein, absichtlich | D-09 |
| Nutzer in Nextcloud gelöscht | nein, absichtlich | D-12 |

Erfolgskriterium 5 der Roadmap ("`occ mcp_connector:purge` und die Deinstallation lassen das
Audit-Log stehen") ist in seiner zweiten Hälfte für den dokumentierten Deinstallationsweg
nicht haltbar, und keine Umsetzung innerhalb von D-01 kann das ändern: eine Datei in einem
gelöschten Volume überlebt nicht.

**Das ist keine Einladung, D-01 aufzumachen.** Ein Pfad ausserhalb des Volumes wurde in
CONTEXT.md erwogen und verworfen, und er würde das Problem auch nur verschieben: ein Container
schreibt nur dorthin, wohin er eingehängt ist. Die ehrliche Auflösung ist eine Formulierung:
Das Log überlebt jeden Vorgang, der das Volume stehen lässt, und `--rm-data` ist der
ausdrückliche, dokumentierte Akt, das Volume zu vernichten. Diese Formulierung gehört in den
Modul-Docstring dieser Phase, und Phase 19 trägt sie nach `docs/privacy.md` und
`docs/uninstall.md`.

---

## Frage 12: Testarten, Gates und wo welcher Test hingehört

### Was es gibt

`pyproject.toml:36-47`:

```
testpaths = ["tests"]
addopts = "-m 'not integration and not matrix' -q --import-mode=importlib"
markers = [
  "integration: needs the Docker test Nextcloud (opt-in via -m integration)",
  "matrix: starts local subprocesses without Nextcloud (opt-in via -m matrix)",
]
```

| Verzeichnis | Was dort steht | Läuft im Vorgabelauf |
|-------------|----------------|----------------------|
| `tests/unit/` | 60 Dateien, alles ohne Netz; `tmp_path`-SQLite ist Hausstil (`test_oauth_store.py:1-10, 43-44`) | ja |
| `tests/contract/` | drei Gates: `test_tool_surface.py`, `test_no_destructive_calls.py`, `test_module_boundaries.py` | ja |
| `tests/integration/` | 21 Dateien, braucht die Docker-Nextcloud, Marker `integration` | nein |
| `tests/compat/` | Client-Matrix, Marker `matrix` | nein |

Asynchrone Tests laufen über `@pytest.mark.anyio` mit der `anyio_backend`-Fixture aus
`tests/conftest.py:13-16`, nicht über `pytest-asyncio` (das ist keine Abhängigkeit).

CI-Gates (`.github/workflows/ci.yml`, Job `unit`): `ruff check .`, `ruff format --check .`,
`pyright`, `vulture src scripts vulture_whitelist.py`, `pytest tests/unit tests/contract`,
`python scripts/check_tool_budget.py`, `pytest -m matrix`.

### Wo die Tests dieser Phase hingehören

| Test | Ort | Warum |
|------|-----|-------|
| Ablage: Schema, Pragmas, Kette, Nebenläufigkeit, Grabsteine, Frist, Obergrenze | `tests/unit/test_audit_store.py` | echte SQLite-Datei in `tmp_path`, genau wie `test_oauth_store.py` |
| **Manipulationstest** (eine nachträglich veränderte Zeile) | `tests/unit/test_audit_store.py` | siehe unten |
| Erfassung: gesetzte Namen, Statusklassen, Gründe, fail-open | `tests/unit/test_audit_record.py` | Wrapper direkt aufrufen, kein Server nötig |
| Erlaubnisliste vollständig, keine Erfindungen, keine Verräter | `tests/contract/test_audit_surface.py` | Gate, nicht Verhalten |
| Jedes Werkzeug trägt den Dekorator | `tests/contract/test_audit_surface.py` | Gate |
| Schalter: `CONFIG_KEYS` und Formularfelder decken sich | `tests/unit/test_exapp_config_values.py` und `test_exapp_admin_settings.py` | die beiden Dateien halten diese Gleichheit schon |
| Purge lässt die Audit-Datei stehen | `tests/unit/test_exapp_purge.py` | dort steht schon die Purge-Logik unter Test |
| occ-Registrierung: zwei Kommandos, unabhängige Fehlschläge | `tests/unit/test_exapp_lifecycle.py` und ein Fall zu `occ.py` | `lifecycle.py:103-110` ist dort schon geprüft |
| Prüfkommando: Handler antwortet 200, benennt die Stelle, Doppelprüfung greift | `tests/unit/` neben `test_exapp_purge.py` | Starlette-Route ohne Netz testbar |
| AppAPI-Nutzerliste am echten Endpunkt | `tests/integration/`, Marker `integration` | braucht die HaRP-Topologie, Vorlage `test_exapp_dav_matrix.py` |

### Wie man eine nachträglich veränderte Zeile testet

Genau so, wie ein Angreifer es täte, ohne durch das Modul zu gehen:

```python
# 1. Ein paar Einträge über die öffentliche Schnittstelle schreiben
# 2. Die Datei mit einer eigenen sqlite3-Verbindung öffnen:
conn = sqlite3.connect(tmp_path / audit.AUDIT_FILENAME, isolation_level=None)
conn.execute("UPDATE entries SET tool = ? WHERE seq = ?", ("files_read", 3))
conn.close()
# 3. Die Prüfung laufen lassen und behaupten:
#    - sie meldet einen Bruch
#    - sie nennt seq 3, nicht seq 4 und nicht "irgendwo"
#    - die Art ist "Zeile verändert", nicht "Zeile fehlt"
```

Der zweite Fall (`DELETE FROM entries WHERE seq = 3`) muss "fehlt zwischen 2 und 4" melden,
der dritte (ein echter Grabstein) darf gar nichts melden. Erst diese drei zusammen belegen,
dass die Prüfung unterscheidet, statt nur "gebrochen" zu rufen. Erfolgskriterium 3 der Roadmap
verlangt genau das.

### Die drei bestehenden Gates, die berührt werden

1. **`tests/contract/test_no_destructive_calls.py`: `DELETE` ist ein verbotenes Wort.** Die
   Ausnahme ist eng gefasst:
   ```python
   FILES_WITH_OWN_SQL = frozenset({"oauth/store.py"})
   SQL_DELETE_FORMS = ("DELETE FROM ", "ON DELETE CASCADE")
   ```
   (`test_no_destructive_calls.py:235-236`). Das Audit-Modul braucht `DELETE FROM` für Frist
   und Obergrenze, also muss seine Datei in diese Menge, mit einer eigenen Begründungszeile
   nach dem Muster der drei bestehenden. Der Gegenbeweis-Test `:395-410` läuft über
   `FILES_WITH_OWN_SQL` und prüft, dass jede genannte Datei existiert; er trägt einen zweiten
   Eintrag ohne Änderung.
2. **Modulzustand ist verboten** (`test_no_destructive_calls.py:615-641`). Erkannt werden
   `ast.Dict`, `ast.List`, `ast.Set`, die drei Comprehensions und Aufrufe von `dict`, `list`,
   `set`, `defaultdict`, `WeakKeyDictionary`, `WeakValueDictionary`. **Ausgenommen sind Namen
   in Grossbuchstaben** (`:635`: `if target.id.isupper()`). Die Erlaubnisliste je Werkzeug
   muss also `PARAM_ALLOWLIST` heissen und nicht `_param_allowlist`. Und
   `assert len(ALLOWED_MODULE_STATE) == 2` (`:658`) heisst: das Audit-Modul darf keinen
   dritten Cache anmelden, sonst ist es ein Review-Entscheid und kein Diff.
3. **`tests/contract/test_tool_surface.py`** vergleicht die Werkzeugmenge gegen ein
   eingefrorenes Literal (`:39-59`). Diese Phase fügt kein Werkzeug hinzu, also bleibt die
   Datei unberührt, solange kein Test dauerhaft etwas am Singleton registriert.

---

## Empfohlener Schnitt: Dateien und Verantwortungen

```
src/mcp_connector/audit/
├── __init__.py       # AUDIT_FILENAME, die Konstanten, audit_opener(env)
├── store.py          # AuditStore: Schema, Kette, Einfügen, Prüfen, Abräumen, Grabsteine
├── record.py         # Recorder: was graceful aufruft; nie eine Ausnahme nach oben (D-13)
└── allowlist.py      # PARAM_ALLOWLIST: dict[str, frozenset[str]] je Werkzeug

geändert:
  server/__init__.py            # graceful: Marker + finally-Zweig, sonst nichts
  deps.py                       # resolve_caller(ctx) -> Caller, ohne Geheimnis
  oauth/verifier.py             # client_name in claims und in OAuthIdentity
  exapp/middleware.py           # AUDIT_STATE_ATTR hinterlegen
  exapp/config_values.py        # ein Schlüssel mehr in CONFIG_KEYS/KEY_TO_ENV/SWITCH_KEYS
  exapp/admin_settings.py       # ein Feld mehr, default False
  exapp/occ.py                  # command_schemes() als Liste, Schleife mit try je Kommando
  exapp/<neu>.py                # Handler des Prüfkommandos, Fabrik, Doppelprüfung
  entry_exapp.py                # audit_opener bauen, Route anhängen, Schalter durchreichen
  config.py                     # ENV_AUDIT_* plus Leser
  errors.py                     # ToolError bekommt reason=
  nextcloud/clients/{ocs,dav,caldav,carddav}.py  # reason an ~7 Statusabbildungen
  appinfo/info.xml              # der fünfte bewusst abwesende Pfad im Kommentar

neu unter tests/: siehe Tabelle in §12
```

---

## Häufige Fallen

### Falle 1: `kwargs` als Quelle der gesetzten Parameternamen
**Was schiefgeht:** Jeder Eintrag nennt alle Parameter des Werkzeugs, auch die, die der
Aufrufer nie gesetzt hat. D-06 ist damit verfehlt, ohne dass ein Test es merkt.
**Warum:** `model_dump_one_level` materialisiert Vorgabewerte (`func_metadata.py:50-61`).
**Vermeidung:** `ctx.request_context.params["arguments"].keys()`, geschnitten mit der
Erlaubnisliste.
**Warnzeichen:** Ein Eintrag zu `files_list` nennt `cursor` und `limit`, obwohl der Aufruf
nur `path` hatte.

### Falle 2: Dateigrösse als Mass für die Obergrenze
**Was schiefgeht:** Der Aufräumlauf löscht bei jedem Durchgang weiter, bis die Tabelle leer
ist, weil die Grösse nach dem `DELETE` nicht fällt.
**Warum:** Gelöschte Seiten wandern in die Freiliste; `os.stat`, `page_count*page_size` und
sogar ein Checkpoint lassen sie liegen (gemessen, §8).
**Vermeidung:** `(page_count - freelist_count) * page_size`.
**Warnzeichen:** Ein Test, der 200 MB einfügt und danach null Zeilen findet.

### Falle 3: `PRAGMA incremental_vacuum` ohne `.fetchall()`
**Was schiefgeht:** Es wird genau eine Seite zurückgegeben, die Datei schrumpft praktisch
nicht, und der Fehler sieht aus wie "SQLite gibt nichts zurück".
**Warum:** Die Pragma-Anweisung liefert Zeilen, die durchgeschritten werden müssen; das
`sqlite3`-Modul führt sie sonst nur bis zum ersten Schritt aus (gemessen: 1 statt 478 Seiten).
**Vermeidung:** `conn.execute("PRAGMA incremental_vacuum(?)", ...).fetchall()`.

### Falle 4: `auto_vacuum` nach dem `CREATE TABLE`
**Was schiefgeht:** `PRAGMA auto_vacuum` bleibt auf 0 und lässt sich später nur noch mit
einem vollen `VACUUM` ändern, das die ganze Datei umschreibt.
**Warum:** Der Modus wird beim Anlegen der Datei festgelegt (gemessen: `effective=0`, wenn das
Pragma nach der ersten Tabelle kam).
**Vermeidung:** In `_connect`, vor `executescript(SCHEMA)`.

### Falle 5: Kette lesen und schreiben in zwei Transaktionen
**Was schiefgeht:** Zwei gleichzeitige Aufrufe desselben Nutzers erzeugen zwei Zeilen mit
demselben `prev_hash`. Die Prüfung meldet einen Bruch, wo keine Manipulation war.
**Warum:** Ohne `BEGIN IMMEDIATE` sehen beide Schreiber denselben letzten Hash
(`oauth/store.py:1366-1371`, Fallstrick 10).
**Vermeidung:** Ein `_transaction`-Rumpf mit `BEGIN IMMEDIATE`, `SELECT ... ORDER BY seq DESC
LIMIT 1`, `INSERT`, `COMMIT`.
**Warnzeichen:** Ein Test, der zwanzig Einträge parallel schreibt und danach eine gebrochene
Kette findet.

### Falle 6: Der Erfassungsvorgang wirft
**Was schiefgeht:** Ein voller Datenträger legt jeden Werkzeugaufruf lahm. Genau das, was D-13
ausschliesst.
**Warum:** Ein `await` im `finally`-Zweig ersetzt eine laufende Ausnahme, wenn er selbst wirft.
**Vermeidung:** Der Rekorder fängt `Exception` selbst, protokolliert **den Ausnahmetyp, nie die
Meldung** (die kann einen Pfad tragen, dieselbe Regel wie `purge.py:158-159`), und kehrt
zurück. Ein Test, der den Speicher durch einen wirft-immer-Doppelgänger ersetzt und behauptet,
dass das Werkzeug trotzdem antwortet.

### Falle 7: Fehlermeldung statt Kennung ins Log
**Was schiefgeht:** `exc.message` trägt Pfade, Kalendernamen, Kennungen. Das ist
Ergebnisinhalt und verletzt AUDIT-01.
**Warum:** Die Meldungen sind für das Modell geschrieben und deshalb konkret
(`dav.py:527`: `f"No permission to write to {path}."`).
**Vermeidung:** Nur `getattr(exc, "reason", ...)`, plus ein Vertragstest gegen eine
eingefrorene Kennungsmenge.

### Falle 8: Client-Name unbehandelt in die Zeile
**Was schiefgeht:** Ein Client registriert sich mit zweihundert Zeichen samt Zeilenumbrüchen
und Steuerzeichen; die Ausgabe des Prüfkommandos wird unlesbar oder täuscht Zeilen vor.
**Warum:** Der Name kommt aus der dynamischen Registrierung, also von aussen
(`exapp/ui/layout.py:506-522` entschärft ihn ausdrücklich für die Anzeige).
**Vermeidung:** Dieselbe Klammerung im Audit-Modul (nicht druckbare Zeichen weg, Leerraum
zusammen, feste Höchstlänge), ohne `exapp/ui` zu importieren.

### Falle 9: Ein Testwerkzeug bleibt am Modulsingleton hängen
**Was schiefgeht:** `tests/contract/test_tool_surface.py` wird rot, weil es die Werkzeugmenge
gegen ein eingefrorenes Literal vergleicht.
**Warum:** `mcp` ist ein Modulsingleton; ein `@mcp.tool` im Test wirkt für die ganze Sitzung.
**Vermeidung:** Den Gegenbeweis ohne Registrierung führen, oder `ToolManager.remove_tool` in
einer Fixture.

### Falle 10: `--rm-data` als "Deinstallation" lesen
**Was schiefgeht:** Der Plan verspricht etwas, das keine Umsetzung halten kann, und Phase 19
schreibt es in `docs/privacy.md`.
**Warum:** Das Flag entfernt das Volume (`docs/uninstall.md:19, 229-235`).
**Vermeidung:** Die Formulierung aus §11 in den Docstring, und Erfolgskriterium 5 in der
Verifikation ausdrücklich mit beiden Hälften belegen.

---

## Nicht selbst bauen

| Problem | Nicht bauen | Stattdessen | Warum |
|---------|-------------|-------------|-------|
| Asynchroner SQLite-Zugriff | `aiosqlite` oder eigener Wrapper | `asyncio.to_thread` je Aufruf, wie `oauth/store.py:1344-1354` | Die Begründung steht im Modul-Docstring von `store.py:9-13`: eine neue direkte Abhängigkeit für dreissig Zeilen |
| Verbindungspool | eigenes Pooling | eine frische Verbindung je Aufruf (gemessen 7,2 ms, §8) | Zwei Prozesse auf einer Datei sind ein unterstützter Fall (SRV-05); ein Pool wäre Modulzustand (D-20) |
| Konto-Existenz | eigene Provisioning-API-Anbindung, neue Berechtigung, Impersonation | `GET /ocs/v2.php/apps/app_api/api/v1/users` im App-Kontext (§7) | Ist schon da, `#[AppAPIAuth]`, keine neue Berechtigung |
| Kanonische Serialisierung | eigenes Trennzeichenformat | `json.dumps(..., separators=(",", ":"))` über eine feste Feldliste | Ein Trennzeichen im Wert täuscht sonst eine Feldgrenze vor |
| Hash | HMAC mit erfundenem Schlüssel, Merkle-Baum | `hashlib.sha256`, wie `oauth/store.py:251-258` | Ein Schlüssel im selben Volume ist kein Schutz, sondern eine zweite Sache, die der Purge zerstören kann |
| Terminierter Aufräumlauf | Cron, `asyncio`-Hintergrundaufgabe, Zähler im Modul | `seq % SWEEP_EVERY == 0` im Schreibpfad (D-11, §8) | Kein Zustand, kein Dienst, prüfbar |
| Zweites occ-Kommando | eine `<route>` im Manifest | zweites Schema in `command_schemes()`, zweite Fabrik | `appinfo/info.xml:266-284`: der PHP-Proxy hängt selbst gültige AppAPI-Kopfzeilen an |

**Kerneinsicht:** Fast jedes Teil dieser Phase hat im Repository schon eine Vorlage, die
begründet, warum sie so aussieht. Wo diese Recherche etwas Neues vorschlägt (Marker am Wrapper,
`params["arguments"]`, `used_bytes`, `auto_vacuum = INCREMENTAL`, Client-Name über `claims`),
ist es gemessen und in §1 bis §8 mit der Messung belegt.

---

## Codebeispiele

### Die Größenmessung, die stimmt

```python
def used_bytes(conn: sqlite3.Connection) -> int:
    """Wie viele Bytes dieser Speicher wirklich belegt.

    Nicht die Dateigrösse und nicht page_count*page_size: beide fallen nach einem DELETE
    nicht, weil die Seiten in die Freiliste wandern (Messung 2026-08-29: 20.000 Zeilen,
    10.000 gelöscht, Datei unverändert bei 4.579.328 Byte, 532 freie Seiten). Eine
    Obergrenze gegen eine dieser beiden Zahlen löscht bis zur leeren Tabelle weiter.
    """
    page_count = conn.execute("PRAGMA page_count").fetchone()[0]
    page_size = conn.execute("PRAGMA page_size").fetchone()[0]
    free = conn.execute("PRAGMA freelist_count").fetchone()[0]
    return (page_count - free) * page_size
```

### Das Anhängen an die Kette, in einer Transaktion

```python
def _append(conn: sqlite3.Connection, chain: str, fields: tuple[Any, ...]) -> int:
    conn.execute("BEGIN IMMEDIATE")
    row = conn.execute(
        "SELECT hash FROM entries WHERE chain = ? ORDER BY seq DESC LIMIT 1", (chain,)
    ).fetchone()
    prev = row[0] if row is not None else GENESIS
    seq = _next_seq(conn)
    digest = hashlib.sha256(_canonical(seq, chain, *fields) + prev).digest()
    conn.execute("INSERT INTO entries (...) VALUES (...)", (seq, chain, *fields, prev, digest))
    conn.execute("COMMIT")
    return seq
```

### Der Erfassungspunkt im Dekorator

```python
def graceful[T](fn: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
    @functools.wraps(fn)
    async def wrapper(*args: Any, **kwargs: Any) -> T:
        started = time.perf_counter()
        ctx = kwargs.get("ctx")
        outcome, reason = OUTCOME_OK, None
        try:
            return await fn(*args, **kwargs)
        except ToolError as exc:
            outcome, reason = OUTCOME_REJECTED, getattr(exc, "reason", REASON_UNSPECIFIED)
            raise ValueError(f"{exc.message} Hint: {exc.hint}") from None
        # ... die drei bestehenden Zweige, jeder setzt outcome und reason
        except BaseException:
            outcome, reason = OUTCOME_FAILED, None
            raise
        finally:
            # Wirft nie. Ein voller Datenträger darf keinen Werkzeugaufruf kosten (D-13).
            await audit.note(ctx, fn.__name__, outcome, reason, time.perf_counter() - started)

    wrapper.__mcp_audited__ = True
    return wrapper
```

### Die gesetzten Parameternamen

```python
def set_parameter_names(ctx: Any, tool: str) -> list[str]:
    """Nur die Namen, die der Aufrufer wirklich gesetzt hat, und nur erlaubte.

    params["arguments"] trägt genau die gesetzten Schlüssel; kwargs kann das nicht, weil
    das SDK Vorgabewerte materialisiert (func_metadata.py:50-61). Die Werte stehen in
    derselben Struktur, deshalb wird ausschliesslich über keys() gegangen. Der Schnitt mit
    der Erlaubnisliste ist die zweite Hälfte: die Argumente sind Eingabe von aussen, und
    ein erfundener Schlüsselname steht auch dann darin, wenn pydantic ihn verwirft.
    """
    params = getattr(getattr(ctx, "request_context", None), "params", None)
    if not isinstance(params, dict):
        return []
    arguments = params.get("arguments")
    if not isinstance(arguments, dict):
        return []
    return sorted(set(arguments.keys()) & PARAM_ALLOWLIST.get(tool, frozenset()))
```

---

## Laufzeitzustand, der diese Phase betrifft

Kein Umbenennen und keine Migration, aber diese Phase legt neuen Zustand an. Die fünf Fragen,
ausdrücklich beantwortet:

| Art | Was diese Phase anlegt oder berührt | Was zu tun ist |
|-----|-------------------------------------|----------------|
| Gespeicherte Daten | Eine neue Datei `audit.sqlite3` plus `-wal` und `-shm` im Volume aus `APP_PERSISTENT_STORAGE`. Vorhandene Installationen haben sie nicht | Nichts zu migrieren. Das Schema wird beim ersten Öffnen angelegt (`oauth/store.py:1373-1387`); eine Installation ohne die Datei bekommt sie beim nächsten Start |
| Konfiguration im laufenden Dienst | Ein neuer Schlüssel in der ExApp-Konfiguration von Nextcloud (Feldkennung = Konfigurationsschlüssel, `config_values.py:18-22`). Er liegt in Nextclouds Datenbank, nicht in git | Nichts zu setzen. Fehlt der Wert, gilt die Vorgabe im Code, und die ist "aus" |
| Bei Nextcloud registrierter Zustand | Ein zweites occ-Kommando. Registrierung im `enabled=1`-Zweig; Abmeldung übernimmt `unregisterExAppOccCommands` von selbst (`occ.py:16-19`) | Eine bestehende Installation bekommt es nach einem Deaktivieren-Aktivieren-Zyklus |
| Geheimnisse und Umgebungsvariablen | Eine neue `NC_MCP_*`-Variable als Vorgabestufe. Kein Geheimnis, kein Wert im Log | Nichts. Der Datenschlüssel wird ausdrücklich **nicht** benutzt (§11) |
| Bauartefakte | Keine. Kein neues Paket, keine neue Abhängigkeit, kein Versionswechsel (EXAPP-12 ist ausserhalb des Meilensteins) | Nichts |

---

## Umgebung und Abhängigkeiten

| Abhängigkeit | Gebraucht für | Vorhanden | Fassung | Ersatzweg |
|--------------|---------------|-----------|---------|-----------|
| Python `sqlite3` | die Ablage | ja | SQLite 3.50.4 (`sqlite3.sqlite_version`, gemessen im Projekt-venv) | -- |
| Python `hashlib` | die Kette | ja | Standardbibliothek | -- |
| `mcp` | `Tool`-Registrierung, `Context`, `Client` in Tests | ja | **2.0.0**, exakt gepinnt in `uv.lock:418-419`, Bereich `mcp[cli]>=2.0,<3` in `pyproject.toml:15` | -- |
| `uv` | jeder Lauf (`uv run --no-sync`) | ja | im Projekt eingerichtet | -- |
| AppAPI in Nextcloud | occ-Kommando, Konfigurationslesen, Nutzerliste | ja, in der Testtopologie | Pfade gegen **app_api 34.0.3** verifiziert (`exapp/occ.py:11`, hier zusätzlich für `/api/v1/users`) | -- |
| Docker-Topologie `compose.exapp.yml` | Messaufgabe zur Nutzerliste | in CI ja, lokal laut CLAUDE.md nicht (Linux-Docker fehlt) | -- | Die Messung als CI-Aufgabe mit Marker `integration` planen, nicht als lokale Vorbedingung |

Fehlende Abhängigkeiten ohne Ersatz: keine.
Fehlende mit Ersatz: die lokale Docker-Engine; der Ersatz ist der CI-Job `exapp`.

---

## Paketprüfung

**Diese Phase installiert kein Paket.** CONTEXT.md legt das unter Established Patterns fest
("Das Audit-Log kommt mit der Standardbibliothek aus"), `docs/dependency-audit.md` ist die
zugehörige Entscheidung, und `tests/unit/test_project_layout.py:22-45` hält die
Abhängigkeitsregeln fest. Alles Nötige (`sqlite3`, `hashlib`, `json`, `time`, `asyncio`) ist
Standardbibliothek. Eine Prüfung mit `slopcheck` entfällt mangels Kandidaten.

Sollte ein Plan trotzdem ein Paket vorschlagen, ist das ein Verstoß gegen einen festen
Entscheid und keine Ermessensfrage.

---

## Sicherheitsdomäne

### Zutreffende ASVS-Kategorien

| Kategorie | Trifft zu | Standardmaßnahme in dieser Phase |
|-----------|-----------|----------------------------------|
| V2 Authentifizierung | nein | Diese Phase legt keinen Anmeldeweg an; sie liest eine bereits geprüfte Identität aus `request.state` |
| V3 Sitzungsverwaltung | nein | Kein Sitzungszustand; der Rekorder lebt für eine Anfrage |
| V4 Zugriffskontrolle | ja | Das Prüfkommando ist administrativ. Die Doppelprüfung aus `purge.py:259-272` (`x-origin-ip` mit 404, dann `require_appapi`) ist Pflicht, ebenso das Fehlen einer `<route>` im Manifest |
| V5 Eingabevalidierung | ja | Argumentnamen werden gegen `PARAM_ALLOWLIST` geschnitten; der Client-Name wird geklammert; Optionen des occ-Kommandos werden im Handler noch einmal geprüft, weil das, was AppAPI übergibt, Eingabe ist (`purge.py:63-66`) |
| V6 Kryptografie | ja | `hashlib.sha256` aus der Standardbibliothek. Kein eigenes Verfahren, kein Schlüssel, keine Verschlüsselung des Logs |
| V7 Fehlerbehandlung und Protokollierung | **Kern dieser Phase** | Ins Nextcloud-Log geht nur der Ausnahmetyp, nie die Meldung (`purge.py:158-159`, `verifier.py:212-215`). Ins Audit-Log geht kein Wert und kein Inhalt |

### Bedrohungsmuster für diesen Aufbau

| Muster | STRIDE | Maßnahme |
|--------|--------|----------|
| Das Log als zweite, schlechter geschützte Kopie der Nutzdaten | Information Disclosure | D-06 und der Vertragstest: nur Namen, nie Werte, nie Inhalte. Die Stufe `full` ist in REQUIREMENTS.md ausgeschlossen |
| Ein Aufrufer schreibt erfundene Parameternamen ins Log | Tampering | Schnitt mit `PARAM_ALLOWLIST` (§1) |
| Ein Client-Name mit Steuerzeichen verfälscht die Ausgabe des Prüfkommandos | Tampering | Klammerung wie `exapp/ui/layout.py:506-522` (Falle 8) |
| Das Prüfkommando wird über den PHP-Proxy von aussen erreichbar | Elevation of Privilege | Keine `<route>` im Manifest plus Doppelprüfung (`appinfo/info.xml:266-284`) |
| Volles Volume macht den OAuth-Speicher schreibunfähig | Denial of Service | Obergrenze gegen `used_bytes` plus `incremental_vacuum` (§8), und AUDIT-03 als Prüfkriterium |
| Fail-open lässt das Log unbemerkt verstummen | Repudiation | D-13: Fehlschlag ins Nextcloud-Log, und das Prüfkommando macht die Lücke sichtbar |
| Ein nutzerbezogenes Protokoll läuft ungefragt mit | Compliance und Mitbestimmung | D-14: ab Werk aus, und der 401 beim ersten Start (§9) fällt in dieselbe Richtung |
| Wer die Datei schreiben kann, rechnet die Kette neu | Repudiation | **Nicht abwehrbar.** Gehört als Grenzbeschreibung in den Docstring (D-v1.5-02) |

---

## Annahmenverzeichnis

| # | Annahme | Abschnitt | Risiko, wenn falsch |
|---|---------|-----------|---------------------|
| A1 | `searchDisplayName('')` hinter `/api/v1/users` gibt auf jedem Backend alle Konten zurück, deaktivierte eingeschlossen | §7 | **Hoch.** Ein fehlendes Konto löscht nach D-12 eine ganze Kette. Absicherung: fail-safe in die Löschrichtung, leere Liste ist immer ein Fehler, Messaufgabe im Plan |
| A2 | Die Zeitkosten von 7,2 ms je Eintrag fallen im Linux-Container deutlich niedriger aus | §8 | Gering. Selbst 7,2 ms sind gegenüber einer Nextcloud-Antwort vertretbar; die Nachmessung gehört trotzdem in einen Plan |
| A3 | 227 Byte je Eintrag gelten auch für echte Werkzeugnamen und echte Client-Namen | §8 | Gering. Die Zahl bestimmt nur, wie viele Einträge in 100 MB passen, nicht die Richtigkeit der Obergrenze |
| A4 | `BLOB`-Hashes sparen rund 28 Prozent Zeilengrösse | §4, §8 | Keines. Gerechnet, nicht gemessen; die Entscheidung Hex gegen BLOB steht unter Claudes Ermessen |
| A5 | Der Aufruf über die Ereignisschleife hinweg zeigt `request.state` verlässlich im Kontext | §1, §3 | Gering. `deps._oauth_identity` (`deps.py:230-246`) fährt heute genau diesen Weg im Produktivbetrieb |
| A6 | Der PHP-Proxy streamt den Antwortrumpf des Prüfkommandos ohne Abschneiden auch bei mehreren Megabyte | §6 | Mittel. `timeout => 0` und `stream => true` sprechen dafür; ein Prüfkommando sollte trotzdem eine Zusammenfassung und nicht das ganze Log ausgeben |

---

## Offene Punkte

1. **Die Erlaubnisliste je Werkzeug ist noch nicht zugeschnitten.**
   - Bekannt: die vollständige Parameterliste aller 21 Werkzeuge (§2).
   - Offen: welche Namen aufgenommen werden. Der Zuschnitt steht unter Claudes Ermessen.
   - Empfehlung: als eigene Planaufgabe mit dem Gate zusammen, damit Liste und Prüfung in
     einem Schritt entstehen. Die drei klaren Ausschlüsse (`content` zweimal, `message`)
     als Sperrliste anlegen.

2. **Der Rückgabewert des Prüfkommandos bei gebrochener Kette.**
   - Bekannt: 200 gibt den Rumpf aus und liefert 0; alles andere verwirft den Rumpf und
     liefert 1 (§6).
   - Offen: ob ein Überwachungsskript den Rückgabewert braucht.
   - Empfehlung: 200 plus Rumpf, und die Abwägung in den Docstring. Ein `--json` liefert eine
     maschinenlesbare Fassung ohne einen zweiten Statuscode.

3. **Ob die Obergrenze WAL und SHM mitzählt.**
   - Bekannt: WAL wächst bis rund 4 MB, innerhalb einer grossen Transaktion bis 5,5 MB (§8).
   - Offen: ob 100 MB die Nutzdaten oder alles meinen.
   - Empfehlung: `used_bytes` allein zählen und die rund 6 MB Luft in der Dokumentation
     nennen. Das Löschen in Stapeln von etwa 5.000 Zeilen hält die WAL-Datei klein.

4. **Der Name des Prüfkommandos.**
   - Bekannt: der Namensraum ist `mcp_connector:` (`occ.py:53`).
   - Offen: `mcp_connector:audit:verify`, `mcp_connector:audit-verify` oder
     `mcp_connector:verify-audit`.
   - Empfehlung: Phase 19 legt mit AUDIT-04 ein zweites Kommando zum Lesen und Exportieren
     nach. Also einen Namensraum wählen, der beide trägt, statt zweimal neu zu erfinden.

---

## Projektvorgaben aus CLAUDE.md

- Python 3.13, mcp 2.x, `uv` als Werkzeugkette (das globale Python ist defekt). Jeder Lauf
  über `uv run --no-sync ...` aus dem Repository-Verzeichnis.
- `ruff check .` und `ruff format --check .` über das **ganze** Repository vor dem Push.
- `pyright` im Modus `standard`, `vulture` über `src scripts vulture_whitelist.py` mit voller
  Zuversicht plus begründeter Ausnahmenliste.
- Nach jedem Edit sofort committen und pushen, ohne Rückfrage, ohne Claude-Attribution
  (`includeCoAuthoredBy=false`).
- Code und README auf Englisch, Projektkommunikation auf Deutsch. Keine Em-Dashes, echte
  Umlaute in deutschen Texten.
- Der MCP darf nie mehr sehen als der angemeldete Nutzer; keine zerstörenden Schreibvorgänge.
- Keine neue direkte Abhängigkeit ohne Not (`docs/dependency-audit.md`).
- Keine neuen Routen im Manifest. Was ein Administrator tut, tut er über `occ`.
- Verbotene Wörter in allen öffentlichen Texten, ab dieser Phase auch in Kommentaren und
  Doku, die hier entstehen: revisionssicher, AI-Act-konform, DSGVO-konform, SIEM-zertifiziert.
- Das Wort "archiv" ist in öffentlichen Artefakten gesperrt (Vokabular-Gate).

---

## Quellen

### Primär (HIGH)

Eigener Quelltext, mit Datei und Zeile im Fließtext belegt:
`src/mcp_connector/server/__init__.py`, `src/mcp_connector/oauth/store.py`,
`src/mcp_connector/oauth/verifier.py`, `src/mcp_connector/deps.py`,
`src/mcp_connector/config.py`, `src/mcp_connector/errors.py`,
`src/mcp_connector/exapp/{purge,occ,lifecycle,config_values,admin_settings,middleware,auth}.py`,
`src/mcp_connector/exapp/ui/layout.py`, `src/mcp_connector/oauth/connections.py`,
`src/mcp_connector/nextcloud/{credentials.py,clients/{ocs,dav,caldav,carddav}.py}`,
`src/mcp_connector/entry_exapp.py`, `scripts/check_tool_budget.py`,
`tests/contract/{test_tool_surface,test_no_destructive_calls,test_module_boundaries}.py`,
`tests/conftest.py`, `pyproject.toml`, `uv.lock`, `.github/workflows/ci.yml`,
`appinfo/info.xml`, `docs/uninstall.md`.

Installiertes SDK, mcp 2.0.0 aus `uv.lock:418-419`:
`mcp/server/mcpserver/tools/base.py`, `mcp/server/mcpserver/tools/tool_manager.py`,
`mcp/server/mcpserver/utilities/func_metadata.py`, `mcp/server/mcpserver/context.py`,
`mcp/server/context.py`.

Fremdquelltext, an Tag `v34.0.3` von `nextcloud/app_api` geprüft:
`appinfo/routes.php:72`, `lib/Controller/OCSApiController.php:81-86`,
`lib/Service/ExAppService.php:199-203`, `lib/Controller/OccCommandController.php:36-52`,
`lib/Service/ExAppOccService.php:116-213`,
`lib/Listener/DeclarativeSettings/SetValueListener.php`.

Eigene Messungen vom 2026-08-29, alle im Projekt-venv über `uv run --no-sync`:
Werkzeugliste samt Wrapper- und Kontextnachweis; `params["arguments"]` gegen einen Aufruf mit
gesetztem und ungesetztem Parameter; drei SQLite-Läufe zu Zeilengrösse, Einfügekosten,
Freiliste, `auto_vacuum` und `incremental_vacuum`; `scripts/check_tool_budget.py`.

### Sekundär (MEDIUM)

`nc_py_api` (`nc_py_api/nextcloud.py:365-367`, `nc_py_api/_session.py:187-190`) als zweite,
unabhängige Bestätigung, dass `/apps/app_api/api/v1/users` der übliche Weg für eine ExApp ist.

### Tertiär (LOW)

Keine. Nichts, was diese Recherche trägt, hängt an einer unbestätigten Websuche.

---

## Metadaten

**Confidence im Einzelnen:**
- Erfassungspunkt und Identität: HIGH, am laufenden Stand gemessen.
- Vertragstest: HIGH, die Registrierung ist geprüft, das Muster steht im Repository.
- SQLite-Muster und Pfad: HIGH, vollständig aus dem eigenen Quelltext.
- Kette und Prüfung: HIGH für den Bau, MEDIUM für die Grabsteinregel in der Instanzkette (eine
  Folgerung aus D-02 und D-03, in CONTEXT.md nicht ausgeschrieben).
- Statusklassen und Gründe: HIGH für den Befund (rund 230 flache Wurfstellen, sieben
  Abbildungen), MEDIUM für den Umfang der `guard_tripped`-Stellen.
- occ-Weg: HIGH, an app_api v34.0.3 verifiziert, inklusive der Ausgabe-Falle.
- Konto-Existenz: HIGH für Endpunkt und Berechtigung, **MEDIUM für die Vollständigkeit der
  Antwort** (A1, die einzige Annahme mit hohem Risiko).
- Schalter und D-15: HIGH, die Wand ist im fremden Quelltext belegt.
- Grenzen und Größenmessung: HIGH, dreimal gemessen.
- Testarten und Gates: HIGH, aus `pyproject.toml`, den drei Gate-Dateien und der CI-Datei.
- Budget: HIGH, frisch nachgemessen.

**Recherchedatum:** 2026-08-29
**Gültig bis:** rund 30 Tage. Was altern kann, ist die Fassung von app_api (heute 34.0.3) und
das SDK (mcp 2.0.0); die Befunde am eigenen Quelltext altern erst mit dem nächsten Commit.
