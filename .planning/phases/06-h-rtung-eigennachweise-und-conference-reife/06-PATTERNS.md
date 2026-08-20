# Phase 6: Härtung, Eigennachweise und Conference-Reife - Pattern Map

**Mapped:** 2026-08-20
**Files analyzed:** 27 (5 neu, 22 geändert)
**Analogs found:** 25 / 27

Diese Datei beantwortet genau eine Frage: **Wovon kopiert jede neue oder geänderte Datei ihr
Muster?** Sie ersetzt nicht 06-RESEARCH.md (das sagt, *was* gebaut wird), sondern liefert die
konkreten Fundstellen, aus denen der Planer die Aktionen schreibt.

Der Kernbefund der Musterprüfung deckt sich mit dem der Recherche: **in dieser Phase entsteht
genau ein Modul ohne echtes Analog** (`oauth/cimd.py`, weil es der erste Outbound-Request in
eine fremde Vertrauensdomäne ist). Alles andere hat ein Vorbild im Repo, oft ein sehr genaues,
und in vier Fällen ist das Vorbild sogar dieselbe Funktion, die nur eine Frage mehr bekommt.

---

## File Classification

### Code

| Neue/geänderte Datei | Rolle | Datenfluss | Nächstes Analog | Match |
|----------------------|-------|------------|-----------------|-------|
| `src/mcp_connector/oauth/cimd.py` (NEU) | service (Transport + Validierung) | request-response (outbound) | `src/mcp_connector/nextcloud/http.py` (Client-Politik) + `src/mcp_connector/exapp/responses.py` (Grenz-Muster) | partial (2 Halb-Analoga, kein Ganzes) |
| `src/mcp_connector/oauth/provider.py` | provider/policy (AS-Hälfte) | request-response | dieselbe Datei, `register_client` (Teilregistrierung, Zeilen 355-428) | exact (Selbst-Analog) |
| `src/mcp_connector/oauth/registry.py` | config/policy | transform (pure) | dieselbe Datei, `ClientPolicy` + `redirect_uri_allowed` | exact (Selbst-Analog) |
| `src/mcp_connector/oauth/consent.py` | route/controller | request-response | dieselbe Datei, `_refuse` (Zeilen 217-243) | exact (Selbst-Analog) |
| `src/mcp_connector/oauth/metadata.py` | config/document | request-response | dieselbe Datei, `dcr_enabled`-Durchreichung + Zeile 202 | exact (Selbst-Analog) |
| `src/mcp_connector/oauth/store.py` | model/storage | CRUD | dieselbe Datei, `_add_missing_columns` (Zeilen 1415-1433) | exact (Selbst-Analog) |
| `src/mcp_connector/exapp/responses.py` | utility | streaming (bounded read) | dieselbe Datei, `bounded_body` (Zeilen 67-96) | exact (Zwilling) |
| `src/mcp_connector/exapp/ui/consent.py` | component (SSR) | request-response | dieselbe Datei, `consent_page`/`unverified` (Zeilen 183-253) | exact (Selbst-Analog) |
| `src/mcp_connector/exapp/ui/strings.py` | config (Texte) | — | dieselbe Datei, `CONSENT_WARNING_*` (Zeilen 250-255) | exact |

### Tests

| Neue/geänderte Datei | Rolle | Datenfluss | Nächstes Analog | Match |
|----------------------|-------|------------|-----------------|-------|
| `tests/unit/test_oauth_cimd.py` (NEU) | test (unit) | request-response (respx) | `tests/unit/test_appapi_credentials.py` Zeilen 372-400 (respx) + `tests/unit/test_oauth_registry.py` (Parametrize-Katalog) | role-match |
| `tests/unit/test_oauth_registry.py` | test (unit) | transform | dieselbe Datei, Zeilen 148-183 | exact |
| `tests/unit/test_oauth_provider.py` | test (unit) | CRUD + request-response | dieselbe Datei, `build`/`registration`/`CURSOR_URIS` (Zeilen 83-128) | exact |
| `tests/unit/test_oauth_consent.py` | test (unit) | request-response | dieselbe Datei (Starlette-TestClient-Muster) | exact |
| `tests/unit/test_oauth_metadata.py` | test (unit) | request-response | dieselbe Datei | exact |
| `tests/unit/test_oauth_store.py` | test (unit) | CRUD | dieselbe Datei | exact |
| `tests/unit/test_oauth_ui.py` | test (unit) | SSR | dieselbe Datei | exact |
| `tests/unit/test_exapp_responses.py` | test (unit) | streaming | dieselbe Datei (`bounded_body`-Tests) | exact |
| `tests/unit/test_project_layout.py` | test (gate) | — | dieselbe Datei, Zeilen 22-46 | exact |

### Manifest, Topologie, Doku, Messungen

| Neue/geänderte Datei | Rolle | Datenfluss | Nächstes Analog | Match |
|----------------------|-------|------------|-----------------|-------|
| `appinfo/info.xml` | config (Manifest) | — | dieselbe Datei, Zeilen 346-363 | exact |
| `.env.exapp.example` | config | — | dieselbe Datei (bestehende `NC_MCP_OAUTH_*`-Zeilen) | exact |
| `compose.exapp.yml` | config (Topologie) | — | dieselbe Datei, Zeile 46 | exact |
| `docs/oauth-setup.md` | docs | — | dieselbe Datei, Abschnitt "Cursor: refused until 0.1.2" (Zeilen 603-638) | exact |
| `docs/client-setup.md` | docs | — | dieselbe Datei, Zeilen 508-531 | exact |
| `docs/exapp-install.md` | docs | — | dieselbe Datei, Zeilen 476-531 | exact |
| `06-XX-MEASUREMENTS.md` (NEU, mehrfach) | docs (Beleg) | — | `git show d3eb627^:.planning/phases/05-.../05-07-MEASUREMENTS.md` und `05-08-MEASUREMENTS.md` | exact (aus Historie) |
| `docs/conference-demo.md` (NEU) | docs (Runbook) | — | `docs/store-submission.md` (Runbook-Form) + `scripts/oauth_flow_check.py` (Schritt-Docstring) | role-match |
| `docs/conference-talk.md` (NEU) | docs (Entwurf) | — | **keines** | none |
| `README.md` / `.de.md` / `.fr.md` | docs (dreisprachig) | — | dieselbe Dateigruppe (bestehende Parallelstruktur) | exact |
| `CHANGELOG.md` | docs | — | dieselbe Datei, `## [Unreleased]` / `## [0.1.2]` | exact |

---

## Pattern Assignments

### 1. `src/mcp_connector/oauth/cimd.py` (NEU, service, outbound request-response)

**Kein Ganz-Analog.** Es gibt im Repo keinen Outbound-Request in eine fremde Domäne: jeder
bestehende Call geht zur eigenen Nextcloud (`NC_MCP_URL`, Phase-01-Entscheidung). Deshalb setzt
sich das Muster aus drei Halb-Analoga zusammen, und der Planer muss alle drei nennen.

**Analog A: die Client-Politik.** `src/mcp_connector/nextcloud/http.py:68-81` ist der einzige
Ort im Repo, an dem ein `httpx.AsyncClient` gebaut wird. Der neue Fetch **kopiert die Haltung,
nicht das Objekt** (Anti-Pattern der Recherche: `shared_client()` darf ein CIMD-Fetch nicht
benutzen, weil er sich keinen Pool mit einem Credential-Pfad teilt):

