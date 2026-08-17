"""The connections page of EXAPP-02: the four screens and E8 (04-UI-SPEC.md, S5 to S8).

Two rules drive the harsher checks of this file, both inherited from phase 3:

* the app name of a row comes from a dynamic client registration, so it is attacker input
  (T-03-20, T-04-34). The escaping check therefore parses the document and compares the
  element sequence instead of looking for a substring: a substring check passes happily
  while the page grew a second form;
* the connection handle is the value a stranger would guess (T-04-31), so it may travel in
  a hidden field and nowhere else.

Nothing here talks to Nextcloud: the pages are pure functions of their arguments, and the
host in every sentence comes from the configured public URL and never from a request
(T-03-02).
"""

import calendar
import re
from html.parser import HTMLParser

from starlette.responses import Response

from mcp_connector import config
from mcp_connector.exapp.ui import connections as ui
from mcp_connector.exapp.ui import errors, icons, layout, strings

PUBLIC_URL = "https://cloud.example.com/exapps/mcp_connector"
HOST = "cloud.example.com"
PREFIX = "/exapps/mcp_connector"

ENV = {config.ENV_PUBLIC_URL: PUBLIC_URL}

NC_USER = "alice"

CLIENT_ID = "9d0f8f1a-0b3c-4a0e-9f4c-000000000001"
CLIENT_NAME = "Claude"
AUTH_ID = "authorization-of-alice-0001"
SECOND_AUTH_ID = "authorization-of-alice-0002"
TOKEN = "an-anti-forgery-value-of-this-row"
SWITCH_TOKEN = "an-anti-forgery-value-of-the-switch"

#: 12 August 2026, 21:30 UTC. Late enough in the day that a local zone east of UTC would
#: render the next day, which is how the UTC rule of 04-UI-SPEC.md S5 is asserted.
CREATED_AT = calendar.timegm((2026, 8, 12, 21, 30, 0, 0, 0, 0))
CONNECTED_ON = "12 August 2026"

#: The section heading as it stands in the document. Compared as markup on purpose: the
#: words "Connected apps" also stand inside the sentence of the switch, so a bare substring
#: would find the wrong one and an order check would silently assert nothing.
SECTION_HEADING = f"<h2>{strings.CONNECTIONS_SECTION}</h2>"

#: A client name as a registration could send it: markup, quotes, a line break and a
#: control character. Nothing of it may reach the document as anything but text.
HOSTILE_NAME = '<script>alert("x")</script>\r\n\x07Bad Client'


