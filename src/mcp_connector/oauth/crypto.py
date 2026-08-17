"""The one way a secret of this phase reaches the disk: AES-GCM bound to its row.

Two responsibilities live here and they are deliberately separable. :func:`encrypt` and
:func:`decrypt` take the key as a parameter, so every call site and every test works
without an environment and without a network. :func:`data_key` is the third one: it fetches
the key of this installation from Nextcloud, which is the only part that talks to anybody.

**Why the key is not derived from the app secret of the AppAPI registration (D-43).**
That value is a transport secret, not a data key, and it is regenerated whenever an ExApp
is registered without one. Deriving from it would mean that a single re-registration, the
most ordinary administrative act there is, turns every stored app password into noise and
every connected assistant into a broken one. The key of this module is created once, kept
in Nextcloud's own configuration and never derived from anything.

**Why the key lives in Nextcloud and not next to the database (D-43).** The store is a
file in a Docker volume that the host can read. A key file beside it would be in the same
place as the data it protects, so one stolen volume would be enough. Nextcloud keeps ExApp
configuration in ``oc_appconfig``, encrypted with the server secret, which is a different
trust boundary and a different backup.

**Why AES-GCM with an aad and not Fernet.** Fernet is simpler, but its ciphertext is not
bound to the row it was stored in. Anybody who can write to the database file could move
a ciphertext from one authorization to another and get the app password of a different
user decrypted for them. The additional authenticated data of this module is the row id,
so a moved ciphertext is refused instead of decrypted (T-03-12).
"""

import hashlib
import hmac
import logging
import secrets
from collections.abc import Mapping
from typing import Any

import httpx
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .. import config
from ..errors import ToolError
from ..nextcloud.clients.ocs import OCS_HEADERS
from ..nextcloud.credentials import appapi_auth_headers
from ..nextcloud.http import shared_client

__all__ = [
    "CONFIG_KEY",
    "CONFIG_READ_FIELD",
    "CONFIG_READ_SUFFIX",
    "EXAPP_CONFIG_PATH",
    "KEY_BYTES",
    "NONCE_BYTES",
    "DecryptionRejected",
    "data_key",
    "decrypt",
    "encrypt",
    "form_token",
]

#: AES-256. The size is fixed here instead of being inferred from the stored value, so a
#: truncated configuration value is a named failure and not a weaker cipher.
KEY_BYTES = 32

#: The nonce size AES-GCM is specified for. A fresh one per call, prepended to the
#: ciphertext: reusing a nonce under one key destroys the security of the mode outright.
NONCE_BYTES = 12

#: The name of the value in Nextcloud's ExApp configuration.
CONFIG_KEY = "oauth_data_key"

#: What :func:`form_token` derives, spelled out so the same key can never produce two
#: values that mean different things. Versioned, so a later change is a new value and not a
#: silent reinterpretation of an old one.
_FORM_TOKEN_LABEL = b"consent-form-v1:"

#: The three purposes a form value of this application can have, and the whole point of the
#: parameter (ME-01). ``consent.py`` writes an authorization under the id of its own flow,
#: so ``auth_id`` and ``flow_id`` are the same string: without a purpose in the derivation,
#: the value that means "approve this authorization request" is byte for byte the value that
#: means "end this connection". Whoever sees one of them once therefore holds the other one
#: for good, and neither can be rotated, because the only key here is the data key and
#: replacing it makes every stored app password unreadable.
PURPOSE_CONSENT = "consent"
PURPOSE_DISCONNECT = "disconnect"
PURPOSE_SWITCH = "switch"

#: The AppAPI route that stores ExApp configuration. ``sensitive`` marks the value as one
#: Nextcloud must not show in any administrative interface.
EXAPP_CONFIG_PATH = "/ocs/v2.php/apps/app_api/api/v1/ex-app/config"

