"""Walk the whole OAuth 2.1 flow against a running ExApp topology and print what happened.

This is the repeatable half of the live proof of plan 03-08. Everything the unit suite can
only assert in process is measured here through the real chain::

    client  ->  reverse proxy  ->  HaRP  ->  ExApp container  ->  Nextcloud

Run it against the topology of ``compose.exapp.yml``::

    export HP_SHARED_KEY="$(openssl rand -hex 32)"
    docker compose -p nc-mcp-exapp -f compose.exapp.yml up -d --wait
    bash scripts/bootstrap_exapp.sh
    set -a && . ./.env.exapp && set +a
    uv run --no-sync python scripts/oauth_flow_check.py \
        http://127.0.0.1:8081/exapps/mcp_connector
    uv run --no-sync python scripts/oauth_flow_check.py \
        http://127.0.0.1:8081/exapps/mcp_connector --measure

The seven steps of the first run are the seven questions the plan asks, in order: the 401
of the MCP route, the three discovery documents over both proxy paths, the canonical root
paths, dynamic client registration, the authorization request with PKCE and the consent
screen, the code exchange with its measured duration, and one tool call over the full
chain with the token that came out of it. ``--measure`` adds Success Criterion 5, the
number of Nextcloud round trips an MCP call costs, and the threshold of our own throttle.

**The one shortcut, and why it is here.** A browser is the actor of two steps: the
Nextcloud sign in of the Login Flow v2 and the "Approve access" button of our own consent
screen. :func:`sign_in` drives the first one over plain HTTP with the account password of
a throwaway test user, exactly as a browser would: it asks for the sign in page, posts the
form with the anti forgery value Nextcloud rendered, and presses "Grant access". This
exists for the test topology and nowhere else. No module under ``src/`` contains a login
automation, no product code ever sees a user password, and ``tests/unit/test_oauth_abuse``
keeps a gate over ``src/`` that says so.

Nothing here changes the instance beyond what it creates itself: one client registration,
one authorization, one note, and it hands all three back at the end.
"""

import argparse
import asyncio
import base64
import hashlib
import json
import os
import re
import secrets
import subprocess
import sys
import time
import urllib.parse
import uuid
from collections.abc import AsyncIterator, Callable, Mapping, Sequence
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

import httpx
import httpx2
from mcp import Client
from mcp.client.streamable_http import streamable_http_client

__all__ = [
    "Connection",
    "connect",
    "list_tools",
    "nextcloud_requests",
    "register_client",
    "revoke",
    "sign_in",
    "tool_call",
]

#: The app id is frozen (docs/app-id-freeze.md), so the routes of the topology are
#: constants here rather than interpolations.
MCP_SUFFIX = "/mcp"
PRM_SUFFIX = "/.well-known/oauth-protected-resource/mcp"
OPENID_SUFFIX = "/.well-known/openid-configuration"
AS_SUFFIX = "/.well-known/oauth-authorization-server"

#: The two canonical paths on the domain root. They belong to Nextcloud, which answers 404
#: for both, and they only reach this app through the two reverse proxy rules of
#: ``deploy/Caddyfile`` (03-RESEARCH.md, pitfall 2).
ROOT_PRM = "/.well-known/oauth-protected-resource/exapps/mcp_connector/mcp"
ROOT_AS = "/.well-known/oauth-authorization-server/exapps/mcp_connector"

#: The second way into the same container: the PHP proxy of AppAPI, measured in phase 2.
PHP_PROXY_PREFIX = "/apps/app_api/proxy/mcp_connector"

#: A return address this run never listens on. It is registered, matched exactly by the
#: server and read back out of the redirect; nothing is served there.
REDIRECT_URI = "http://127.0.0.1:41999/callback"

#: What the registration calls itself. It shows up on the consent screen and, through the
#: user agent of the sign in, under "Devices and sessions" in Nextcloud.
CLIENT_NAME = "OAuth flow check"

#: The audience of every token this run asks for (RFC 8707).
SCOPES = "nextcloud offline_access"

#: The container of the throwaway topology whose access log answers Success Criterion 5.
NEXTCLOUD_CONTAINER = "nc-mcp-exapp-nc"

#: The health check of that container, which writes one access log line every five seconds
#: and is not traffic anybody caused.
HEALTHCHECK = "GET /status.php"