```python
# src/mcp_connector/nextcloud/http.py:68-81
def shared_client() -> httpx.AsyncClient:
    """Return the client bound to the running event loop, creating it on first use."""
    loop = asyncio.get_running_loop()
    client = _clients.get(loop)
    if client is None or client.is_closed:
        client = httpx.AsyncClient(
            timeout=httpx.Timeout(10.0, connect=5.0, read=30.0),
            follow_redirects=False,
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
            headers={"User-Agent": USER_AGENT},
            cookies=NoCookieJar(),
        )
        _clients[loop] = client
    return client
```

Was davon zu übernehmen ist, und was nicht:

| Eigenschaft | Übernehmen? | Grund |
|-------------|-------------|-------|
| `follow_redirects=False` | **ja, wörtlich** | Hausregel und für CIMD zusätzlich Sicherheitsgrenze (ein Redirect ist ein zweites, ungeprüftes Ziel) |
| `timeout=httpx.Timeout(..., connect=5.0)` | ja, mit eigenen Werten (5 s / 5 s) | derselbe Stil, andere Zahl: der Fetch sitzt in einem Browser-Request |
| `limits=httpx.Limits(...)` | ja, aber `max_connections=1, max_keepalive_connections=0` | ein Einzelabruf braucht keinen Pool |
| `cookies=NoCookieJar()` | ja | derselbe Grund wie dort: der Prozess ist geteilt, eine fremde Domäne darf nichts hinterlassen |
| `headers={"User-Agent": USER_AGENT}` | ja, dieselbe Konstante importieren | ein zweiter User-Agent wäre eine zweite Wahrheit |
| pro-Loop-Cache (`_clients`) | **nein** | ein Einzelabruf pro Aufruf, kein Prozess-Zustand (D-20) |

Ebenfalls aus dieser Datei: der **Docstring-Stil "drei bewusste Einstellungen"**
(`nextcloud/http.py:1-14`, jede Einstellung mit ihrem Grund und ihrer Threat-ID). Das ist die
Form, in der `cimd.py` seine Grenzen erklären soll.

**Analog B: das Grenz-Muster.** `src/mcp_connector/exapp/responses.py:67-96` ist der
Request-Zwilling dessen, was `cimd.py` auf der Response-Seite braucht. Der Zähler, der Abbruch
vor dem vollen Lesen, die zwei getrennten Exceptions und der Satz "nothing of the body is ever
logged" sind zu übernehmen:

```python
# src/mcp_connector/exapp/responses.py:42-47
class BodyTooLarge(Exception):
    """More body arrived than the caller of :func:`bounded_body` is willing to read."""


class BodyUnreadable(Exception):
    """The body could not be read to its end, so there is nothing to decide on."""


# src/mcp_connector/exapp/responses.py:84-96
    chunks: list[bytes] = []
    seen = 0
    try:
        async for chunk in request.stream():
            seen += len(chunk)
            if seen > max_bytes:
                raise BodyTooLarge
            chunks.append(chunk)
    except BodyTooLarge:
        raise
    except Exception as exc:
        raise BodyUnreadable from exc
    return b"".join(chunks)
```

Empfehlung an den Planer: den Zwilling `bounded_response(response, max_bytes)` **in
`exapp/responses.py` neben `bounded_body` legen**, nicht in `cimd.py`. Begründung aus der
Datei selbst (Zeilen 1-16): dieses Modul ist der erklärte Ort für "die eine Stelle, an der ein
Größenlimit implementiert ist", und zwei Größenlimits in zwei Modulen sind genau die Kopie, die
dieses Modul einmal abgeschafft hat. `cimd.py` importiert es dann.

**Analog C: die Refusal-Semantik.** `oauth/registry.py:138-171` (`redirect_uri_allowed`) ist
das Vorbild für eine reine Prüffunktion, die `bool` liefert, nie wirft, und deren Docstring die
Refusals einzeln begründet:

```python
# src/mcp_connector/oauth/registry.py:153-171
    parts = urlsplit((value or "").strip())
    if parts.scheme not in ("https", "http"):
        return False
    if parts.fragment:
        return False
    try:
        host = parts.hostname
        port = parts.port
    except ValueError:
        # A malformed host or port. An address this library cannot take apart is not one
        # a browser and this server would agree about either.
        return False
    if not host or parts.username or parts.password:
        return False
    if port is not None and not 0 < port <= 65535:
        return False
    if parts.scheme == "https":
        return True
    return host.lower() in LOOPBACK_HOSTS
```

Das ist exakt die Form, in die `is_cimd_client_id` aus 06-RESEARCH.md gehört: `urlsplit`, das
`try/except ValueError` um `hostname`/`port`, und **kein Logging des geprüften Werts**.

**Logger-Muster** (für die Refusal-Protokollierung), aus `oauth/registry.py:79` und
`exapp/responses.py:39`:

```python
logger = logging.getLogger("mcp_connector.oauth.registry")
```

Also `logging.getLogger("mcp_connector.oauth.cimd")`. Und die Regel, wie geloggt wird, steht in
`provider.py:308-312`: **die Art des Fehlers, kein Wert der Anfrage.**

```python
# src/mcp_connector/oauth/provider.py:308-312
        except Exception as exc:
            # A store that cannot be opened or read is not a reason to let a client in
            # (D-37). The kind of the failure is logged, no value of the request is.
            logger.error("the client lookup has no store: %s", type(exc).__name__)
            return None
```

---

### 2. `src/mcp_connector/oauth/provider.py` (provider, request-response) — der CIMD-Zweig

**Analog: dieselbe Datei, `register_client` (Zeilen 355-428).** Das ist kein Ausweichen: die
Teilregistrierung ist der Vorgang, den der CIMD-Zweig wiederholt (fremde `redirect_uris` durch
D-35 filtern, das Ergebnis als `clients`-Zeile schreiben, `allowed` aus der Policy).

**Die Einstiegsstelle** (Zeilen 314-337, hier steht heute `row is None -> return None`):

```python
# src/mcp_connector/oauth/provider.py:314-337
        if row is None:
            return None

        client = _client_information(row.metadata_json, client_id)
        if client is None:
            return None

        if not row.allowed:
            return None

        addresses = [str(uri) for uri in client.redirect_uris or []]
        if not self._policy.allows(client_id, addresses):
            return None

        if _has_expired(row.registered_at, row.last_used_at):
            # The credentials first, then the row (WR-04): ``authorizations`` points at
            # ``clients`` with ON DELETE CASCADE, so the delete would take the ciphertext of
            # every app password under this client along and leave the credentials working
            # at Nextcloud with no record that they exist.
            await self._hand_back_client(store, client_id)
            await store.delete_client(client_id)
            return None

        return client
```

Der Zweig gehört **zwischen `if row is None:` und `client = _client_information(...)`**, damit
der gemeinsame Rest (`allowed`, `policy.allows`, `_has_expired`) unverändert weiterläuft. Das
ist Pattern 1 der Recherche und der Grund, warum die vier AUTH-07-Punkte gratis greifen.

**Pitfall 4 hat hier seine Zeile:** `_has_expired` liegt *nach* dem Zweig und würde eine
CIMD-Zeile mit ihren `authorizations` löschen. Der Plan muss hier eine bewusste Entscheidung
treffen (Ausnahme für CIMD-Zeilen oder zwei getrennte Fristen), nicht schweigen.

**Das Filter- und Schreibmuster** für `_resolve_cimd`, wörtlich aus `register_client`
(Zeilen 403-428):