#: How the read is asked, measured against a running AppAPI 34.0.0 in plan 03-08. The
#: route table of that app declares three verbs on this resource and none of them is a
#: ``GET``: ``POST /ex-app/config`` writes, ``DELETE /ex-app/config`` removes, and the read
#: is ``POST /ex-app/config/get-values`` with a JSON body ``{"configKeys": [...]}``
#: (``AppConfigController::getAppConfigValues``). The shape this module carried until then
#: was a ``GET`` with a ``configKeys[]`` query parameter, which the server has no route for
#: and answers with 401 and "Current user is not logged in", because the request never
#: reaches the AppAPI authentication of a declared route.
CONFIG_READ_SUFFIX = "/get-values"
CONFIG_READ_FIELD = "configKeys"

_KEY_HINT = (
    "The data key of this app lives in the ExApp configuration of Nextcloud "
    f"(key {CONFIG_KEY!r}, stored as sensitive). Check that the app is registered and "
    "enabled and that Nextcloud is reachable from the container, then restart the app. "
    "Never replace the value by hand: a different key makes every stored authorization "
    "unreadable and every connected client has to authorize again."
)

logger = logging.getLogger("mcp_connector.oauth.crypto")


class DecryptionRejected(Exception):
    """This ciphertext does not belong to this key and this row.

    Carries no message and no arguments on purpose, the same rule the AppAPI rejection
    follows: the material is the key, the nonce and the ciphertext, and an exception that
    quotes any of them writes them into every traceback and every log handler above
    (T-03-16). Wrong key, wrong row, flipped byte and truncated blob are one case for the
    caller, because it can act on none of them.
    """


def encrypt(key: bytes, plaintext: bytes, *, aad: str) -> bytes:
    """Return ``nonce || ciphertext`` for this plaintext, bound to ``aad``.

    ``aad`` is the id of the row the result is stored in. It is authenticated but not
    encrypted, which is exactly what is needed: it never has to come back out of the blob,
    it only has to make the blob useless anywhere else.
    """
    _check_key(key)
    nonce = secrets.token_bytes(NONCE_BYTES)
    return nonce + AESGCM(key).encrypt(nonce, plaintext, aad.encode("utf-8"))


def decrypt(key: bytes, blob: bytes, *, aad: str) -> bytes:
    """Return the plaintext of ``blob``, or refuse. There is no third outcome.

    AES-GCM verifies the authentication tag before it releases anything, so a single
    flipped byte yields a refusal and never a partial or corrupted plaintext.
    """
    _check_key(key)
    if len(blob) <= NONCE_BYTES:
        raise DecryptionRejected
    try:
        return AESGCM(key).decrypt(blob[:NONCE_BYTES], blob[NONCE_BYTES:], aad.encode("utf-8"))
    except InvalidTag:
        raise DecryptionRejected from None


def form_token(key: bytes, handle: str, *, purpose: str) -> str:
    """The anti forgery value of one form, for one handle and one purpose (T-03-50, ME-01).

    A hidden field that binds a form to one action has to be three things: impossible to
    produce without being this deployment, impossible to reuse for another handle, and
    impossible to reuse for another action on the same handle. An HMAC over the purpose and
    the handle with the data key is all three, and it is the one shape that needs no column:
    a value that can be recomputed at every render is a migration for nothing. It also
    survives a restart and a second worker process, which a token kept in a dictionary would
    not.

    ``purpose`` is not decoration. It closes the case where two different privileged actions
    are about the same string, which is exactly what this application has: an authorization
    is written under the id of the flow it was born in. The label keeps every value of this
    function apart from anything else the same key might ever authenticate; the purpose keeps
    them apart from each other.

    The two fields are joined with the length of the first in front of them, so the split
    between them is unambiguous whatever either of them contains. ``"a"`` plus ``"b:c"`` and
    ``"a:b"`` plus ``"c"`` would otherwise be the same material and therefore the same value,
    which is the classic way a domain separation stops separating. Neither field is attacker
    controlled today, and this is what lets that stay a property rather than a coincidence.
    """
    _check_key(key)
    material = f"{len(purpose)}:{purpose}:{handle}".encode()
    return hmac.new(key, _FORM_TOKEN_LABEL + material, hashlib.sha256).hexdigest()