#: How many MCP calls one measurement averages over. Small on purpose: the number this
#: measures is a ratio, not a load profile.
MEASURE_CALLS = 5

#: How far past the throttle of ``oauth/throttle.py`` (ten refusals per window) the flood
#: is allowed to count before it gives up looking for a 429.
FLOOD_LIMIT = 20

TIMEOUT = httpx.Timeout(30.0, read=60.0)


@dataclass(frozen=True, slots=True)
class Connection:
    """One finished OAuth connection, with everything a later step needs to use or end it."""

    base: str
    client_id: str
    client_secret: str
    access_token: str
    refresh_token: str
    user: str


class CheckFailed(RuntimeError):
    """A step did not answer the way the specification and this deployment require."""


def report(step: str, method: str, path: str, status: int, **fields: object) -> None:
    """One line per measured request: what was asked, what came back, and the headers."""
    extra = " | ".join(f"{key}={value}" for key, value in fields.items() if value not in ("", None))
    line = f"[{step}] {method} {path} -> {status}"
    print(f"{line} | {extra}" if extra else line)


def note(step: str, text: str) -> None:
    """A line that is a finding rather than a request."""
    print(f"[{step}] {text}")


def pkce() -> tuple[str, str]:
    """A verifier and its S256 challenge, the only code challenge method this server takes."""
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return verifier, base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def request_token_of(html: str) -> str:
    """The anti forgery value Nextcloud renders into every page of its own."""
    match = re.search(r'data-requesttoken="([^"]+)"', html)
    if match is None:
        raise CheckFailed("the Nextcloud page carried no requesttoken")
    return match.group(1)


def login_flow_state(html: str) -> dict[str, Any]:
    """The state Nextcloud hands to its own login flow pages, as the page carries it."""
    match = re.search(r'id="initial-state-core-loginFlowAuth" value="([^"]+)"', html)
    if match is None:
        return {}
    decoded = json.loads(base64.b64decode(match.group(1)))
    return decoded if isinstance(decoded, dict) else {}


def hidden_field(html: str, name: str) -> str:
    """One hidden form value out of a page this server rendered."""
    match = re.search(rf'<input type="hidden" name="{re.escape(name)}" value="([^"]*)">', html)
    if match is None:
        raise CheckFailed(f"the rendered form carried no {name} field")
    return match.group(1)


def detail_value(html: str, term: str) -> str:
    """One value out of the definition list of a page this server rendered."""
    match = re.search(rf"<dt>{re.escape(term)}</dt><dd class=\"mono\">([^<]*)</dd>", html)
    if match is None:
        raise CheckFailed(f"the rendered page carried no {term!r} entry")
    return match.group(1)


def sign_in(nc: str, user: str, password: str, login_url: str) -> None:
    """Complete a Nextcloud Login Flow v2 sign in without a browser (test topology only).

    Three requests, and each of them is what a browser sends: the auth picker page of the
    running flow, the sign in form of Nextcloud, and the "Grant access" button of the flow.
    The account password never leaves this process and never reaches this project's server:
    Nextcloud authenticates the user on its own pages, which is the whole point of the flow
    (T-03-30). It exists so that a plan can prove the chain end to end without a human, and
    it lives in ``scripts/`` because it must never be reachable from the product.
    """
    with httpx.Client(base_url=nc, follow_redirects=True, timeout=TIMEOUT) as browser:
        picker = browser.get(login_url)
        if picker.status_code != 200:
            raise CheckFailed(f"the sign in page answered {picker.status_code}")
        state = login_flow_state(picker.text)
        grant_url = str(state.get("loginRedirectUrl") or "")
        if not grant_url:
            raise CheckFailed("the sign in page named no grant address")

        form = browser.get("/login")
        request_token = request_token_of(form.text)
        signed_in = browser.post(
            "/login",
            data={
                "user": user,
                "password": password,
                "requesttoken": request_token,
                "timezone": "UTC",
                "timezone_offset": "0",
            },
            headers={"requesttoken": request_token, "Referer": f"{nc}/login", "Origin": nc},
            follow_redirects=False,
        )
        if signed_in.status_code != 303:
            raise CheckFailed(f"the sign in answered {signed_in.status_code}, not a redirect")

        grant = browser.get(grant_url)
        # The grant page carries no state of its own in Nextcloud 34; the value is the one
        # the auth picker named, and it is what the button posts back.
        state_token = login_flow_state(grant.text).get("stateToken") or state.get("stateToken", "")
        granted = browser.post(
            "/login/v2/grant",
            data={"stateToken": state_token},
            headers={
                "requesttoken": request_token_of(grant.text),
                "Referer": grant_url,
                "Origin": nc,
            },
            follow_redirects=False,
        )
        if granted.status_code != 200:
            raise CheckFailed(f"the grant answered {granted.status_code}")


