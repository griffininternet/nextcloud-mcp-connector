"""MCP server layer: the only place in this project that registers tools.

Three things live here and nowhere else: the server object with its tool annotations, the
compact JSON serialisation, and the graceful wrapper that turns every internal error into
one honest sentence for the model. Transport arguments are not part of the constructor;
``entry_stdio`` calls ``mcp.run()`` and ``entry_http`` builds ``streamable_http_app()``.

The auth wiring is decided once, at process start, from the environment: either the SDK
bearer layer guards the server (static bearer, single-user deployment) or it stays
completely unarmed and the Basic credentials of each request are passed through. Mixing
the two is pitfall 2, and switching modes is a restart, not a request.

Deliberately absent (D-19, D-20, pitfall 1): the v1 server class, the legacy-only
statelessness switch and ``request_state_security``. In mcp 2.x both protocol eras are
served from one server object, and that switch only affects the legacy leg, where it costs
both server-to-client channels. It is the exact setting behind nextcloud/context_agent#227,
so it stays unset and is not even named here, which keeps the grep gate honest.
"""

import functools
import importlib
import json
import pkgutil
from collections.abc import Awaitable, Callable
from typing import Any

import httpx
from mcp.server import MCPServer
from mcp.types import ToolAnnotations

from .. import deps
from ..errors import ToolError

__all__ = ["CREATE_ONLY", "READ_ONLY", "compact", "graceful", "mcp"]

# (None, None) unless a static bearer is configured. The SDK rejects one without the
# other with a ValueError in the constructor, so they are built as a pair.
_token_verifier, _auth_settings = deps.build_auth()

mcp = MCPServer(
    "MCP Connector",
    version="0.1.0",
    instructions=(
        "Read and create content in the user's own Nextcloud. "
        "This server can never delete, overwrite or re-share anything."
    ),
    token_verifier=_token_verifier,
    auth=_auth_settings,
)

# Honest annotations (D-16). snake_case in Python, camelCase on the wire.
READ_ONLY = ToolAnnotations(read_only_hint=True, open_world_hint=False)
CREATE_ONLY = ToolAnnotations(
    read_only_hint=False,
    destructive_hint=False,
    idempotent_hint=False,
    open_world_hint=False,
)


def compact(payload: object) -> str:
    """Serialise a tool answer without a single wasted byte (schema diet, D-14)."""
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=False)


def graceful[T](fn: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
    """Translate internal failures into an ordinary tool error the model can act on.

    ``from None`` is not cosmetic: an httpx traceback can contain the request URL, and a
    URL is one careless change away from carrying credentials (threat T-01-07). A 4xx or a
    guard rejection reaches the model as text so it can correct itself; only situations no
    model could fix (missing credentials in HTTP mode) become an ``MCPError``, which plan
    04 adds where it belongs.

    Generic in the return type, because thirteen tools answer with a compact JSON string
    and the two tools of the ChatGPT profile answer with a Pydantic model. Pinning this to
    ``str`` would erase exactly the annotation the SDK builds their output schema from.
    """

    @functools.wraps(fn)
    async def wrapper(*args: Any, **kwargs: Any) -> T:
        try:
            return await fn(*args, **kwargs)
        except ToolError as exc:
            raise ValueError(f"{exc.message} Hint: {exc.hint}") from None
        except httpx.TimeoutException:
            raise ValueError(
                "Nextcloud did not respond in time. Hint: retry with a smaller range or a "
                "narrower scope."
            ) from None
        except httpx.RequestError:
            raise ValueError(
                "Could not reach Nextcloud. Hint: check the configured Nextcloud URL and "
                "that the server is online."
            ) from None

    return wrapper


def _load_registrations() -> None:
    """Import every ``reg_*`` module so its tools register themselves.

    Each tool bundle owns its own registration file. That way plans that are written in
    parallel never have to change one shared file, and a new bundle is a new file plus
    nothing else.
    """
    for module in pkgutil.iter_modules(__path__):
        if module.name.startswith("reg_"):
            importlib.import_module(f"{__name__}.{module.name}")


_load_registrations()
