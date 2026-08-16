"""The data key of this phase and the encryption every stored secret goes through.

Threats covered here: T-03-10 (the store file leaves the volume), T-03-12 (ciphertexts
moved between rows), T-03-14 (a key derived from the transport secret dies on the next
registration) and T-03-16 (a key or a plaintext in a log record).

Nothing here opens a socket. The two crypto functions take the key as a parameter, which
is what lets every check below run without an environment and without Nextcloud, and the
one outgoing OCS call is answered by respx.
"""

import inspect
import json
import logging

import httpx
import pytest
import respx

from mcp_connector import config
from mcp_connector.errors import ToolError
from mcp_connector.oauth import crypto

APP_ID = "mcp_connector"
APP_SECRET = "app-secret-test"
APP_VERSION = "0.1.0"
BASE_URL = "http://nc.test"

ENV = {
    config.ENV_APP_ID: APP_ID,
    config.ENV_APP_SECRET: APP_SECRET,
    config.ENV_APP_VERSION: APP_VERSION,
    config.ENV_AA_VERSION: "34.0.3",
    config.ENV_NEXTCLOUD_URL: BASE_URL,
}

CONFIG_URL = f"{BASE_URL}{crypto.EXAPP_CONFIG_PATH}"
#: The read is its own route and its own verb (measured against AppAPI 34.0.0 in plan
#: 03-08): a POST to /get-values with a JSON body, not a GET with a query parameter.
READ_URL = f"{CONFIG_URL}{crypto.CONFIG_READ_SUFFIX}"

#: A key that is not secret, because it never leaves this file.
KEY = bytes(range(32))
OTHER_KEY = bytes(range(32, 64))
STORED_KEY_HEX = "b1" * 32

AAD = "auth-0001"
OTHER_AAD = "auth-0002"
PLAINTEXT = b"app-password-of-alice"


def ocs_body(data: object) -> dict[str, object]:
    """The OCS v2 envelope AppAPI answers with."""
    return {"ocs": {"meta": {"status": "ok", "statuscode": 200, "message": "OK"}, "data": data}}


def stored(value: str) -> dict[str, object]:
    """The shape a running AppAPI 34.0.0 answers with: the column names, lower case."""
    return ocs_body([{"configkey": crypto.CONFIG_KEY, "configvalue": value}])


# --- the two crypto functions -----------------------------------------------------


@pytest.mark.parametrize(
    "plaintext",
    [b"", b"x", PLAINTEXT, "Grüße aus Hamburg".encode(), bytes(range(256)) * 4],
    ids=["empty", "one byte", "an app password", "umlauts", "a kilobyte of every byte"],
)
def test_encrypt_and_decrypt_are_inverse_for_any_bytes(plaintext: bytes) -> None:
    blob = crypto.encrypt(KEY, plaintext, aad=AAD)
    assert crypto.decrypt(KEY, blob, aad=AAD) == plaintext


def test_a_ciphertext_of_another_row_is_refused() -> None:
    """T-03-12: aad is the row id, so a ciphertext moved between rows does not decrypt."""
    blob = crypto.encrypt(KEY, PLAINTEXT, aad=AAD)
    with pytest.raises(crypto.DecryptionRejected):
        crypto.decrypt(KEY, blob, aad=OTHER_AAD)


def test_a_ciphertext_of_another_key_is_refused() -> None:
    blob = crypto.encrypt(KEY, PLAINTEXT, aad=AAD)
    with pytest.raises(crypto.DecryptionRejected):
        crypto.decrypt(OTHER_KEY, blob, aad=AAD)


@pytest.mark.parametrize("index", [0, crypto.NONCE_BYTES - 1, crypto.NONCE_BYTES, -1])
def test_a_single_flipped_byte_is_refused_in_the_nonce_and_in_the_ciphertext(index: int) -> None:
    """No partial result: AES-GCM verifies the tag before it returns anything."""
    blob = bytearray(crypto.encrypt(KEY, PLAINTEXT, aad=AAD))
    blob[index] ^= 0x01
    with pytest.raises(crypto.DecryptionRejected):
        crypto.decrypt(KEY, bytes(blob), aad=AAD)