def register_client(base: str, *, name: str = CLIENT_NAME, step: str = "step 4") -> dict[str, Any]:
    """Register this run as a client of the authorization server (RFC 7591)."""
    with httpx.Client(timeout=TIMEOUT) as client:
        response = client.post(
            f"{base}/register",
            json={
                "client_name": name,
                "redirect_uris": [REDIRECT_URI],
                "grant_types": ["authorization_code", "refresh_token"],
                "response_types": ["code"],
                "token_endpoint_auth_method": "none",
                "scope": SCOPES,
            },
        )
    document = response.json() if response.content else {}
    report(
        step,
        "POST",
        "/register",
        response.status_code,
        cache_control=response.headers.get("cache-control"),
        client_id=str(document.get("client_id", ""))[:12] + "...",
    )
    if response.status_code != 201:
        raise CheckFailed(f"the registration answered {response.status_code}, not 201")
    if response.headers.get("cache-control") != "no-store":
        raise CheckFailed("the registration answer may be cached")
    return document


def connect(
    base: str,
    nc: str,
    user: str,
    password: str,
    *,
    name: str = CLIENT_NAME,
    verbose: bool = False,
) -> Connection:
    """Walk register, authorize, sign in, approve and exchange, and return the connection.

    This is the whole client half of the specification, driven by hand so that every step
    can be measured. The MCP SDK client speaks the same sequence; what it cannot do is
    press the two buttons a person presses, which is why this function exists.
    """
    document = register_client(base, name=name, step="step 4" if verbose else "connect")
    client_id = str(document["client_id"])
    client_secret = str(document.get("client_secret") or "")
    verifier, challenge = pkce()
    state = secrets.token_urlsafe(16)

    with httpx.Client(timeout=TIMEOUT, follow_redirects=False) as client:
        authorize = client.get(
            f"{base}/authorize",
            params={
                "response_type": "code",
                "client_id": client_id,
                "redirect_uri": REDIRECT_URI,
                "code_challenge": challenge,
                "code_challenge_method": "S256",
                "state": state,
                "scope": SCOPES,
                "resource": f"{base}{MCP_SUFFIX}",
            },
        )
        if verbose:
            report("step 5", "GET", "/authorize", authorize.status_code)
        if authorize.status_code != 302:
            raise CheckFailed(f"the authorization request answered {authorize.status_code}")
        handoff = urllib.parse.urlsplit(authorize.headers["location"])
        parameters = urllib.parse.parse_qs(handoff.query)
        flow_id = parameters["flow"][0]
        login_url = parameters["login"][0]

        sign_in(nc, user, password, login_url)

        screen = client.get(f"{base}/authorize/consent", params={"flow": flow_id, "step": "wait"})
        if verbose:
            report(
                "step 5",
                "GET",
                "/authorize/consent",
                screen.status_code,
                cache_control=screen.headers.get("cache-control"),
                signed_in=user in screen.text,
            )
        if screen.status_code != 200:
            raise CheckFailed(f"the consent screen answered {screen.status_code}")
        confirm = hidden_field(screen.text, "confirm")

        approved = client.post(
            f"{base}/authorize/consent",
            data={"flow": flow_id, "confirm": confirm, "decision": "approve"},
        )
        if approved.status_code != 302:
            raise CheckFailed(f"the approval answered {approved.status_code}, not a redirect")
        returned = urllib.parse.parse_qs(urllib.parse.urlsplit(approved.headers["location"]).query)
        if verbose:
            report(
                "step 5",
                "POST",
                "/authorize/consent",
                approved.status_code,
                code="present" if returned.get("code") else "missing",
                state="matches" if returned.get("state") == [state] else "differs",
                iss=returned.get("iss", [""])[0],
            )
        if not returned.get("code"):
            raise CheckFailed("the redirect carried no authorization code")
        if returned.get("state") != [state]:
            raise CheckFailed("the redirect carried another state")
        if returned.get("iss") != [base]:
            raise CheckFailed("the redirect carried no issuer or the wrong one")

        started = time.monotonic()
        exchanged = client.post(
            f"{base}/token",
            data={
                "grant_type": "authorization_code",
                "code": returned["code"][0],
                "redirect_uri": REDIRECT_URI,
                "client_id": client_id,
                "code_verifier": verifier,
                "resource": f"{base}{MCP_SUFFIX}",
            },
        )
        elapsed = time.monotonic() - started
        payload = exchanged.json() if exchanged.content else {}
        if verbose:
            report(
                "step 6",
                "POST",
                "/token",
                exchanged.status_code,
                cache_control=exchanged.headers.get("cache-control"),
                fields=",".join(sorted(payload)),
                seconds=f"{elapsed:.2f}",
            )
        if exchanged.status_code != 200:
            raise CheckFailed(f"the code exchange answered {exchanged.status_code}: {payload}")
        if elapsed >= 5.0:
            raise CheckFailed(f"the code exchange took {elapsed:.2f}s, a connector waits ten")

    return Connection(
        base=base,
        client_id=client_id,
        client_secret=client_secret,
        access_token=str(payload["access_token"]),
        refresh_token=str(payload.get("refresh_token") or ""),
        user=user,
    )