```python
# src/mcp_connector/oauth/provider.py:403-428
        registrable = [
            uri for uri in client_info.redirect_uris or [] if redirect_uri_allowed(str(uri))
        ]
        if not registrable:
            raise RegistrationError("invalid_redirect_uri", _REDIRECT_RULE)
        # Written into the object, not only into the record: the handler echoes this very
        # object back, so a client that reads the answer sees what it may come back to.
        client_info.redirect_uris = registrable
        addresses = [str(uri) for uri in registrable]

        client_info.scope = REGISTERED_SCOPE
        secret = client_info.client_secret
        store = await self.store()
        await store.save_client(
            client_info.client_id,
            metadata_json=client_info.model_dump_json(exclude={"client_secret"}),
            secret_hash=token_hash(secret) if secret else None,
            allowed=self._policy.allows(client_info.client_id, addresses),
        )
```

Für CIMD gilt davon: dieselbe List-Comprehension mit `redirect_uri_allowed`, dasselbe
`model_dump_json`, dasselbe `allowed=self._policy.allows(...)`. **Zwei Abweichungen,
die der Plan explizit machen muss:**

1. `secret_hash=None` immer (CIMD-Clients sind per Draft public, Shared-Secret-Verfahren sind
   verboten). Vorbild für die "kein Secret"-Lesart: `client_secret_hash` (Zeilen 339-353), das
   `None` ausdrücklich als "dieser Client hat kein Secret" liest.
2. Kein `raise RegistrationError` — `get_client` gibt `None` zurück statt zu werfen (D-37, die
   ganze Funktion tut das an fünf Stellen). Eine Exception aus `get_client` wäre eine neue
   Fehlerform in vier Endpunkten.

**Scope:** `client_info.scope = REGISTERED_SCOPE` gilt für CIMD genauso, mit derselben
Begründung wie im Docstring Zeilen 379-393 (die angekündigte und die gewährte Menge müssen
dieselbe sein, sonst antwortet der eigene Server `invalid_scope`).

---

### 3. `src/mcp_connector/oauth/registry.py` (config/policy, transform) — Schalter + Loopback-Regel

**Analog: dieselbe Datei, vollständig.** Sie ist 214 Zeilen lang und ist die Bauanleitung für
beide Ergänzungen.

**Der Schalter** kopiert die drei bestehenden Zeilen 52-60 und 129-135:

```python
# src/mcp_connector/oauth/registry.py:52-60
#: Dynamic client registration, globally. On in the shipped state, because success criteria
#: 1 and 2 are about connecting Claude.ai and ChatGPT without an administrator (D-35).
ENV_DCR = "NC_MCP_OAUTH_DCR"

#: Only explicitly listed clients may authorize. Off in the shipped state.
ENV_ALLOWLIST_ONLY = "NC_MCP_OAUTH_ALLOWLIST_ONLY"

#: The list itself: client ids or redirect URIs, separated by commas.
ENV_ALLOWED_CLIENTS = "NC_MCP_OAUTH_ALLOWED_CLIENTS"

# src/mcp_connector/oauth/registry.py:129-135
def client_policy(env: Mapping[str, str] | None = None) -> ClientPolicy:
    """Read the three switches. The environment is a parameter, as everywhere here."""
    return ClientPolicy(
        dcr_enabled=_switch(env, ENV_DCR, default=True),
        allowlist_only=_switch(env, ENV_ALLOWLIST_ONLY, default=False),
        allowed=_entries(env, ENV_ALLOWED_CLIENTS),
    )
```

Also: `ENV_CIMD = "NC_MCP_OAUTH_CIMD"` in den Konstantenblock, ein viertes Feld auf dem
`@dataclass(frozen=True, slots=True, repr=False)`, `__all__` (Zeilen 40-50) alphabetisch
ergänzen, und die fail-closed-Ableitung aus Pattern 2 der Recherche:

```python
        dcr = _switch(env, ENV_DCR, default=True)
        cimd_enabled=_switch(env, ENV_CIMD, default=True) and dcr,
```

`_switch` (Zeilen 174-198) wird **unverändert benutzt**: es kennt schon den Default-an-Fall
(`ENV_DCR` war der erste), es behandelt einen Leerwert als ungesetzt und einen Tippfehler als
"Default behalten plus Warnung". Ein zweiter Parser wäre eine zweite Wahrheit.

**Die Loopback-Regel** setzt sich neben `redirect_uri_allowed` (Zeilen 138-171) und benutzt
dessen Konstante:

```python
# src/mcp_connector/oauth/registry.py:68-71
#: The addresses the OAuth 2.1 security guidance exempts from the https rule, because a
#: native client on a desktop has no certificate for its own callback (D-35). ``urlsplit``
#: reports the IPv6 host without its brackets, so the set carries the unbracketed form.
LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})
```

Diese Konstante ist die Antwort auf die "Falle" aus Pattern 4 der Recherche (§7.3 nennt nur
IP-Literale, Claude Code schickt `localhost`): D-35 lässt bereits alle drei Hosts registrieren,
also ist `LOOPBACK_HOSTS` die konsistente Menge für `loopback_match`. Der Vergleich bleibt
sonst exakt (Schema, Host, Pfad, Query), was dem Stil von `redirect_uri_allowed` entspricht:
jede Lockerung wird einzeln benannt und begründet.

**Der Docstring-Auftrag** aus Zeilen 1-31 gilt fort: das Modul erklärt, *warum* es eine Policy
ist und nicht eine Bedingung, und listet die vier Enforcement-Punkte namentlich. Wer
`cimd_enabled` hinzufügt, ergänzt dort einen Satz, sonst driftet die Erklärung vom Code weg.

---

### 4. `src/mcp_connector/oauth/consent.py` (route, request-response) — die eine `validate_redirect_uri`-Stelle

**Analog: dieselbe Funktion, `_refuse` (Zeilen 217-243).** Das ist der einzige Ort im eigenen
Code, an dem ein Request-Wert gegen die Registrierung verglichen wird:

```python
# src/mcp_connector/oauth/consent.py:233-243
    raw = params.get("redirect_uri")
    try:
        requested = AnyUrl(str(raw)) if raw else None
        address = client.validate_redirect_uri(requested)
    except (InvalidRedirectUriError, ValidationError, ValueError):
        return _page(errors.error_page("E5", env=env, client=_name(client)))
    if not redirect_uri_allowed(str(address)):
        # A registration from before this rule, or one written another way. The address is
        # checked where it is used and not only where it was accepted (T-03-41).
        return _page(errors.error_page("E5", env=env, client=_name(client)))
    return None
```

Zwei Muster daraus sind bindend:

1. **Die Reihenfolge:** erst SDK-Vergleich, dann die eigene Regel. Die RFC-8252-§7.3-Lockerung
   gehört in den `except InvalidRedirectUriError`-Zweig oder davor als Vorbereitung, aber die
   Prüfung `redirect_uri_allowed(str(address))` danach bleibt stehen: eine Lockerung des
   Ports darf die D-35-Prüfung des Ergebnisses nicht überspringen.
2. **Ein Fehlerbild für alles.** `E5` für jeden Redirect-Fehler, kein neuer Code, keine
   Auskunft darüber, welche Prüfung fiel. Die Begründung steht in `_no_client_page`
   (Zeilen 246-267): "an answer that separates them is an information service for whoever is
   guessing client ids (T-03-47)".

**Das Flag-Muster für die Consent-Seite** (Pattern 5 der Recherche), aus Zeilen 394-404:

```python
# src/mcp_connector/oauth/consent.py:394-404
    addresses = [str(uri) for uri in client.redirect_uris or []]
    return consent_page(
        _name(client),
        client.client_id,
        row.redirect_uri,
        user,
        row.flow_id,
        store.form_token(row.flow_id, purpose=crypto.PURPOSE_CONSENT),
        unverified=not provider.policy.listed(client.client_id, addresses),
        env=env,
    )
```

Ein zweites Keyword-Argument (Herkunft = CIMD, plus die zwei Hostnamen) ist derselbe
Mechanismus. Der Aufrufer berechnet, die Seite rendert nur.

---

### 5. `src/mcp_connector/oauth/metadata.py` (config/document) — das Advertising

**Analog: dieselbe Datei, die `dcr_enabled`-Durchreichung.** Zeile für Zeile das Vorbild:

```python
# src/mcp_connector/oauth/metadata.py:106-120
def metadata_routes(
    env: Mapping[str, str] | None = None, *, dcr_enabled: bool = True
) -> list[Route]:
    """Build the three discovery routes against one environment.
    ...
    ``dcr_enabled`` is the switch plan 03-05 hands in from the registry policy (AUTH-07).
    When dynamic client registration is off, the document stops advertising an endpoint that
    would refuse every call. ...
    """
```

```python
# src/mcp_connector/oauth/metadata.py:196-210
    metadata.scopes_supported = [TOOL_SCOPE, REFRESH_SCOPE]
    # RFC 9207: the authorization response carries the issuer, which is what lets a client
    # notice a mix-up attack between two authorization servers it talks to.
    metadata.authorization_response_iss_parameter_supported = True

    document = metadata.model_dump(mode="json", exclude_none=True)
    # RFC 8414 compares the issuer byte for byte ...
    document["issuer"] = base
    return document
```

Zwei Details, die aus diesem Ausschnitt folgen und die ein Plan sonst übersieht:

- **`exclude_none=True` heißt: `None` verschwindet aus dem Dokument.** Genau darum funktioniert
  `metadata.client_id_metadata_document_supported = cimd_enabled or None` aus 06-RESEARCH.md.
  Das ist kein Trick, sondern das etablierte Verhalten dieser Funktion.
- Das Feld muss **nach** `build_metadata` gesetzt werden, wie die drei Felder darüber, weil das
  SDK es nicht setzt (verifizierte Negativ-Grep der Recherche).

Der zweite Teil: `metadata_routes(..., cimd_enabled=...)` braucht einen Aufrufer. Der Ort ist
`entry_exapp.build_exapp_app`, wo heute `dcr_enabled` aus der Policy übergeben wird — der Plan
muss diese Stelle mitnennen, sonst bleibt der Schalter unverbunden (Pitfall 5).

---

### 6. `src/mcp_connector/oauth/store.py` (model/storage, CRUD) — Spalten für Herkunft und Frist

**Analog: `_add_missing_columns` (Zeilen 1415-1433).** Das ist die vollständige Bauanleitung
für eine idempotente Schema-Erweiterung in diesem Projekt, inklusive der Begründung, warum
`CREATE TABLE IF NOT EXISTS` allein nicht genügt:

```python
# src/mcp_connector/oauth/store.py:1415-1433
def _add_missing_columns(conn: sqlite3.Connection) -> None:
    """Bring a file written by an earlier build up to the schema above.

    ``CREATE TABLE IF NOT EXISTS`` does nothing to a table that already exists, so a store
    file from a development build before plan 03-06 would keep an ``auth_codes`` table
    without ``redirect_uri_explicit`` and fail on the first insert. One ``ALTER TABLE`` with
    the same default as the schema is the whole migration, and it is idempotent because it
    asks first. Nothing here rewrites a row: a column that is added with a default is what
    every existing code carried anyway, an authorization request that named its return
    address.
    """
    columns = {row[1] for row in conn.execute("PRAGMA table_info(auth_codes)")}
    if "redirect_uri_explicit" not in columns:
        conn.execute(
            "ALTER TABLE auth_codes ADD COLUMN redirect_uri_explicit INTEGER NOT NULL DEFAULT 1"
        )
    columns = {row[1] for row in conn.execute("PRAGMA table_info(authorizations)")}
    if "cleanup_at" not in columns:
        conn.execute("ALTER TABLE authorizations ADD COLUMN cleanup_at INTEGER")
```

Das zweite Beispiel (`cleanup_at`, nullable ohne Default) ist das genaue Vorbild für
`cimd_fetched_at` / `cimd_expires_at`: eine bestehende DCR-Zeile hat keine Werte und braucht
keine, `NULL` heißt "keine CIMD-Zeile". **Keine Datenmigration**, exakt wie im Docstring
begründet.

Der Rest der Kette, alles in derselben Datei:

| Stelle | Zeilen | Was zu tun ist |
|--------|--------|----------------|
| `SCHEMA`, Tabelle `clients` | 158-166 | die zwei Spalten in den Schema-Text (für eine neue Datei) |
| `ClientRow` | 246-262 | zwei Felder; der maskierende `__repr__` bleibt |
| `save_client` | 427-453 | `ON CONFLICT ... DO UPDATE SET`-Liste erweitern (Achtung: `registered_at` wird bewusst nicht überschrieben) |
| `load_client` | 455-473 | die zwei Spalten in die `SELECT`-Liste **und** in den `ClientRow`-Aufbau |