async def data_key(env: Mapping[str, str] | None = None) -> bytes:
    """Return the data key of this installation, creating it on the very first start.

    One attempt per call and no retry loop, like every other outgoing call of this project
    (shared pattern 4). The difference to ``exapp/status.py``, and it is the whole reason
    this function raises instead of logging: a missed progress push costs a progress bar,
    while a missed key would either stop the store or, far worse, tempt a caller into
    running with a fresh one. A fresh key looks like it works and silently invalidates
    every authorization that was ever stored, so every failure below is a hard one
    (pitfall 11, T-03-14).

    **What the read back does, and what it does not do (WR-02).** The write is followed by
    a read rather than by trusting what was sent, and the answer is compared against what
    was written: a worker that lost the race adopts the key of the one that won, which is
    the key of this installation from then on, and says so in a warning. This function
    never returns a value it did not read out of Nextcloud.

    It does not make the first start of two workers atomic, and the docstring used to claim
    it did. There is no compare and set in the ExApp configuration API, so two writes can
    still interleave in a way no read of ours can see: A writes, A reads back its own
    value, B writes over it. The read is therefore repeated once after the first one has
    returned, which catches the write that arrived while the first read was in flight, and
    a loser that is still missed encrypts with a key nobody can read again. The window is
    the very first start of a deployment, before any row exists, and the failure is loud
    rather than silent: the store answers ``DecryptionRejected`` on the first read of a row
    it wrote, which every caller of this phase already handles as a refusal. An
    installation that wants the window closed starts the first container with one worker,
    which ``docs/oauth-setup.md`` says.
    """
    settings = config.exapp_settings(env)
    stored = await _read_key(settings)
    if stored is not None:
        return stored

    written = secrets.token_bytes(KEY_BYTES).hex()
    await _write_key(settings, written)
    stored = await _confirm_key(settings)
    if stored.hex() != written:
        # Somebody else stored a key first, and theirs is the key of this installation.
        # Nothing of ours is lost here: no row exists yet at this point of a first start.
        logger.warning("another worker stored the data key first; this one adopts the stored key")
        return stored

    # A second read, after the first one has already returned: a worker that wrote while
    # that read was in flight is visible in this one and in no earlier answer.
    confirmed = await _confirm_key(settings)
    if confirmed.hex() != written:
        logger.warning("another worker stored the data key first; this one adopts the stored key")
    return confirmed


async def _confirm_key(settings: config.ExAppSettings) -> bytes:
    """The stored key after a write, or a named failure. Never ``None``, never invented."""
    stored = await _read_key(settings)
    if stored is None:
        raise ToolError(
            message=f"The ExApp configuration has no {CONFIG_KEY} after it was stored.",
            hint=_KEY_HINT,
        )
    return stored


async def _read_key(settings: config.ExAppSettings) -> bytes | None:
    """Return the stored key, or ``None`` when Nextcloud says there is none yet.

    ``None`` means one thing only: the answer was readable and the value is not there. An
    answer we cannot read raises, because treating it as "no key yet" is what would make
    the caller store a second key over a first one that was merely unreadable to us.
    """
    url = f"{settings.base_url}{EXAPP_CONFIG_PATH}{CONFIG_READ_SUFFIX}"
    client = shared_client()
    try:
        response = await client.post(
            url, json={CONFIG_READ_FIELD: [CONFIG_KEY]}, headers=_headers(settings)
        )
    except httpx.HTTPError:
        # No value from the request is repeated here: the headers carry the app secret.
        logger.error("the ExApp configuration at %s could not be read", url)
        raise ToolError(
            message="Nextcloud could not be reached to read the data key of this app.",
            hint=_KEY_HINT,
        ) from None

    if response.status_code // 100 != 2:
        raise ToolError(
            message=f"Nextcloud answered {response.status_code} when the data key was read.",
            hint=_KEY_HINT,
        )

    raw = _config_value(_payload(response))
    if raw is None:
        return None
    return _decode_key(raw)