def revoke(connection: Connection, *, token: str = "") -> int:
    """End one connection through ``/revoke``, the way a client ends it (RFC 7009)."""
    body = {"token": token or connection.refresh_token, "client_id": connection.client_id}
    if connection.client_secret:
        body["client_secret"] = connection.client_secret
    with httpx.Client(timeout=TIMEOUT) as client:
        response = client.post(f"{connection.base}/revoke", data=body)
    return response.status_code


async def list_tools(base: str, token: str) -> set[str]:
    """The tool surface over the full chain, asked with an OAuth bearer."""
    async with _session(base, token) as client:
        return {tool.name for tool in (await client.list_tools()).tools}


async def tool_call(base: str, token: str, name: str, arguments: Mapping[str, Any]) -> Any:
    """One tool call over the full chain, asked with an OAuth bearer."""
    async with _session(base, token) as client:
        return await client.call_tool(name, dict(arguments))


def payload_of(result: Any) -> dict[str, Any]:
    """The compact JSON a tool answers with, or a failure that names the error."""
    if result.is_error:
        raise CheckFailed(f"the tool call ended in an error: {texts_of(result)!r}")
    texts = texts_of(result)
    if not texts:
        raise CheckFailed("the tool answered without any text content")
    decoded = json.loads(texts[0])
    if not isinstance(decoded, dict):
        raise CheckFailed("the tool did not answer with an object")
    return decoded


def texts_of(result: Any) -> list[str]:
    return [c.text for c in result.content if getattr(c, "text", None) is not None]


@asynccontextmanager
async def _session(base: str, token: str) -> AsyncIterator[Client]:
    """An MCP session over Streamable HTTP, authenticated with one bearer.

    The transport client of the SDK carries the header, which is what the SDK's own OAuth
    client provider does once it has a token. Everything past that header is the deployed
    chain: the reverse proxy, HaRP, the container, the token verifier and Nextcloud.
    """
    url = base.rstrip("/") + MCP_SUFFIX
    async with httpx2.AsyncClient(
        headers={"Authorization": f"Bearer {token}"},
        timeout=httpx2.Timeout(30.0, read=120.0),
    ) as http_client:
        transport = streamable_http_client(url, http_client=http_client)
        async with Client(transport) as client:
            yield client


def nextcloud_requests() -> list[str]:
    """Every access log line of the Nextcloud container so far, health check aside.

    ``docker logs`` is the access log of this image: the Apache of ``nextcloud:34-apache``
    writes it to stdout. The health check of ``compose.exapp.yml`` polls ``status.php``
    every five seconds and is not traffic anybody caused, so it is filtered out here.

    The whole log rather than a time window on purpose: ``docker logs --since`` resolves to
    whole seconds, and a measurement that counts round trips per call cannot afford to
    inherit or lose the requests of the second it starts in. The caller takes the list
    before and after and reads the difference, which is exact.
    """
    finished = subprocess.run(  # noqa: S603 - a fixed argument list, no shell, no user input
        ["docker", "logs", NEXTCLOUD_CONTAINER],  # noqa: S607 - docker is on PATH by contract
        capture_output=True,
        text=True,
        check=False,
    )
    lines = (finished.stdout + finished.stderr).splitlines()
    return [line for line in lines if '"' in line and HEALTHCHECK not in line]