@pytest.mark.parametrize("length", [0, 1, crypto.NONCE_BYTES, crypto.NONCE_BYTES + 1])
def test_a_truncated_blob_is_refused_and_never_raises_something_else(length: int) -> None:
    blob = crypto.encrypt(KEY, PLAINTEXT, aad=AAD)
    with pytest.raises(crypto.DecryptionRejected):
        crypto.decrypt(KEY, blob[:length], aad=AAD)


def test_the_same_plaintext_twice_gives_two_different_ciphertexts() -> None:
    """A fresh nonce per call. Reusing one under the same key breaks AES-GCM outright."""
    first = crypto.encrypt(KEY, PLAINTEXT, aad=AAD)
    second = crypto.encrypt(KEY, PLAINTEXT, aad=AAD)
    assert first != second
    assert first[: crypto.NONCE_BYTES] != second[: crypto.NONCE_BYTES]
    assert crypto.decrypt(KEY, first, aad=AAD) == crypto.decrypt(KEY, second, aad=AAD)


def test_the_ciphertext_never_contains_the_plaintext() -> None:
    blob = crypto.encrypt(KEY, PLAINTEXT, aad=AAD)
    assert PLAINTEXT not in blob


@pytest.mark.parametrize("key", [b"", b"short", bytes(31), bytes(33)])
def test_a_key_of_the_wrong_length_is_a_programming_error(key: bytes) -> None:
    """Not a ToolError: no operator can act on this, it is a bug in a call site."""
    with pytest.raises(ValueError, match="32"):
        crypto.encrypt(key, PLAINTEXT, aad=AAD)
    with pytest.raises(ValueError, match="32"):
        crypto.decrypt(key, b"x" * 40, aad=AAD)


def test_the_refusal_carries_neither_the_key_nor_the_ciphertext() -> None:
    """T-03-16: an exception that quotes the material is a leak with a stack trace."""
    blob = crypto.encrypt(KEY, PLAINTEXT, aad=AAD)
    with pytest.raises(crypto.DecryptionRejected) as excinfo:
        crypto.decrypt(KEY, blob, aad=OTHER_AAD)
    text = f"{excinfo.value} {excinfo.value.args!r}"
    assert text.strip() in ("()", " ()")
    assert KEY.hex() not in text
    assert blob.hex() not in text


# --- the key exchange with the ExApp config ---------------------------------------


@pytest.mark.anyio
@respx.mock
async def test_the_first_start_creates_the_key_and_stores_it_as_sensitive() -> None:
    """D-43: our own 32 byte key, in Nextcloud's config, marked sensitive."""
    read = respx.post(READ_URL).mock(
        side_effect=[
            httpx.Response(200, json=ocs_body([])),
            httpx.Response(200, json=stored(STORED_KEY_HEX)),
        ]
    )
    write = respx.post(CONFIG_URL).mock(return_value=httpx.Response(200, json=ocs_body([])))

    key = await crypto.data_key(ENV)

    assert key == bytes.fromhex(STORED_KEY_HEX)
    assert write.called
    payload = json.loads(write.calls.last.request.content)
    assert payload["configKey"] == crypto.CONFIG_KEY
    assert payload["sensitive"] == 1
    assert len(bytes.fromhex(payload["configValue"])) == crypto.KEY_BYTES
    assert read.call_count == 2, "the value is read back, so a parallel worker wins cleanly"