async def _write_key(settings: config.ExAppSettings, value: str) -> None:
    """Store a freshly created key as a sensitive value. One attempt, no retry."""
    url = f"{settings.base_url}{EXAPP_CONFIG_PATH}"
    client = shared_client()
    try:
        response = await client.post(
            url,
            json={"configKey": CONFIG_KEY, "configValue": value, "sensitive": 1},
            headers=_headers(settings),
        )
    except httpx.HTTPError:
        # Neither the key nor a header value appears in this line.
        logger.error("the ExApp configuration at %s could not be written", url)
        raise ToolError(
            message="Nextcloud could not be reached to store the data key of this app.",
            hint=_KEY_HINT,
        ) from None

    if response.status_code // 100 != 2:
        raise ToolError(
            message=f"Nextcloud answered {response.status_code} when the data key was stored.",
            hint=_KEY_HINT,
        )


def _headers(settings: config.ExAppSettings) -> dict[str, str]:
    """The OCS headers plus the AppAPI identity, in the app context (empty user id)."""
    headers = dict(OCS_HEADERS)
    headers.update(
        appapi_auth_headers(
            "",
            app_id=settings.app_id,
            app_version=settings.app_version,
            aa_version=settings.aa_version,
            app_secret=settings.app_secret,
        )
    )
    return headers


def _payload(response: httpx.Response) -> Any:
    try:
        return response.json()
    except ValueError:
        raise ToolError(
            message="Nextcloud answered the data key request with something that is not JSON.",
            hint=_KEY_HINT,
        ) from None


def _config_value(payload: Any) -> str | None:
    """Pull our one value out of the OCS envelope, or refuse to guess.

    Three shapes are accepted. The one a running AppAPI 34.0.0 answers with is a list of
    entries whose field names are lower case, ``configkey`` and ``configvalue``: they are
    the column names of the ``ex_apps_config`` table, serialised straight out of the
    entity (measured in plan 03-08, and the second reason the read never worked before).
    The camel case spelling of the same list is accepted next to it, because it is what
    the write side of this API takes and what a later version may answer with, and so is a
    mapping of key to value. Everything else raises rather than being read as an empty
    result (fail closed, D-37).
    """
    if not isinstance(payload, dict):
        raise _unreadable()
    ocs = payload.get("ocs")
    if not isinstance(ocs, dict) or "data" not in ocs:
        raise _unreadable()

    data = ocs["data"]
    if isinstance(data, list):
        for entry in data:
            if not isinstance(entry, dict):
                raise _unreadable()
            name = entry.get("configkey", entry.get("configKey"))
            if name is None:
                raise _unreadable()
            if name != CONFIG_KEY:
                continue
            value = entry.get("configvalue", entry.get("configValue"))
            if not isinstance(value, str):
                raise _unreadable()
            return value
        return None
    if isinstance(data, dict):
        if CONFIG_KEY not in data:
            return None
        value = data[CONFIG_KEY]
        if not isinstance(value, str):
            raise _unreadable()
        return value
    raise _unreadable()


def _decode_key(raw: str) -> bytes:
    """Turn the stored hex into a key, or name the value that is wrong without quoting it."""
    try:
        key = bytes.fromhex(raw.strip())
    except ValueError:
        raise _wrong_key_material() from None
    if len(key) != KEY_BYTES:
        raise _wrong_key_material()
    return key


def _wrong_key_material() -> ToolError:
    """The stored value itself never appears in the message: it is key material."""
    return ToolError(
        message=f"The stored {CONFIG_KEY} is not {KEY_BYTES} bytes of hex.",
        hint=_KEY_HINT,
    )


def _unreadable() -> ToolError:
    return ToolError(
        message="The ExApp configuration answer could not be read, so it is not treated as "
        "an empty one.",
        hint=_KEY_HINT,
    )


def _check_key(key: bytes) -> None:
    if len(key) != KEY_BYTES:
        raise ValueError(f"the data key must be {KEY_BYTES} bytes, got {len(key)}")
