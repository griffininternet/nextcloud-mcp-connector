"""The data key of this phase and the encryption every stored secret goes through.

Threats covered here: T-03-10 (the store file leaves the volume), T-03-12 (ciphertexts
moved between rows), T-03-14 (a key derived from the transport secret dies on the next
registration) and T-03-16 (a key or a plaintext in a log record).

Nothing here opens a socket. The two crypto functions take the key as a parameter, which
is what lets every check below run without an environment and without Nextcloud, and the
one outgoing OCS call is answered by respx.
"""

import base64
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


#: The id both forms of one connection are about, which is the whole reason ME-01 exists.
HANDLE = "the-one-id-both-forms-are-about"

#: The start of a window, so no case below sits on a boundary by accident. The clock is a
#: parameter of every function under test here, so nothing in this file waits for time.
NOW = float((1_776_000_000 // 3600) * 3600)


def test_one_handle_under_two_purposes_gives_two_different_values() -> None:
    """ME-01: two privileged actions of this app are about the same id.

    An authorization is written under the id of the flow it was born in, so ``auth_id`` and
    ``flow_id`` are one string, and a value derived from the string alone authorised both
    "approve this authorization request" and "end this connection". Domain separation is
    exactly what stops a stolen value from changing its meaning.
    """
    purposes = (crypto.PURPOSE_CONSENT, crypto.PURPOSE_DISCONNECT, crypto.PURPOSE_SWITCH)

    values = {
        purpose: crypto.form_token(KEY, HANDLE, purpose=purpose, now=NOW) for purpose in purposes
    }

    assert len(set(values.values())) == len(purposes), "one value per purpose, never shared"
    assert (
        crypto.form_token(KEY, HANDLE, purpose=crypto.PURPOSE_CONSENT, now=NOW)
        == values[crypto.PURPOSE_CONSENT]
    ), "derived and not stored: the same render in the same window gives the same value"
    assert (
        crypto.form_token(OTHER_KEY, HANDLE, purpose=crypto.PURPOSE_CONSENT, now=NOW)
        != values[crypto.PURPOSE_CONSENT]
    ), "and another deployment cannot produce it"


def test_the_purpose_and_the_handle_cannot_be_shifted_into_each_other() -> None:
    """The separator is what makes the two fields two fields (T-03-50).

    Neither value is attacker controlled today, and this holds the property that lets it
    stay that way: a purpose that ends in the start of a handle may not collide with the
    next pair.
    """
    assert crypto.form_token(KEY, "b:c", purpose="a", now=NOW) != crypto.form_token(
        KEY, "c", purpose="a:b", now=NOW
    )


# --- the time window of a form value (BL-08, ME-02) --------------------------------


def test_the_window_is_an_hour_and_a_later_window_is_another_value() -> None:
    """BL-08: without a window the value of an account never changes at all.

    The only other rotation point would be the data key, and rotating that makes every
    stored app password unreadable, so the window is the one that can move.
    """
    assert crypto.FORM_TOKEN_WINDOW == 3600

    this_hour = crypto.form_token(KEY, HANDLE, purpose=crypto.PURPOSE_SWITCH, now=NOW)
    still_this_hour = crypto.form_token(
        KEY, HANDLE, purpose=crypto.PURPOSE_SWITCH, now=NOW + crypto.FORM_TOKEN_WINDOW - 1
    )
    next_hour = crypto.form_token(
        KEY, HANDLE, purpose=crypto.PURPOSE_SWITCH, now=NOW + crypto.FORM_TOKEN_WINDOW
    )

    assert this_hour == still_this_hour, "a page rendered twice in one window carries one value"
    assert this_hour != next_hour


@pytest.mark.parametrize(
    ("offset", "accepted"),
    [
        (0, True),
        (crypto.FORM_TOKEN_WINDOW - 1, True),
        (-1, True),
        (-crypto.FORM_TOKEN_WINDOW, True),
        (-crypto.FORM_TOKEN_WINDOW - 1, False),
        (-2 * crypto.FORM_TOKEN_WINDOW, False),
        (crypto.FORM_TOKEN_WINDOW, False),
    ],
    ids=[
        "this window",
        "the end of this window",
        "the previous window, one second back",
        "the start of the previous window",
        "the window before that",
        "two windows back",
        "a window that has not started yet",
    ],
)
def test_this_window_and_the_previous_one_are_accepted_and_nothing_else(
    offset: int, accepted: bool
) -> None:
    """Two windows, so a form that was open across an hour boundary still submits once.

    The price is written down and chosen (BL-08): a page left open for more than two
    windows is refused, and the refusal is the quiet one every wrong value gets.
    """
    presented = crypto.form_token(KEY, HANDLE, purpose=crypto.PURPOSE_CONSENT, now=NOW + offset)

    valid = crypto.form_token_valid(KEY, HANDLE, presented, purpose=crypto.PURPOSE_CONSENT, now=NOW)

    assert valid is accepted


def test_the_purpose_still_binds_in_both_accepted_windows() -> None:
    """ME-01 does not weaken because a second window is accepted now."""
    this_window = crypto.form_token(KEY, HANDLE, purpose=crypto.PURPOSE_DISCONNECT, now=NOW)
    previous = crypto.form_token(
        KEY, HANDLE, purpose=crypto.PURPOSE_DISCONNECT, now=NOW - crypto.FORM_TOKEN_WINDOW
    )

    for presented in (this_window, previous):
        assert (
            crypto.form_token_valid(
                KEY, HANDLE, presented, purpose=crypto.PURPOSE_DISCONNECT, now=NOW
            )
            is True
        )
        assert (
            crypto.form_token_valid(KEY, HANDLE, presented, purpose=crypto.PURPOSE_CONSENT, now=NOW)
            is False
        )


def test_another_handle_and_another_deployment_are_refused_in_every_window() -> None:
    other_handle = crypto.form_token(
        KEY, "another-connection", purpose=crypto.PURPOSE_CONSENT, now=NOW
    )
    other_key = crypto.form_token(OTHER_KEY, HANDLE, purpose=crypto.PURPOSE_CONSENT, now=NOW)

    assert (
        crypto.form_token_valid(KEY, HANDLE, other_handle, purpose=crypto.PURPOSE_CONSENT, now=NOW)
        is False
    )
    assert (
        crypto.form_token_valid(KEY, HANDLE, other_key, purpose=crypto.PURPOSE_CONSENT, now=NOW)
        is False
    )


@pytest.mark.parametrize("presented", ["", "   ", "not-a-value", "0" * 64])
def test_a_value_that_is_not_one_is_refused_and_never_raises(presented: str) -> None:
    """The value arrives from a request, so every shape of it has to be an answer."""
    assert (
        crypto.form_token_valid(KEY, HANDLE, presented, purpose=crypto.PURPOSE_SWITCH, now=NOW)
        is False
    )


def test_without_a_time_both_halves_read_the_same_clock(monkeypatch: pytest.MonkeyPatch) -> None:
    """The parameter is for tests; the callers pass none and must land in the same window."""
    monkeypatch.setattr(crypto, "_unix_time", lambda: NOW)
    stale = crypto.form_token(
        KEY, HANDLE, purpose=crypto.PURPOSE_SWITCH, now=NOW - crypto.FORM_TOKEN_WINDOW
    )
    expired = crypto.form_token(
        KEY, HANDLE, purpose=crypto.PURPOSE_SWITCH, now=NOW - 2 * crypto.FORM_TOKEN_WINDOW
    )

    rendered = crypto.form_token(KEY, HANDLE, purpose=crypto.PURPOSE_SWITCH)

    assert rendered == crypto.form_token(KEY, HANDLE, purpose=crypto.PURPOSE_SWITCH, now=NOW)
    assert crypto.form_token_valid(KEY, HANDLE, rendered, purpose=crypto.PURPOSE_SWITCH) is True
    assert crypto.form_token_valid(KEY, HANDLE, stale, purpose=crypto.PURPOSE_SWITCH) is True
    assert crypto.form_token_valid(KEY, HANDLE, expired, purpose=crypto.PURPOSE_SWITCH) is False


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


# --- deleting the key, the last step of the purge (plan 05-06) ---------------------


@pytest.mark.anyio
@respx.mock
async def test_delete_key_sends_one_delete_that_names_the_config_key() -> None:
    """The third verb of this resource, on the same path the write uses."""
    route = respx.delete(CONFIG_URL).mock(return_value=httpx.Response(200, json=ocs_body([])))

    assert await crypto.delete_key(ENV) is True

    assert route.call_count == 1, "one attempt, no retry"
    sent = route.calls.last.request
    assert sent.method == "DELETE"
    assert str(sent.url) == CONFIG_URL, "the write path, not the read path with its suffix"
    assert json.loads(sent.content) == {"configKeys": [crypto.CONFIG_KEY]}
    assert sent.headers["OCS-APIRequest"] == "true"
    assert sent.headers["EX-APP-ID"] == APP_ID
    assert sent.headers["EX-APP-VERSION"] == APP_VERSION
    assert sent.headers["AUTHORIZATION-APP-API"], "the app context token of an ExApp"


@pytest.mark.anyio
@respx.mock
@pytest.mark.parametrize("status_code", [400, 401, 500])
async def test_a_refused_deletion_is_false_and_one_log_line(
    caplog: pytest.LogCaptureFixture, status_code: int
) -> None:
    """A failure the caller reports as a number: the purge itself may not be stopped by it."""
    respx.delete(CONFIG_URL).mock(return_value=httpx.Response(status_code, json={}))

    with caplog.at_level(logging.DEBUG):
        assert await crypto.delete_key(ENV) is False

    assert [record for record in caplog.records if record.levelno >= logging.ERROR]


@pytest.mark.anyio
@respx.mock
async def test_a_deletion_that_finds_no_key_is_true_and_no_error(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """404 is this endpoint saying it deleted zero rows, so the key is not there.

    ``AppConfigController::deleteAppConfigValues`` raises ``OCSNotFoundException`` ("No
    appconfig_ex values deleted") when nothing matched, and that is the end state the caller
    asked for. Reporting ``key_deleted: false`` for it would tell an administrator to go
    looking for a value that does not exist (measured against AppAPI 34.0.0, plan 05-08).
    """
    respx.delete(CONFIG_URL).mock(return_value=httpx.Response(404, json={}))

    with caplog.at_level(logging.DEBUG):
        assert await crypto.delete_key(ENV) is True

    assert not [record for record in caplog.records if record.levelno >= logging.ERROR]


@pytest.mark.anyio
@respx.mock
async def test_a_deletion_that_does_not_reach_nextcloud_is_false_and_never_raises(
    caplog: pytest.LogCaptureFixture,
) -> None:
    respx.delete(CONFIG_URL).mock(side_effect=httpx.ConnectError("no route to nextcloud"))

    with caplog.at_level(logging.DEBUG):
        assert await crypto.delete_key(ENV) is False

    assert [record for record in caplog.records if record.levelno >= logging.ERROR]


@pytest.mark.anyio
async def test_a_deletion_without_a_deploy_environment_is_false_and_touches_nothing(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """An incomplete deploy environment is a startup problem, not an exception here.

    No respx route at all in this check, which is the assertion: a missing variable is
    refused before anything opens a socket.
    """
    with caplog.at_level(logging.DEBUG):
        assert await crypto.delete_key({}) is False

    assert [record for record in caplog.records if record.levelno >= logging.ERROR]


@pytest.mark.anyio
@respx.mock
@pytest.mark.parametrize("outcome", ["ok", "refused", "unreachable"])
async def test_no_deletion_log_line_carries_key_material_or_the_app_secret(
    caplog: pytest.LogCaptureFixture, outcome: str
) -> None:
    """T-03-16 and security domain V7: the headers carry the secret, the value is a key."""
    route = respx.delete(CONFIG_URL)
    if outcome == "unreachable":
        route.mock(side_effect=httpx.ConnectError("no route to nextcloud"))
    else:
        route.mock(return_value=httpx.Response(200 if outcome == "ok" else 500, json={}))

    with caplog.at_level(logging.DEBUG):
        await crypto.delete_key(ENV)

    logged = "\n".join(record.getMessage() for record in caplog.records)
    assert APP_SECRET not in logged
    assert base64.b64encode(f":{APP_SECRET}".encode()).decode() not in logged
    assert STORED_KEY_HEX not in logged
    assert STORED_KEY_HEX[:16] not in logged


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