def paths_of(lines: Sequence[str]) -> list[str]:
    """The request line of each access log entry, for the breakdown of a measurement."""
    found: list[str] = []
    for line in lines:
        match = re.search(r'"([A-Z]+ [^"]*?) HTTP/[0-9.]+"', line)
        if match is not None:
            found.append(match.group(1))
    return found


def check_discovery(base: str, nc: str) -> None:
    """Steps 2 and 3: the three documents over both proxy paths and the canonical roots."""
    with httpx.Client(timeout=TIMEOUT) as client:
        bodies: dict[str, bytes] = {}
        for way, prefix in (("harp", base), ("php-proxy", f"{nc}{PHP_PROXY_PREFIX}")):
            for suffix in (PRM_SUFFIX, OPENID_SUFFIX, AS_SUFFIX):
                response = client.get(f"{prefix}{suffix}")
                bodies[f"{way}{suffix}"] = response.content
                report(
                    "step 2",
                    "GET",
                    f"{way}:{suffix}",
                    response.status_code,
                    content_type=response.headers.get("content-type"),
                    cache_control=response.headers.get("cache-control"),
                )
                if response.status_code != 200:
                    raise CheckFailed(f"{way}{suffix} answered {response.status_code}")
        for suffix in (PRM_SUFFIX, OPENID_SUFFIX, AS_SUFFIX):
            if bodies[f"harp{suffix}"] != bodies[f"php-proxy{suffix}"]:
                raise CheckFailed(f"{suffix} differs between the two proxy paths")
        note("step 2", "both proxy paths serve all three documents byte for byte the same")

        for path in (ROOT_PRM, ROOT_AS):
            response = client.get(f"{nc}{path}")
            report(
                "step 3",
                "GET",
                f"root:{path}",
                response.status_code,
                content_type=response.headers.get("content-type"),
                rewrite="active" if response.status_code == 200 else "absent",
            )


def check_anonymous(base: str) -> None:
    """Step 1: the 401 that starts the whole discovery flow, and what it has to carry."""
    with httpx.Client(timeout=TIMEOUT) as client:
        response = client.post(
            f"{base}{MCP_SUFFIX}",
            headers={"Accept": "application/json, text/event-stream"},
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
        )
    challenge = response.headers.get("www-authenticate", "")
    report(
        "step 1",
        "POST",
        MCP_SUFFIX,
        response.status_code,
        cache_control=response.headers.get("cache-control"),
        www_authenticate=challenge,
    )
    if response.status_code != 401:
        raise CheckFailed(f"an anonymous MCP request answered {response.status_code}, not 401")
    if "resource_metadata=" not in challenge:
        raise CheckFailed("the 401 carries no resource_metadata pointer")
    if response.headers.get("cache-control") != "no-store":
        raise CheckFailed("the 401 may be cached")


async def check_flow(base: str, nc: str, user: str, password: str) -> tuple[Connection, str]:
    """Steps 4 to 7: registration, authorization, code exchange and one tool call."""
    connection = connect(base, nc, user, password, verbose=True)
    names = await list_tools(base, connection.access_token)
    report("step 7", "POST", MCP_SUFFIX, 200, tools=len(names), transport="streamable-http")
    if "files_upload" not in names:
        raise CheckFailed(f"the chain served a short tool list: {sorted(names)}")
    marker = f"oauthflowcheck{uuid.uuid4().hex[:10]}"
    created = payload_of(
        await tool_call(
            base,
            connection.access_token,
            "notes_create",
            {"title": marker, "content": "written by scripts/oauth_flow_check.py"},
        )
    )
    report("step 7", "tool", "notes_create", 200, note_id=created.get("id"), as_user=user)
    return connection, str(created.get("id") or "")