@pytest.mark.anyio
@respx.mock
async def test_the_key_this_process_wrote_is_confirmed_by_a_second_read() -> None:
    """WR-02: the first read back can answer our own write while a worker that started at
    the same moment is still writing over it. The second read, sent after the first one has
    returned, is the one that can see that write."""
    written: list[str] = []

    def write(request: httpx.Request) -> httpx.Response:
        written.append(json.loads(request.content)["configValue"])
        return httpx.Response(200, json=ocs_body([]))

    reads: list[int] = []

    def answer(request: httpx.Request) -> httpx.Response:
        reads.append(1)
        if not written:
            return httpx.Response(200, json=ocs_body([]))
        return httpx.Response(200, json=stored(written[0]))

    respx.post(READ_URL).mock(side_effect=answer)
    respx.post(CONFIG_URL).mock(side_effect=write)

    key = await crypto.data_key(ENV)

    assert key == bytes.fromhex(written[0])
    assert len(reads) == 3, "empty, the read back, and the one that confirms it"


@pytest.mark.anyio
@respx.mock
async def test_a_worker_that_lost_the_race_adopts_the_stored_key(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """WR-02: the docstring claimed both workers continue with the value that survived. The
    loser has to adopt the stored one, and it has to say so: every row it wrote with its
    own key would be unreadable, and at this point of a first start there are none."""
    respx.post(READ_URL).mock(
        side_effect=[
            httpx.Response(200, json=ocs_body([])),
            httpx.Response(200, json=stored(STORED_KEY_HEX)),
        ]
    )
    respx.post(CONFIG_URL).mock(return_value=httpx.Response(200, json=ocs_body([])))

    with caplog.at_level(logging.WARNING):
        key = await crypto.data_key(ENV)

    assert key == bytes.fromhex(STORED_KEY_HEX), "the stored key wins, never the written one"
    assert "another worker stored the data key first" in caplog.text
    assert STORED_KEY_HEX not in caplog.text, "T-03-16: no key material in a log line"


@pytest.mark.anyio
@respx.mock
async def test_a_key_that_disappears_on_the_confirming_read_is_a_named_failure() -> None:
    """The second read is a read like every other one: an absent value is a hard failure and
    never a reason to run on a key nobody stored."""
    written: list[str] = []

    def write(request: httpx.Request) -> httpx.Response:
        written.append(json.loads(request.content)["configValue"])
        return httpx.Response(200, json=ocs_body([]))

    reads: list[int] = []

    def answer(request: httpx.Request) -> httpx.Response:
        reads.append(1)
        if len(reads) == 2 and written:
            return httpx.Response(200, json=stored(written[0]))
        return httpx.Response(200, json=ocs_body([]))

    respx.post(READ_URL).mock(side_effect=answer)
    respx.post(CONFIG_URL).mock(side_effect=write)

    with pytest.raises(ToolError) as excinfo:
        await crypto.data_key(ENV)

    assert crypto.CONFIG_KEY in excinfo.value.message


@pytest.mark.anyio
@respx.mock
async def test_an_existing_key_is_read_and_never_overwritten() -> None:
    """T-03-14: a second key would make every stored app password unreadable."""
    respx.post(READ_URL).mock(return_value=httpx.Response(200, json=stored(STORED_KEY_HEX)))
    write = respx.post(CONFIG_URL).mock(return_value=httpx.Response(200, json=ocs_body([])))

    assert await crypto.data_key(ENV) == bytes.fromhex(STORED_KEY_HEX)
    assert not write.called


@pytest.mark.anyio
@respx.mock
async def test_the_read_carries_the_ocs_and_the_appapi_headers() -> None:
    read = respx.post(READ_URL).mock(return_value=httpx.Response(200, json=stored(STORED_KEY_HEX)))

    await crypto.data_key(ENV)

    sent = read.calls.last.request
    assert sent.headers["OCS-APIRequest"] == "true"
    assert sent.headers["Accept"] == "application/json"
    assert sent.headers["EX-APP-ID"] == APP_ID
    assert sent.headers["EX-APP-VERSION"] == APP_VERSION
    assert sent.headers["AUTHORIZATION-APP-API"], "the app context token of an ExApp"
    assert json.loads(sent.content) == {crypto.CONFIG_READ_FIELD: [crypto.CONFIG_KEY]}, (
        "the read names the one key it wants, in the body of the POST AppAPI declares"
    )


@pytest.mark.parametrize(
    "data",
    [
        [{"configkey": crypto.CONFIG_KEY, "configvalue": STORED_KEY_HEX}],
        [{"configKey": crypto.CONFIG_KEY, "configValue": STORED_KEY_HEX}],
        [
            {"configkey": "another_key", "configvalue": "00" * 32},
            {"configkey": crypto.CONFIG_KEY, "configvalue": STORED_KEY_HEX},
        ],
        {crypto.CONFIG_KEY: STORED_KEY_HEX},
    ],
    ids=["the measured shape", "camel case", "next to another entry", "a mapping"],
)
@pytest.mark.anyio
@respx.mock
async def test_every_answer_shape_this_api_has_produced_is_read(data: object) -> None:
    """The lower case list is what AppAPI 34.0.0 answers (measured, plan 03-08).

    The other three stay accepted next to it: camel case is the spelling of the write side
    of the same API, an entry of another key must be stepped over rather than refused, and
    the mapping is the shape an earlier reading of this API expected.
    """
    respx.post(READ_URL).mock(return_value=httpx.Response(200, json=ocs_body(data)))
    write = respx.post(CONFIG_URL).mock(return_value=httpx.Response(200, json=ocs_body([])))

    assert await crypto.data_key(ENV) == bytes.fromhex(STORED_KEY_HEX)
    assert not write.called


@pytest.mark.anyio
@respx.mock
async def test_a_transport_error_stops_the_process_instead_of_inventing_a_key() -> None:
    """Pitfall 11: a random key looks like it works and kills every existing connection."""
    respx.post(READ_URL).mock(side_effect=httpx.ConnectError("no route to host"))
    write = respx.post(CONFIG_URL).mock(return_value=httpx.Response(200, json=ocs_body([])))

    with pytest.raises(ToolError) as excinfo:
        await crypto.data_key(ENV)
    assert excinfo.value.hint
    assert not write.called


@pytest.mark.parametrize("status", [401, 403, 404, 500, 502])
@pytest.mark.anyio
@respx.mock
async def test_a_rejected_read_is_a_named_failure(status: int) -> None:
    respx.post(READ_URL).mock(return_value=httpx.Response(status, json=ocs_body([])))

    with pytest.raises(ToolError) as excinfo:
        await crypto.data_key(ENV)
    assert str(status) in excinfo.value.message
    assert excinfo.value.hint


@pytest.mark.parametrize(
    "body",
    [
        {"unexpected": "shape"},
        {"ocs": {"meta": {}}},
        {"ocs": {"meta": {}, "data": "a string"}},
        {"ocs": {"meta": {}, "data": [{"configKey": crypto.CONFIG_KEY}]}},
        {"ocs": {"meta": {}, "data": [{"configkey": crypto.CONFIG_KEY}]}},
        {"ocs": {"meta": {}, "data": [{"value": STORED_KEY_HEX}]}},
    ],
    ids=[
        "no envelope",
        "no data",
        "data is not a collection",
        "entry without a value",
        "entry without a value, lower case",
        "entry without a key at all",
    ],
)
@pytest.mark.anyio
@respx.mock
async def test_an_unreadable_answer_never_counts_as_an_absent_key(body: dict) -> None:
    """Fail closed: 'I could not read it' must never turn into 'there is none yet'."""
    respx.post(READ_URL).mock(return_value=httpx.Response(200, json=body))
    write = respx.post(CONFIG_URL).mock(return_value=httpx.Response(200, json=ocs_body([])))

    with pytest.raises(ToolError):
        await crypto.data_key(ENV)
    assert not write.called, "a new key here would overwrite one we simply failed to parse"


@pytest.mark.parametrize(
    "value",
    ["", "not hex at all", "ab", "b1" * 31, "b1" * 33, "  "],
    ids=["blank", "not hex", "too short", "31 bytes", "33 bytes", "whitespace"],
)
@pytest.mark.anyio
@respx.mock
async def test_a_stored_value_that_is_not_a_32_byte_key_is_refused(value: str) -> None:
    respx.post(READ_URL).mock(return_value=httpx.Response(200, json=stored(value)))

    with pytest.raises(ToolError) as excinfo:
        await crypto.data_key(ENV)
    assert crypto.CONFIG_KEY in excinfo.value.message
    assert value.strip() not in excinfo.value.message or not value.strip()


@pytest.mark.anyio
@respx.mock
async def test_a_rejected_write_is_a_named_failure() -> None:
    respx.post(READ_URL).mock(return_value=httpx.Response(200, json=ocs_body([])))
    respx.post(CONFIG_URL).mock(return_value=httpx.Response(403, json=ocs_body([])))

    with pytest.raises(ToolError) as excinfo:
        await crypto.data_key(ENV)
    assert excinfo.value.hint


@pytest.mark.anyio
@respx.mock
async def test_a_key_that_disappears_between_write_and_read_back_is_a_named_failure() -> None:
    """Two workers may race; the loser must not run on a key nobody stored."""
    respx.post(READ_URL).mock(return_value=httpx.Response(200, json=ocs_body([])))
    respx.post(CONFIG_URL).mock(return_value=httpx.Response(200, json=ocs_body([])))

    with pytest.raises(ToolError) as excinfo:
        await crypto.data_key(ENV)
    assert crypto.CONFIG_KEY in excinfo.value.message


@pytest.mark.anyio
@respx.mock
async def test_nothing_of_the_key_or_the_plaintext_reaches_the_log(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """T-03-16: not on DEBUG, not truncated, not in the successful case either."""
    respx.post(READ_URL).mock(return_value=httpx.Response(200, json=stored(STORED_KEY_HEX)))

    with caplog.at_level(logging.DEBUG):
        key = await crypto.data_key(ENV)
        blob = crypto.encrypt(key, PLAINTEXT, aad=AAD)
        assert crypto.decrypt(key, blob, aad=AAD) == PLAINTEXT

    assert STORED_KEY_HEX not in caplog.text
    assert STORED_KEY_HEX[:16] not in caplog.text
    assert PLAINTEXT.decode() not in caplog.text
    assert APP_SECRET not in caplog.text


@pytest.mark.anyio
@respx.mock
async def test_a_failure_log_line_repeats_no_value_of_the_request(
    caplog: pytest.LogCaptureFixture,
) -> None:
    respx.post(READ_URL).mock(side_effect=httpx.ConnectError("boom"))

    with caplog.at_level(logging.DEBUG), pytest.raises(ToolError):
        await crypto.data_key(ENV)

    assert APP_SECRET not in caplog.text


# --- source gates ------------------------------------------------------------------


def test_the_key_exchange_uses_the_shared_client_and_never_retries() -> None:
    """Shared pattern 4: one attempt, no retry, no second client with other timeouts."""
    source = inspect.getsource(crypto)
    code = "\n".join(line for line in source.splitlines() if not line.strip().startswith("#"))
    assert "shared_client()" in code
    assert "httpx.AsyncClient(" not in code
    assert "for attempt" not in code
    assert "while True" not in code


def test_the_data_key_is_not_derived_from_the_transport_secret() -> None:
    """T-03-14, D-43: the AppAPI secret is regenerated on every registration."""
    source = inspect.getsource(crypto)
    code = "\n".join(line for line in source.splitlines() if not line.strip().startswith("#"))
    assert "APP_SECRET" not in code
    assert "pbkdf2" not in code.lower()
    assert "hkdf" not in code.lower()