class Document(HTMLParser):
    """A minimal reader for the questions these checks ask about a rendered page."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tags: list[str] = []
        self.attributes: list[tuple[str, str, str | None]] = []
        self.chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tags.append(tag)
        for name, value in attrs:
            self.attributes.append((tag, name, value))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)

    def handle_data(self, data: str) -> None:
        self.chunks.append(data)

    @property
    def text(self) -> str:
        return "".join(self.chunks)

    def values_of(self, attribute: str) -> list[str]:
        return [value or "" for _, name, value in self.attributes if name == attribute]


def body(response: Response) -> str:
    return bytes(response.body).decode("utf-8")


def parse(response: Response) -> Document:
    document = Document()
    document.feed(body(response))
    return document


def connection(
    *,
    auth_id: str = AUTH_ID,
    client_name: str = CLIENT_NAME,
    client_id: str = CLIENT_ID,
    created_at: int = CREATED_AT,
    token: str = TOKEN,
) -> ui.Connection:
    return ui.Connection(
        auth_id=auth_id,
        client_name=client_name,
        client_id=client_id,
        created_at=created_at,
        token=token,
    )


def listing(
    *,
    rows: list[ui.Connection] | None = None,
    paused: bool = False,
    result: str = "",
    result_client: str = "",
) -> Response:
    return ui.connections_page(
        [connection()] if rows is None else rows,
        user=NC_USER,
        paused=paused,
        switch_token=SWITCH_TOKEN,
        result=result,
        result_client=result_client,
        env=ENV,
    )


def order_of(text: str, *needles: str) -> list[int]:
    """Where each of these sentences stands in the document, so an order can be asserted."""
    places = []
    for needle in needles:
        place = text.find(needle)
        assert place >= 0, f"{needle!r} is not in the page at all"
        places.append(place)
    return places


# --- S5, the list ------------------------------------------------------------------


def test_the_list_shows_every_fact_of_a_connection_once() -> None:
    """S5: who is asking, who is signed in, and the three facts of a row."""
    document = parse(listing())

    assert strings.WORDMARK in document.text
    assert HOST in document.text
    assert strings.CONNECTIONS_TITLE in document.text
    assert strings.CONSENT_IDENTITY.format(user=NC_USER, host=HOST) in document.text
    assert strings.CONNECTIONS_SECTION in document.text
    assert CLIENT_NAME in document.text
    assert CLIENT_ID in document.text, "the client id is shown in full and never shortened"
    assert strings.CONNECTIONS_ROW_CONNECTED.format(date=CONNECTED_ON) in document.text
    assert strings.CONNECTIONS_FOOTNOTE in document.text
    assert strings.CONNECT_TITLE in document.text, "the way to the onboarding page"
    assert strings.FOOTER_PASSWORD_PROMPT in document.text


def test_the_list_is_a_real_list_with_one_item_per_connection() -> None:
    """A screen reader has to hear how many connections there are (04-UI-SPEC.md, A11y)."""
    document = parse(listing(rows=[connection(), connection(auth_id=SECOND_AUTH_ID)]))

    assert document.tags.count("li") == 2
    assert "table" not in document.tags
    assert document.values_of("class").count("row") == 2


def test_every_row_carries_its_own_form_and_its_own_accessible_name() -> None:
    """One form per row, and a button whose name is not five times the same word."""
    document = parse(listing(rows=[connection(), connection(auth_id=SECOND_AUTH_ID)]))
    text = body(listing())

    assert document.tags.count("form") == 3, "two rows plus the switch"
    assert f'aria-label="Disconnect {CLIENT_NAME}"' in text
    assert f'action="{PREFIX}{ui.CONNECTIONS_PATH}"' in text


def test_the_date_of_a_row_is_day_month_year_in_utc() -> None:
    """12 August 2026, not 12/08/2026 and not the next day of a local zone."""
    text = body(listing())

    assert CONNECTED_ON in text
    assert "13 August 2026" not in text, "the date is computed in UTC, not in a local zone"
    assert not re.search(r"\d{2}/\d{2}/\d{4}", text)
    assert "21:30" not in text, "no time of day in a list whose unit is a connection"


def test_the_handle_of_a_row_is_never_visible_text() -> None:
    """T-04-31: the handle of a credential travels in a hidden field and nowhere else."""
    response = listing()

    assert AUTH_ID not in parse(response).text
    assert f'value="{AUTH_ID}"' in body(response)


def test_the_switch_block_is_the_on_state_plus_a_secondary_button() -> None:
    """Access on: no accent on this page, and the brake is present but not advertised."""
    text = body(listing())

    assert strings.SWITCH_ON_STATE in text
    assert strings.SWITCH_TURN_OFF in text
    assert f'class="btn-secondary" type="submit" name="{ui.ACTION_FIELD}"' in text
    assert f'value="{ui.ACTION_PAUSE}"' in text
    assert strings.CONNECTIONS_PAUSED_TITLE not in text
    assert '<button class="btn-primary"' not in text, "access on: this page has no accent button"


def test_a_paused_account_gets_the_primary_button_and_the_warning() -> None:
    """The named accent exception: the page state is degraded, so the way back is primary."""
    response = listing(paused=True)
    text = body(response)

    assert strings.SWITCH_OFF_STATE in text
    assert strings.SWITCH_TURN_ON in text
    assert f'value="{ui.ACTION_RESUME}"' in text
    assert "btn-primary" in text
    assert strings.CONNECTIONS_PAUSED_TITLE in parse(response).text
    assert strings.CONNECTIONS_PAUSED_BODY in parse(response).text
    assert icons.WARNING in text


def test_the_switch_block_stands_directly_above_the_pause_warning() -> None:
    """The callout stops being a pointer to Nextcloud: the way back is one line above it."""
    state, warning, section = order_of(
        body(listing(paused=True)),
        strings.SWITCH_OFF_STATE,
        strings.CONNECTIONS_PAUSED_TITLE,
        SECTION_HEADING,
    )

    assert state < warning < section


def test_the_paused_body_no_longer_points_at_the_nextcloud_settings() -> None:
    """Amended 2026-08-17: the switch sits on this page, so the pointer sentence is gone."""
    assert strings.SETTINGS_PLACE not in strings.CONNECTIONS_PAUSED_BODY
    assert strings.SETTINGS_PLACE in strings.ACCESS_DISABLED_DESCRIPTION


# --- S6, the empty state -----------------------------------------------------------


def test_the_empty_state_is_the_same_shell_and_answers_200() -> None:
    """S6: a state of the same page and not an error."""
    response = listing(rows=[])
    document = parse(response)

    assert response.status_code == 200
    assert strings.CONNECTIONS_EMPTY_TITLE in document.text
    assert strings.CONNECTIONS_EMPTY_BODY in document.text
    assert strings.CONSENT_IDENTITY.format(user=NC_USER, host=HOST) in document.text
    assert strings.CONNECTIONS_FOOTNOTE in document.text
    assert strings.CONNECT_TITLE in document.text
    assert "ul" not in document.tags, "no empty list, and no section heading above one"
    assert SECTION_HEADING not in body(response)


def test_the_empty_state_keeps_the_switch_and_its_warning() -> None:
    """The switch belongs to the account, not to the list, so it survives an empty one."""
    document = parse(listing(rows=[], paused=True))

    assert strings.SWITCH_OFF_STATE in document.text
    assert strings.CONNECTIONS_PAUSED_TITLE in document.text


# --- S7, the confirmation ----------------------------------------------------------


def test_the_confirm_page_names_the_app_and_the_limit_of_the_consequence() -> None:
    document = parse(ui.confirm_page(connection(), env=ENV))

    assert strings.DISCONNECT_TITLE.format(client=CLIENT_NAME) in document.text
    assert strings.DISCONNECT_BODY.format(client=CLIENT_NAME) in document.text
    assert strings.DISCONNECT_AGAIN in document.text
    assert strings.CONSENT_DETAIL_APP_NAME in document.text
    assert strings.CONSENT_DETAIL_CLIENT_ID in document.text
    assert strings.CONNECTIONS_DETAIL_CONNECTED in document.text
    assert CONNECTED_ON in document.text


def test_the_confirm_page_offers_keep_before_disconnect_in_one_form() -> None:
    """The safe action is reachable first, exactly as deny comes before approve (S3)."""
    response = ui.confirm_page(connection(), env=ENV)
    text = body(response)
    keep, disconnect = order_of(
        text, f">{strings.DISCONNECT_KEEP}<", f">{strings.DISCONNECT_ACTION}<"
    )

    assert keep < disconnect
    assert parse(response).tags.count("form") == 1
    assert text.count("<button") == 2
    assert f'class="btn-primary" type="submit" name="{ui.ACTION_FIELD}"' in text
    assert f'value="{ui.ACTION_DISCONNECT}"' in text


def test_the_confirm_page_opens_with_the_focus_on_its_heading() -> None:
    """A page that opens with the acting button focused turns a stray Enter into the act."""
    text = body(ui.confirm_page(connection(), env=ENV))

    assert '<h1 class="heading" tabindex="-1" autofocus>' in text


def test_the_confirm_page_carries_the_handle_and_the_hmac_as_hidden_fields_only() -> None:
    response = ui.confirm_page(connection(), env=ENV)
    document = parse(response)
    text = body(response)

    assert AUTH_ID not in document.text
    assert TOKEN not in document.text
    assert f'<input type="hidden" name="{ui.AUTH_PARAM}" value="{AUTH_ID}">' in text
    assert f'<input type="hidden" name="{ui.CONFIRM_PARAM}" value="{TOKEN}">' in text


# --- S8, the result of a disconnect ------------------------------------------------


def test_a_finished_disconnect_answers_the_list_with_the_success_callout() -> None:
    response = listing(rows=[], result=ui.RESULT_DONE, result_client=CLIENT_NAME)
    document = parse(response)

    assert response.status_code == 200
    assert strings.DISCONNECT_DONE_TITLE in document.text
    assert strings.DISCONNECT_DONE_BODY.format(client=CLIENT_NAME) in document.text
    assert icons.CHECK in body(response)


def test_a_disconnect_of_something_that_is_gone_says_so_calmly() -> None:
    response = listing(result=ui.RESULT_GONE)
    document = parse(response)

    assert response.status_code == 200
    assert strings.DISCONNECT_GONE_TITLE in document.text
    assert strings.DISCONNECT_GONE_BODY in document.text
    assert icons.WARNING in body(response)


def test_the_result_callout_stands_before_the_pause_warning() -> None:
    """Both can appear at once, and the order is fixed: result first, condition second."""
    result, warning, section = order_of(
        body(listing(paused=True, result=ui.RESULT_DONE, result_client=CLIENT_NAME)),
        strings.DISCONNECT_DONE_TITLE,
        strings.CONNECTIONS_PAUSED_TITLE,
        SECTION_HEADING,
    )

    assert result < warning < section


# --- the attacker input of this surface --------------------------------------------


def test_a_hostile_client_name_does_not_add_a_single_element() -> None:
    """T-04-34: a registration must not be able to write page copy or a second form."""
    benign = parse(listing())
    hostile = parse(listing(rows=[connection(client_name=HOSTILE_NAME)]))

    assert hostile.tags == benign.tags
    assert "script" not in hostile.tags
    assert "<script" not in body(listing(rows=[connection(client_name=HOSTILE_NAME)]))


def test_a_hostile_client_name_is_readable_as_text() -> None:
    """Escaped, not swallowed: the user has to see what the app calls itself."""
    document = parse(listing(rows=[connection(client_name=HOSTILE_NAME)]))

    assert "Bad Client" in document.text
    assert "\x07" not in document.text
    assert "\r" not in document.text


def test_a_hostile_client_name_stays_text_on_every_screen_of_this_family() -> None:
    """The confirmation page and the result callout carry the same name (T-04-34)."""
    confirm = parse(ui.confirm_page(connection(client_name=HOSTILE_NAME), env=ENV))
    result = parse(listing(result=ui.RESULT_DONE, result_client=HOSTILE_NAME))

    assert "script" not in confirm.tags
    assert "script" not in result.tags
    assert "Bad Client" in confirm.text
    assert "Bad Client" in result.text


def test_a_nameless_registration_is_shown_as_the_fallback_wording() -> None:
    document = parse(listing(rows=[connection(client_name="")]))

    assert strings.CLIENT_NAME_FALLBACK in document.text


# --- E8, not signed in -------------------------------------------------------------


def test_e8_is_a_403_that_names_the_host_and_offers_no_link() -> None:
    """403 and not 401: this surface never puts a password prompt in front of a user."""
    response, reference = errors.error_page("E8", env=ENV)
    document = parse(response)

    assert response.status_code == 403
    assert reference == "", "E8 is not the generic page and needs no reference"
    assert strings.ERROR_SIGN_IN_TITLE in document.text
    assert strings.ERROR_SIGN_IN_BODY.format(host=HOST) in document.text
    assert "a" not in document.tags, "no invented link to a sign in page"
    assert "{host}" not in document.text


def test_e8_is_a_row_of_the_existing_table_and_not_a_new_mechanism() -> None:
    assert "E8" in errors.CODES
    assert errors.CODES.index("E8") == len(errors.CODES) - 2, "E8 stands before the generic page"


# --- the stylesheet and the icons --------------------------------------------------


def test_the_row_list_is_the_one_new_primitive_of_the_stylesheet() -> None:
    """Three rules, exactly the ones of the component inventory, and no new value."""
    assert "ul.rows" in layout.STYLESHEET
    assert "li.row" in layout.STYLESHEET
    assert ".row-title" in layout.STYLESHEET
    assert "border-top: 1px solid #D5D8DD" in layout.STYLESHEET
    assert layout.STYLESHEET.count("#") == len(re.findall(r"#[0-9A-F]{6}", layout.STYLESHEET))


def test_this_phase_adds_no_fourth_icon() -> None:
    """An icon that appears once is an icon nobody learns (04-UI-SPEC.md)."""
    shapes = [name for name in vars(icons) if name.isupper() and not name.startswith("_")]

    assert sorted(shapes) == ["CHECK", "CROSS", "WARNING"]


def test_every_page_of_this_family_carries_the_five_required_headers() -> None:
    """The PHP proxy caches for 3600 seconds unless told otherwise (T-04-32)."""
    for response in (listing(), listing(rows=[]), ui.confirm_page(connection(), env=ENV)):
        assert response.headers["cache-control"] == "no-store"
        assert response.headers["x-frame-options"] == "DENY"
        assert response.headers["referrer-policy"] == "no-referrer"
        assert "form-action 'self'" in response.headers["content-security-policy"]
        assert response.headers["content-type"] == "text/html; charset=utf-8"