def drop_note(nc: str, user: str, credential: str, note_id: str) -> None:
    """Remove the one object this run created. The tool surface cannot: it never deletes.

    No tool of this server removes anything, which is the promise of the whole project
    (no destructive writes in v1). So the cleanup goes to Nextcloud directly, with the
    user's own app password, and only for the note this run wrote.
    """
    if not note_id:
        return
    with httpx.Client(base_url=nc, timeout=TIMEOUT) as client:
        response = client.delete(
            f"/index.php/apps/notes/api/v1/notes/{note_id.removeprefix('note:')}",
            auth=(user, credential),
            headers={"OCS-APIRequest": "true", "Accept": "application/json"},
        )
    report("cleanup", "DELETE", "/apps/notes/api/v1/notes", response.status_code, note=note_id)


def measure_roundtrips(base: str, connection: Connection) -> None:
    """Success Criterion 5: how many Nextcloud requests one MCP call costs, counted."""
    accepted = _count_around(
        lambda: asyncio.run(_repeat_calls(base, connection.access_token, MEASURE_CALLS))
    )
    note(
        "sc 5",
        f"{MEASURE_CALLS} accepted MCP calls -> {len(accepted)} Nextcloud requests "
        f"({len(accepted) / MEASURE_CALLS:.1f} per call): {sorted(set(paths_of(accepted)))}",
    )

    refused = _count_around(lambda: _flood_mcp(base, MEASURE_CALLS))
    note(
        "sc 5",
        f"{MEASURE_CALLS} refused MCP calls -> {len(refused)} Nextcloud requests "
        f"({len(refused) / MEASURE_CALLS:.1f} per call): {sorted(set(paths_of(refused)))}",
    )


def _count_around(work: Callable[[], object]) -> list[str]:
    """The access log lines one piece of work produced, and nothing that came before it."""
    time.sleep(1.0)
    before = len(nextcloud_requests())
    work()
    time.sleep(1.0)
    return nextcloud_requests()[before:]


def _flood_mcp(base: str, count: int) -> None:
    """A series of MCP calls with bearers this server never issued."""
    with httpx.Client(timeout=TIMEOUT) as client:
        for _ in range(count):
            client.post(
                f"{base}{MCP_SUFFIX}",
                headers={
                    "Accept": "application/json, text/event-stream",
                    "Authorization": f"Bearer {secrets.token_urlsafe(32)}",
                },
                json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
            )


async def _repeat_calls(base: str, token: str, count: int) -> None:
    async with _session(base, token) as client:
        for _ in range(count):
            await client.list_tools()


def measure_throttle(base: str) -> None:
    """The threshold of our own throttle, and the counter check the research asks for."""
    attempts = 0
    retry_after = ""
    with httpx.Client(timeout=TIMEOUT) as client:
        for attempt in range(1, FLOOD_LIMIT + 1):
            response = client.post(
                f"{base}/token",
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": secrets.token_urlsafe(32),
                    "client_id": "no-such-client",
                },
            )
            attempts = attempt
            if response.status_code == 429:
                retry_after = response.headers.get("retry-after", "")
                break
    report(
        "sc 5",
        "POST",
        "/token",
        429 if retry_after else 400,
        attempts=attempts,
        retry_after=retry_after or "not reached",
    )
    if not retry_after:
        raise CheckFailed(f"{FLOOD_LIMIT} refused token requests did not reach the throttle")


def counter_check(nc: str, user: str, password: str) -> None:
    """After the flood: the test user still signs in, so Nextcloud blocked nobody."""
    with httpx.Client(base_url=nc, timeout=TIMEOUT) as client:
        response = client.get(
            "/ocs/v2.php/cloud/user?format=json",
            auth=(user, password),
            headers={"OCS-APIRequest": "true", "Accept": "application/json"},
        )
    report("sc 5", "GET", "/ocs/v2.php/cloud/user", response.status_code, as_user=user)
    if response.status_code != 200:
        raise CheckFailed("the test user cannot sign in after the flood of invalid bearers")