Der `SCHEMA`-Docstring (Zeilen 150-157) erklärt zusätzlich, wann eine Änderung greift ("a new
table arrives with a restart and not in the middle of a request", LO-02) — das ist die Aussage,
die in die Messdatei gehört, wenn der Store nach dem Rebuild ein neues Schema hat.

Und der FK-Zwang, den Pitfall 3 nennt, steht wörtlich hier:

```sql
-- src/mcp_connector/oauth/store.py:170 und :183
  client_id TEXT NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
```

---

### 7. `src/mcp_connector/exapp/ui/consent.py` + `ui/strings.py` (component, SSR)

**Analog: `consent_page` (Zeilen 183-253) mit dem `unverified`-Block.** Das ist genau die
Stelle, an die die zwei neuen Spec-Pflichten gehören (Hostname-Anzeige, Loopback-Warnung):

```python
# src/mcp_connector/exapp/ui/consent.py:214-230
    name = layout.client_name(client_name)
    blocks = [
        layout.paragraph(strings.CONSENT_IDENTITY.format(user=user, host=_host(env))),
    ]
    if unverified:
        blocks.append(
            layout.callout("warning", strings.CONSENT_WARNING_TITLE, strings.CONSENT_WARNING_BODY)
        )
    blocks.extend(
        [
            layout.detail_list(
                [
                    (strings.CONSENT_DETAIL_APP_NAME, name),
                    (strings.CONSENT_DETAIL_REDIRECT, redirect_uri),
                    (strings.CONSENT_DETAIL_CLIENT_ID, client_id),
                ]
            ),
```

Konkret zu kopieren:

- ein zweiter `if`-Block mit `layout.callout("warning", ...)` für die Loopback-Warnung, direkt
  neben dem bestehenden. Kein neues Rendering-Primitiv.
- der Hostname als **weiterer Eintrag in `detail_list`**, nicht als neuer Absatz. Die
  `redirect_uri` steht dort schon vollständig ("never shortened", Docstring Zeilen 196-198).
- kein `logo_uri`. Der Docstring dieses Moduls (Zeilen 8-12) sagt, warum jeder gezeigte Wert
  Angreifereingabe ist und was ihn sicher macht (`layout` säubert und escaped an einer Stelle);
  ein Bild von fremder Domäne fällt nicht darunter.

**Texte** kommen in `ui/strings.py`, im Muster von Zeilen 250-255:

```python
# src/mcp_connector/exapp/ui/strings.py:250-255
CONSENT_WARNING_TITLE = "Unverified client"

CONSENT_WARNING_BODY = (
    "This app registered itself automatically. Nextcloud has not verified it. Only approve "
    "it if you started this connection yourself."
)
```

Beachten: `__all__` (ab Zeile 30) ist alphabetisch sortiert und wird von vulture gelesen. Und
Pitfall 10 der Recherche verbietet hier das Wort "verified"/"verifiziert" im **neuen** Text —
der bestehende benutzt es als Negation ("has not verified it"), was zulässig bleibt.

---

### 8. `tests/unit/test_oauth_cimd.py` (NEU, test unit)

**Analog A: respx-Muster**, aus `tests/unit/test_appapi_credentials.py:372-386`. Das ist die
einzige Form, in der in diesem Repo ein Outbound-Call getestet wird:

```python
# tests/unit/test_appapi_credentials.py:371-386
@pytest.mark.anyio
@respx.mock
async def test_a_read_in_the_basic_mode_sends_an_authorization_header() -> None:
    route = respx.get(f"{BASE_URL}/ocs/v2.php/cloud/user").mock(
        return_value=httpx.Response(200, json={})
    )
    creds = Credentials(BASE_URL, USER, SECRET)

    async with httpx.AsyncClient(follow_redirects=False) as client:
        await ocs.ocs_get(client, creds, "/cloud/user")

    sent = route.calls.last.request
    expected = base64.b64encode(f"{USER}:{SECRET}".encode()).decode()
    assert sent.headers["authorization"] == f"Basic {expected}"
```

Drei Dinge daraus sind für AUTH-09 tragend:

1. `@pytest.mark.anyio` + `@respx.mock` als Dekoratorpaar (das Projekt nutzt anyio, nicht
   pytest-asyncio-Marker).
2. `route.calls.last.request` ist die Art, wie man **das Gesendete** prüft. Genau so wird das
   IP-Pinning belegt: `sent.url.host` ist die IP, `sent.headers["host"]` der Originalname,
   `sent.extensions["sni_hostname"]` der Originalname.
3. `respx.mock(assert_all_called=False)` (Muster aus `test_caldav_client.py:149`) ist die Form
   für die wichtigsten Negativtests: **keine Route getroffen** beweist "kein Netzwerkverkehr",
   und das ist die Formulierung, die der Negativtest-Katalog verlangt (Schalter aus, kein
   https, DCR aus).

**Analog B: der Parametrize-Katalog**, aus `tests/unit/test_oauth_registry.py:148-183`. Der
SSRF-Katalog aus 06-RESEARCH.md hat 22 Zeilen und gehört genau in diese Form, positiv und
negativ getrennt:

```python
# tests/unit/test_oauth_registry.py:148-183
@pytest.mark.parametrize(
    "uri",
    [
        "https://claude.ai/api/mcp/auth_callback",
        ...
        "http://[::1]:5000/cb",
    ],
)
def test_https_and_loopback_http_are_accepted(uri: str) -> None:
    assert registry.redirect_uri_allowed(uri) is True


@pytest.mark.parametrize(
    "uri",
    [
        "http://claude.ai/api/mcp/auth_callback",
        ...
        "",
    ],
)
def test_everything_else_is_refused(uri: str) -> None:
    """The spec exception is loopback for native clients, and nothing else (D-35)."""
    assert registry.redirect_uri_allowed(uri) is False
```

**Analog C: der Fake-Resolver.** Für den Rebinding-Test gibt es kein Analog im Repo (siehe "No
Analog Found"), aber die zulässige Injektionsform steht in
`tests/unit/test_oauth_provider.py:91-107`: eine Callable wird hereingegeben, nichts wird
gemonkeypatcht:

```python
# tests/unit/test_oauth_provider.py:91-107
def opener(subject: OAuthStore) -> Callable[[], Awaitable[OAuthStore]]:
    async def open_it() -> OAuthStore:
        return subject

    return open_it


def build(tmp_path: Path, **env: str) -> tuple[provider_module.NextcloudOAuthProvider, OAuthStore]:
    """A provider on a real store file, with the policy of the given environment."""
    subject = OAuthStore(tmp_path / "oauth.sqlite3", KEY)
    policy = registry.client_policy(ENV | env)
    return (
        provider_module.NextcloudOAuthProvider(
            env=ENV | env, policy=policy, store_provider=opener(subject)
        ),
        subject,
    )
```

Konsequenz für `cimd.py`: **die Auflösefunktion ist ein Parameter mit Default**, nicht ein
Modulaufruf. Nur so ist der Zwei-Antworten-Resolver testbar, ohne `anyio.getaddrinfo` zu
patchen. Diese API-Entscheidung gehört in den Plan, nicht in die Testdatei.

**Kopfzeilen-Muster:** jede Testdatei beginnt mit einem Docstring, der die abgedeckten Threats
nennt und sagt, was *nicht* passiert (`test_oauth_provider.py:1-15`: "Nothing here starts a
container or opens a socket"). Für `test_oauth_cimd.py` ist das die Zeile "kein Paket geht ins
Netz, respx antwortet".

---

### 9. `tests/unit/test_oauth_provider.py` (geändert) — CIMD-Zweig und Cursor-Belege

**Analog: dieselbe Datei.** Zwei Fundstellen sind direkt wiederzuverwenden.

Die Cursor-Fixture existiert schon und ist die Brücke zu CLIENT-04:

```python
# tests/unit/test_oauth_provider.py:80-89
#: What Cursor sends to ``/register`` in one body, measured against staging on 2026-08-16
#: (03-09-MEASUREMENTS.md, run 4). The first entry is a private-use URI scheme, which D-35
#: refuses and BL-04 keeps refusing; the other two are registrable.
CURSOR_URIS = [
    "cursor://anysphere.cursor-mcp/oauth/callback",
    "https://www.cursor.com/agents/mcp/oauth/callback",
    "http://localhost:8787/callback",
]
CURSOR_REGISTRABLE = CURSOR_URIS[1:]
```

Und `registration()` (Zeilen 110-128) ist das Muster für eine `OAuthClientInformationFull`-
Fixture. Für CIMD braucht der Plan das Geschwister `cimd_document()`, das dasselbe JSON in der
Form des echten Claude-Code-Dokuments liefert (06-RESEARCH.md, Pattern 4) — mit derselben
Kommentarpflicht: **wo der Wert gemessen wurde.**

Der Testname-Stil dieser Datei ist bindend und ungewöhnlich lang, weil er den Satz enthält, den
der Test beweist: `test_a_registration_is_refused_with_its_reason_while_the_switch_is_off`.
Neue Tests folgen dem, z. B. `test_a_url_client_id_is_refused_while_dcr_is_off`.

**Der Gate-Test für den Schalternamen** liegt in `test_oauth_registry.py:213-220` und **bricht
mit der Änderung**, weil er die Anzahl der Variablennamen zählt:

```python
# tests/unit/test_oauth_registry.py:213-220
def test_the_variable_names_live_in_the_constant_block_and_nowhere_else() -> None:
    """The rule of config.py: a name is a module constant, never a literal at a use site."""
    source = inspect.getsource(registry)
    body = "\n".join(
        line for line in source.splitlines() if not line.lstrip().startswith(("#", "*"))
    )

    assert body.count('"NC_MCP_OAUTH') == 3
```

Die `3` wird zu `4`. Ein Plan, der das nicht nennt, produziert einen roten Lauf, der wie ein
Regressionsfund aussieht.

---

### 10. `appinfo/info.xml`, `.env.exapp.example`, `compose.exapp.yml` (config)

**Analog: `appinfo/info.xml:346-363`**, das Vorbild inklusive des Kommentars, der erklärt,
warum die Defaults leer bleiben:

```xml
<!-- appinfo/info.xml:344-363 -->
		  - The three switches of AUTH-07 are declared for the administrator who needs
		  - them, with their shipped defaults empty so nothing here overrides the code:
		  - AppAPI drops a variable with an empty value instead of exporting it blank.
		-->
		<environment-variables>
			<variable>
				<name>NC_MCP_OAUTH_DCR</name>
				<display-name>Allow clients to register themselves</display-name>
				<description>Dynamic client registration (RFC 7591). On unless set to off. Claude.ai and ChatGPT need it to connect without an administrator.</description>			</variable>
```

Zu kopieren: die Tab-Einrückung, die drei Kindelemente, und der Satzbau der `description`
("On unless set to off." plus der Grund). Der `NC_MCP_OAUTH_CIMD`-Eintrag muss zusätzlich die
Kopplung an DCR nennen, sonst liest ein Admin sie nicht.

**Ohne diese Deklaration reicht der Deploy-Daemon die Variable nicht durch** (in Phase 3 gegen
AppAPI 34.0.0 gemessen). Das ist der teuerste stille Fehler dieser Phase.

**`compose.exapp.yml:46`** ist eine Einzeilenänderung mit einem Beleg-Zwang aus Pitfall 6:

```yaml
    image: nextcloud:34-apache      # -> nextcloud:34.0.3-apache
```

Der gleitende Tag ist genau die Falle: das lokale Image unter `34-apache` trägt 34.0.2.1. Die
Messdatei nennt `occ status`, nicht den Tag.

---

### 11. `06-XX-MEASUREMENTS.md` (NEU, mehrfach) — die Beweisform dieses Projekts

**Analog: `git show d3eb627^:.planning/phases/05-hardening-und-store-einreichung/05-07-MEASUREMENTS.md`.**
Die Dateien sind gelöscht und liegen nur in der Historie; der Planer muss den `git show`-Befehl
in den Plan schreiben, sonst erfindet der Executor die Form neu.

Kopf und Topologie-Tabelle, wörtlich als Vorlage:

```markdown
# 05-07 Messprotokoll: Open WebUI gegen den Connector

Datum des Laufs: 2026-08-19, 18:02 bis 18:20 UTC. Rechner: der Entwicklungsrechner aus
05-RESEARCH.md "Environment Availability". Alles unten ist aus einem Lauf, nicht aus dem
Quellcode abgeleitet; wo eine Aussage aus dem Quellcode kommt, steht das dabei.

## Topologie des Laufs

| Was | Wert |
|-----|------|
| ExApp-Topologie | `compose.exapp.yml`, Projekt `nc-mcp-exapp`, neu angefahren nach der Prozedur aus STATE.md |
| Nextcloud | `nextcloud:34-apache`, erreichbar unter `http://127.0.0.1:8081` (Caddy, nur Loopback) |
| Connector | `mcp_connector` 0.1.0, Image-Digest `sha256:dd28c591b139...`, `occ app_api:app:list` meldet `mcp_connector (MCP Connector): 0.1.0 [enabled]` |
| `NC_MCP_PUBLIC_URL` | `http://127.0.0.1:8081/exapps/mcp_connector` |
| Owner-Instanzen | `nc-mcp-test` und `findling-nextcloud` liefen durch, unberuehrt (kein Kommando dieses Laufs nennt sie) |
```

Vier weitere Muster aus derselben Datei und aus `05-08`:

1. **Rohbeleg pro Behauptung**, nicht Prosa. In 05-07 ist das der Container-Log-Block mit vier
   Zeilen (`POST /mcp 401`, `GET /.well-known/... 200`, `POST /register 201`) und danach eine
   Tabelle der geschriebenen Store-Zeile, Feld für Feld.
2. **Die Eigenheit der Messumgebung wird benannt**, nicht versteckt: der Loopback-Weiterleiter
   im fremden Container steht mit Gegenprobe im Protokoll ("derselbe URL-Aufruf liefert vom
   Host und aus dem Container dasselbe Dokument").
3. **Die Konventionen des Protokolls stehen oben** (05-08): `occ` steht für
   `docker exec -u www-data nc-mcp-exapp-nc php occ`, und **kein Credential steht im Dokument,
   auch kein Wegwerf-Credential (T-05-39)**.
4. **Das Unvorhergesagte bekommt einen eigenen Absatz** ("Nicht vorhergesagt und darum hier
   festgehalten: Open WebUI registriert sich als vertraulicher Client").

Die Pflichtzeilen dieser Phase, über das Muster hinaus:

| Messdatei | Pflichtangabe, die das Muster noch nicht hat |
|-----------|---------------------------------------------|
| CLIENT-05 (Loopback-Port) | der genommene Port **je Lauf, mindestens drei Läufe**, plus ein separater Lauf mit gesetztem `MCP_OAUTH_CALLBACK_PORT` |
| CLIENT-04 (Cursor) | Cursor-Version **und** Image-Digest des Connectors (Pitfall 8: 0.1.1 hat die Teilregistrierung nicht) |
| EXAPP-06 (UI-Smoke) | `occ status` als **erste Zeile**, das Konto, unter dem gemessen wurde (Admin), und der Store-Cache-Schritt (Überschreiben mit timestamp 0, nie Löschen) |

---

### 12. `docs/oauth-setup.md`, `docs/client-setup.md`, `docs/exapp-install.md` (docs)

**Analog: `docs/oauth-setup.md`, Abschnitt "Cursor: refused until 0.1.2, registrable since"
(Zeilen 603-638).** Das ist die Musterform für einen Absatz, der einen Befund ersetzt, ohne die
Historie zu tilgen:

```markdown
### Cursor: refused until 0.1.2, registrable since

Cursor 3.2.16 needs no button either, it picks up `~/.cursor/mcp.json` on its own. Up to
and including 0.1.1 its registration was refused with `400 invalid_redirect_uri`, and
Cursor printed our sentence verbatim in its log: `redirect_uris must use https, except
loopback addresses of native clients`.
...
**Since 0.1.2 an inadmissible entry is dropped instead of refusing the registration.** ...
The change is covered by unit tests; a live run against Cursor 3.2.16 is still open.
```

Fünf Eigenschaften dieses Absatzes, die zu kopieren sind:

1. Der Zustand steht **im Titel** ("refused until 0.1.2, registrable since"), nicht erst im
   Text. Für CLIENT-04 wird daraus ein Titel, der das Live-Ergebnis nennt.
2. Der alte Befund bleibt stehen und wird datiert ("Measured against the live instance on
   2026-08-16").
3. Der letzte Satz nennt den offenen Rest ehrlich: "a live run against Cursor 3.2.16 is still
   open" — **genau dieser Satz ist das, was CLIENT-04 löscht und ersetzt.**
4. Was sich *nicht* geändert hat, wird ausdrücklich gesagt ("Nothing about the rule itself
   moved"). Für CLIENT-05 heißt das: D-35 steht, nur der Port-Vergleich lockert.
5. Roh-Zahlen im Code-Block, nie im Fließtext.

**Für `docs/exapp-install.md` ist das Analog der eigene Abschnitt "Nextcloud 34 has no
interface for installing or removing an ExApp" (Zeilen 476-531).** Er trägt bereits die
Vorwärts-Zeile, die EXAPP-06 füllt oder korrigiert:

```markdown
## Nextcloud 34 has no interface for installing or removing an ExApp

**Fixed upstream in Nextcloud 34.0.3** (verified 2026-08-20: the finding below is
[nextcloud/app_api#971](...) and [nextcloud/server#61709](...), resolved by
[server PR 62276](...), backported to 34.0.3 and confirmed by the original reporter). On
34.0.2 and earlier everything below still applies, and occ remains the reliable path on
every version.

Measured on **2026-08-19** against Nextcloud 34.0.2 with AppAPI 34.0.0, while looking for the
Install button of this app:
```

Diese Struktur ist die Vorlage für **beide** Ausgänge aus Open Question 1: der Absatz wird
entweder mit einer gemessenen Bestätigung ("verified on 34.0.3.2 on 2026-08-XX: the Install
button is shown") ergänzt, oder mit einem negativen Befund plus der md5-Gegenprobe. Der
Titelsatz "Fixed upstream" darf so lange nicht stehen bleiben, wie er unbelegt ist: das ist die
Locked Decision "Doku sagt GENAU das Gemessene".

**Die Dreisprachigkeit trennt sauber** (Pitfall 9): `docs/*.md` ist einsprachig kanonisch,
`README.md` / `README.de.md` / `README.fr.md` und der Store-Text ziehen zusammen nach. Beleg
dafür, dass die Parallelstruktur existiert und wie sie aussieht: die drei READMEs tragen
identische Überschriftenfolgen (`## Status`, `### OAuth 2.1`, `## Get it from the Nextcloud App
Store`, ...). Ein Plan, der eine README-Zeile ändert, nennt alle drei Dateien.

---

### 13. `docs/conference-demo.md` (NEU, docs/Runbook) — CONF-01

**Analog A: die Runbook-Form von `docs/store-submission.md`.** Überschriftenfolge als Vorlage:
`## Where this stands` → `## What the artifacts are` → `## One time setup (per app id), done`
→ `## Release runbook for a follow up release` → `## Pre submission checklist` →
`## Not needed, common misunderstandings`. Übersetzt auf die Demo: Stand, was gezeigt wird,
Einmal-Aufbau, Drehbuch, Checkliste vorher, was bewusst nicht gezeigt wird.

**Analog B: der Schritt-Docstring von `scripts/oauth_flow_check.py:1-30`**, weil er schon jetzt
das Drehbuch der Verbindungsstrecke ist und die Kopier-Kommandos im Code-Block führt:

```python
# scripts/oauth_flow_check.py:11-24
    export HP_SHARED_KEY="$(openssl rand -hex 32)"
    docker compose -p nc-mcp-exapp -f compose.exapp.yml up -d --wait
    bash scripts/bootstrap_exapp.sh
    set -a && . ./.env.exapp && set +a
    uv run --no-sync python scripts/oauth_flow_check.py \
        http://127.0.0.1:8081/exapps/mcp_connector

The seven steps of the first run are the seven questions the plan asks, in order: the 401
of the MCP route, the three discovery documents over both proxy paths, the canonical root
paths, dynamic client registration, the authorization request with PKCE and the consent
screen, the code exchange with its measured duration, and one tool call over the full
chain with the token that came out of it.
```

Das ist zugleich der Hinweis, dass die Demo **nichts neu bauen muss**: `oauth_flow_check.py`
deckt Verbindung und Tool-Aufruf ab, `acceptance_all_tools.py` (Docstring Zeilen 1-27) deckt
den Werkzeug-Durchlauf ab. Die Demo ist das Drehbuch um zwei existierende Skripte plus die
Per-User-Seite und den Widerruf aus Phase 4.

Owner-Regel, die hier greift: **Kopier-Texte immer im Code-Block.** Beide Skript-Docstrings
machen es genau so.

---

## Shared Patterns

### A. Fail-closed als Rückgabewert, nicht als Exception

**Quelle:** `src/mcp_connector/oauth/provider.py:296-337` (fünf `return None` in einer
Funktion), `src/mcp_connector/oauth/registry.py:117-126`, `src/mcp_connector/exapp/responses.py:115-138`
**Gilt für:** `cimd.py`, den `get_client`-Zweig, jede neue Prüffunktion

```python
# src/mcp_connector/exapp/responses.py:134-138
    try:
        return await request.form()
    except Exception:
        logger.warning("a submitted form could not be parsed")
        return None
```

Die Regel dieses Projekts (D-37): eine Funktion auf einem Request-Pfad liefert einen Wert oder
eine Absage, **nie eine Exception in einen Handler**. `cimd.py` darf intern ein privates
`_Refused` benutzen (so steht es im Recherche-Beispiel), muss es aber an der Modulgrenze in
`None` verwandeln.

### B. Umgebung ist ein Parameter, niemals `os.environ`

**Quelle:** `oauth/registry.py:129-135`, `oauth/metadata.py:106-120`, `tests/unit/test_oauth_registry.py:26-28`
**Gilt für:** jeden neuen Schalter, jede neue Factory, jeden Test

```python
# tests/unit/test_oauth_registry.py:26-28
def policy(**env: str) -> registry.ClientPolicy:
    """A policy from an environment a test writes out in full, never from os.environ."""
    return registry.client_policy(env)
```

Konsequenz für Phase 6: die Konstanten des CIMD-Fetch (5120 Bytes, 5 s) sind **Modulkonstanten
ohne Env-Schalter** (Open Question 5 der Recherche), aber der Policy-Schalter kommt aus einem
übergebenen Mapping.

### C. Kein modul-globaler veränderlicher Zustand (D-20)

**Quelle:** `src/mcp_connector/nextcloud/http.py:63-65` (die eine erlaubte Ausnahme, und sie
ist ein `WeakKeyDictionary` pro Event-Loop), `oauth/metadata.py:32-34` (Factory-Muster)
**Gilt für:** den CIMD-Cache

Die Entscheidung der Recherche (Cache als Spalte auf `clients`) folgt direkt aus dieser Regel.
Wer stattdessen einen Prozess-Cache will, braucht die Closure-Form der Routen-Fabrik
(`store_opener`), nicht ein Modul-Dict.

### D. Ein Fehlerbild, keine Auskunft über die gefallene Prüfung

**Quelle:** `oauth/consent.py:246-267`
**Gilt für:** `consent.py`, `provider.py`, jede neue Absage

```python
# src/mcp_connector/oauth/consent.py:249-254
    """Which of the three pages a refused client gets, decided without asking the store.

    ``get_client`` answers ``None`` for unknown, blocked, unlisted and expired alike, and
    that is deliberate: an answer that separates them is an information service for whoever
    is guessing client ids (T-03-47). The page is therefore chosen from the policy, which
    is the administrator's own configuration and tells the caller nothing about any client:
```

Für CIMD heißt das: ein Client, dessen Dokument nicht geholt werden konnte, bekommt dasselbe
Bild wie ein unbekannter. Die Recherche verlangt zusätzlich, dass die Allowlist-Absage bei CIMD
"mit derselben Seite wie bei DCR" endet — das ist genau dieser Code, unverändert.

### E. Drosselung statt Negativ-Cache

**Quelle:** `src/mcp_connector/oauth/throttle.py:105-149` und `:299-345`
**Gilt für:** den CIMD-Fetch (Flooding mit unbekannten URL-`client_id`)

```python
# src/mcp_connector/oauth/throttle.py:105-124 (Auszug)
CLASS_TOKEN = "token"  # noqa: S105 - the name of a path class, not a credential
CLASS_REGISTER = "register"
CLASS_REVOKE = "revoke"
CLASS_AUTHORIZE = "authorize"
...
CLASS_CONNECT_START = "connect-start"
CLASS_AUTHORIZE_START = "authorize-start"
```

Der Kommentar zu `CLASS_AUTHORIZE_START` (Zeilen 123-124 plus `consent.py:200-211`) ist das
Vorbild: eine Klasse existiert, damit ein Missbrauch der einen Route nicht die andere schließt.
Der `/authorize`-Start ist bereits mit `count_all=True` und `FLOW_LIMIT` gedrosselt — der Plan
muss prüfen, ob das für den CIMD-Fetch **schon genügt** (der Fetch hängt an genau dieser
Route), bevor er eine neunte Klasse erfindet. Empfehlung: erst messen, dann Klasse.

Wichtig aus der Recherche: **kein Negativ-Cache**, der Draft verbietet das Cachen von Fehlern
wörtlich. `Throttled` ist der zulässige Ort, `save_client` nicht.

### F. Docstring als Entscheidungsprotokoll

**Quelle:** überall, am dichtesten `oauth/registry.py:1-31`, `oauth/provider.py:364-398`,
`nextcloud/http.py:27-54`
**Gilt für:** jede geänderte Datei

Der Stil dieses Repos ist ungewöhnlich und konsistent: der Docstring nennt **das Problem, den
Messwert und die verworfene Alternative**, mit Referenz (D-xx, T-xx-xx, BL-xx, Pitfall-Nummer).
Ein Plan, der nur Code beschreibt, produziert hier einen Fremdkörper. Beispiel für die Dichte,
die erwartet wird:

```python
# src/mcp_connector/oauth/provider.py:364-377 (Auszug)
        **Why one forbidden address no longer refuses the whole registration (BL-04).**
        The rule of D-35 is unchanged and so is the reasoning behind it; what changed is
        what happens to the entries around a refused one. Cursor sends three addresses in
        one body, ``cursor://anysphere.cursor-mcp/oauth/callback`` next to an https one and
        a loopback one, and an all or nothing field check turned that into a 400 with our
        rule quoted in the client's own log: a whole class of clients stayed out over an
        entry it would not have had to use.
```

### G. Gates, die eine Änderung mitzieht

**Quelle:** `tests/unit/test_project_layout.py:22-46`, `tests/unit/test_oauth_registry.py:213-220`
**Gilt für:** jeden Plan dieser Phase

```python
# tests/unit/test_project_layout.py:29-34
def test_httpx_is_pinned_for_our_own_client_code(pyproject: dict) -> None:
    deps = pyproject["project"]["dependencies"]
    assert any(dep.startswith("httpx>=") for dep in deps), (
        "our own HTTP code uses httpx, because respx mocks httpx and not httpx2"
    )
```

Dieser Test ist der geschriebene Grund, warum `cimd.py` `httpx` und nicht `httpx2` benutzt. Die
drei Gates, die eine Phase-6-Änderung berührt:

| Gate | Datei | Wirkung |
|------|-------|---------|
| Variablennamen-Zähler | `test_oauth_registry.py:213-220` | `3` → `4` mit `ENV_CIMD` |
| httpx-Pin | `test_project_layout.py:29-34` | bleibt grün, ist die Begründung für den Client |
| `vulture_whitelist.py` | Repo-Wurzel | neue `__all__`-Konstanten (Strings, Klassen) können hier landen müssen |

Dazu die Owner-Regeln, die kein Test abdeckt und die vor jedem Push laufen: Vokabular-Gate
("archiv" in öffentlichen Artefakten), `ruff check .` **und** `ruff format --check .` über das
ganze Repo, `CHANGELOG.md` unter `## [Unreleased]` für alles Nutzerrelevante.

---

## No Analog Found

| Datei / Baustein | Rolle | Datenfluss | Grund |
|------------------|-------|------------|-------|
| `oauth/cimd.py`, die IP-Pinning-Hälfte (`extensions={"sni_hostname": ...}`, URL auf IP-Literal umschreiben) | service | outbound request-response | Es gibt im Repo keinen Request an ein anderes Ziel als die konfigurierte Nextcloud. Der Planer nimmt hier das verifizierte Code-Beispiel aus 06-RESEARCH.md (Pattern 3, `_fetch_pinned`) und nicht ein Repo-Analog. Die Recherche verlangt zusätzlich, den ersten Plan-Task gegen einen lokalen TLS-Server zu verifizieren, weil der Code gelesen, aber nie ausgeführt wurde |
| Rebinding-Test mit Zwei-Antworten-Resolver | test | — | Kein Test im Repo hat einen austauschbaren Resolver. Injektionsform: `test_oauth_provider.py:91-107` (Callable als Parameter). Die Testidee selbst kommt aus 06-RESEARCH.md, Pitfall 2 |
| `docs/conference-talk.md` (Folien + Sprechzettel) | docs | — | Das Repo hat kein Präsentationsartefakt. Empfehlung der Recherche: HTML/Markdown im Repo, damit kein Paket-Legitimacy-Gate ausgelöst wird. Vorlage für Ton und Inhalt sind die vier Differenzierer aus CONTEXT.md und die Statuszeilen von `README.md:25-56` |
| SSRF-Zielprüfung (`ipaddress`-Konjunktion) | utility | transform | Kein Analog, aber die Regel ist in 06-RESEARCH.md gegen Python 3.13.13 **gemessen** (Flag-Matrix, drei belegte Lücken). Sie ist zu übernehmen, wie sie dort steht, und die Formprüfung daneben kopiert `registry.redirect_uri_allowed` |

---

## Metadata

**Analog search scope:** `src/mcp_connector/oauth/`, `src/mcp_connector/exapp/`,
`src/mcp_connector/nextcloud/`, `tests/unit/`, `docs/`, `scripts/`, `appinfo/`,
Repo-Wurzel (`compose.exapp.yml`, `CHANGELOG.md`, `README*.md`), plus die gelöschten
MEASUREMENTS-Dateien aus `d3eb627^` in der Git-Historie.

**Files scanned:** 78 Python-Module unter `src/`, 76 Testdateien, 15 Doku-Seiten,
9 Skripte, 8 historische Messprotokolle (Namensliste), Manifest und Compose-Datei.

**Vollständig gelesene Analoga:** `oauth/registry.py`, `oauth/metadata.py`,
`exapp/responses.py`, `nextcloud/http.py`, `tests/unit/test_oauth_registry.py`.
**Gezielt gelesene Abschnitte:** `oauth/provider.py:280-459`, `oauth/store.py:140-270`,
`:420-493`, `:1396-1440`, `oauth/consent.py:200-268`, `:380-424`,
`oauth/throttle.py:84-150`, `:299-345`, `exapp/ui/consent.py:1-253`,
`exapp/ui/strings.py` (Konstanten), `tests/unit/test_oauth_provider.py:1-175`,
`tests/unit/test_appapi_credentials.py:360-400`, `tests/unit/test_project_layout.py:1-60`,
`appinfo/info.xml:340-368`, `docs/oauth-setup.md:603-645`, `docs/client-setup.md:508-535`,
`docs/exapp-install.md:476-537`.

**Pattern extraction date:** 2026-08-20
</content>
</invoke>