def onboarding(base: str, nc: str, user: str, password: str) -> None:
    """Success Criterion 3: the browser onboarding of AUTH-02, walked without a browser."""
    with httpx.Client(timeout=TIMEOUT, follow_redirects=False) as client:
        invitation = client.get(f"{base}/connect")
        report(
            "sc 3",
            "GET",
            "/connect",
            invitation.status_code,
            cache_control=invitation.headers.get("cache-control"),
        )
        started = client.post(f"{base}/connect", data={"action": "start"})
        report("sc 3", "POST", "/connect", started.status_code)
        if started.status_code != 200:
            raise CheckFailed(f"the onboarding start answered {started.status_code}")
        link = re.search(r'href="([^"]*login/v2/flow[^"]*)"', started.text)
        if link is None:
            raise CheckFailed("the handoff page carried no sign in link")
        flow_id = hidden_field(started.text, "flow")

        sign_in(nc, user, password, link.group(1))

        result = client.get(f"{base}/connect/wait", params={"flow": flow_id})
        credential = detail_value(result.text, "Credential for your assistant app")
        report(
            "sc 3",
            "GET",
            "/connect/wait",
            result.status_code,
            signed_in_as=detail_value(result.text, "Signed in as"),
            credential=f"{len(credential)} characters, shown once",
        )

        again = client.get(f"{base}/connect/wait", params={"flow": flow_id})
        shown_twice = "Credential for your assistant app" in again.text
        report(
            "sc 3", "GET", "/connect/wait", again.status_code, credential_shown_again=shown_twice
        )
        if shown_twice:
            raise CheckFailed("the credential is shown a second time")

    with httpx.Client(timeout=TIMEOUT) as client:
        used = client.post(
            f"{base}{MCP_SUFFIX}",
            headers={
                "Accept": "application/json, text/event-stream",
                "Authorization": "Basic "
                + base64.b64encode(f"{user}:{credential}".encode()).decode(),
            },
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "oauth-flow-check", "version": "1.0"},
                },
            },
        )
    report(
        "sc 3",
        "POST",
        MCP_SUFFIX,
        used.status_code,
        auth="the credential from the page",
        server=used.headers.get("server"),
    )
    if used.status_code != 200:
        raise CheckFailed(f"the handed out credential answered {used.status_code} on /mcp")

    with httpx.Client(base_url=nc, timeout=TIMEOUT) as client:
        sessions = client.get(
            "/ocs/v2.php/core/getapppassword",
            auth=(user, credential),
            headers={"OCS-APIRequest": "true", "Accept": "application/json"},
        )
    note(
        "sc 3",
        f"the credential is a Nextcloud app password "
        f"(getapppassword answered {sessions.status_code})",
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Walk the whole OAuth 2.1 flow against a running ExApp topology."
    )
    parser.add_argument("base", help="the public base URL of the ExApp, without a trailing slash")
    parser.add_argument(
        "--measure",
        action="store_true",
        help="add the Success Criterion 5 round trip count and the Success Criterion 3 walk",
    )
    arguments = parser.parse_args(argv)
    base = arguments.base.rstrip("/")

    nc = (os.environ.get("NC_MCP_URL") or "").rstrip("/")
    user = os.environ.get("NC_MCP_TEST_USER") or ""
    password = os.environ.get("NC_MCP_TEST_PASSWORD") or ""
    missing = [
        name
        for name, value in (
            ("NC_MCP_URL", nc),
            ("NC_MCP_TEST_USER", user),
            ("NC_MCP_TEST_PASSWORD", password),
        )
        if not value
    ]
    if missing:
        print(f"missing environment: {', '.join(missing)} (see .env.exapp)", file=sys.stderr)
        return 2

    try:
        check_anonymous(base)
        check_discovery(base, nc)
        connection, note_id = asyncio.run(check_flow(base, nc, user, password))
        if arguments.measure:
            measure_roundtrips(base, connection)
            onboarding(base, nc, user, password)
        drop_note(nc, user, os.environ.get("NC_MCP_TEST_APP_PASSWORD") or password, note_id)
        status = revoke(connection)
        report("cleanup", "POST", "/revoke", status, connection="ended")
        if arguments.measure:
            # Last, and deliberately so: the throttle counts per path class and per source,
            # and this measurement blocks the token class for this source for the length of
            # a window. Everything above it has to have happened by then, and a second run
            # of this script has to wait that window out (five minutes).
            measure_throttle(base)
            counter_check(nc, user, password)
    except CheckFailed as failure:
        print(f"FAILED: {failure}", file=sys.stderr)
        return 1
    print("all steps answered as the specification and this deployment require")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
