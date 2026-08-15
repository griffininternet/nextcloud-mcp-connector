"""The browser facing building blocks of phase 3, checked against 03-UI-SPEC.md.

Every page of this phase runs through ``layout.page``. That is the whole reason the module
exists, so the checks here are mostly checks on that one function: the five required
response headers, the per response nonce, the escaping of attacker controlled values and
the accessibility contract of the rendered document.

Two rules drive the harsher checks:

* The client name and the redirect URI arrive from a dynamic client registration, which is
  open by default (D-35). They are attacker input (T-03-20), so the escaping test parses
  the document and counts elements instead of comparing substrings: a substring check
  passes happily while the page grew a second form.
* A consent page that can be framed is a clickjacked consent page (T-03-21), and a cached
  one shows the next user a foreign client name (T-03-25). Both are header checks, and
  they run against every page family, not against one example.
"""

import inspect
import re
from html.parser import HTMLParser

import pytest
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Route
from starlette.testclient import TestClient

from mcp_connector import config
from mcp_connector.exapp.ui import icons, layout, strings

ENV = {config.ENV_PUBLIC_URL: "https://cloud.example.com/exapps/mcp_connector"}
HOST = "cloud.example.com"

#: A client name as a registration could send it: markup, quotes, a line break and a
#: control character. Nothing of it may reach the document as anything but text.
HOSTILE_NAME = '<script>alert("x")</script>\r\n\x07Bad Client'
BENIGN_NAME = "Friendly Client"

REDIRECT_URI = (
    "https://claude.ai/api/mcp/auth_callback?state=0123456789abcdef0123456789abcdef"
    "&flow=connector-authorization-with-a-very-long-query-string"
)


class Document(HTMLParser):
    """A minimal reader for the three questions the checks ask about a rendered page."""

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


def parse(response: Response) -> Document:
    document = Document()
    document.feed(body(response))
    return document


def body(response: Response) -> str:
    return response.body.decode("utf-8")


def sample_page(name: str = BENIGN_NAME, **kwargs: object) -> Response:
    """One page that uses every component, so a single render covers the whole surface."""
    blocks = [
        layout.paragraph(strings.SIGNIN_BODY.format(client=layout.client_name(name), host=HOST)),
        layout.callout(
            "warning",
            strings.CONSENT_WARNING_TITLE,
            strings.CONSENT_WARNING_BODY,
        ),
        layout.detail_list(
            [
                (strings.CONSENT_DETAIL_APP_NAME, layout.client_name(name)),
                (strings.CONSENT_DETAIL_REDIRECT, REDIRECT_URI),
            ]
        ),
        layout.form(
            "/authorize",
            [
                layout.button_secondary(strings.CONSENT_DENY, name="decision", value="deny"),
                layout.button_primary(strings.CONSENT_APPROVE, name="decision", value="approve"),
            ],
            hidden={"state": "abc"},
        ),
        layout.action(strings.ACTION_START_OVER, "/authorize"),
    ]
    return layout.page(
        strings.CONSENT_TITLE.format(client=layout.client_name(name)), blocks, env=ENV, **kwargs
    )  # type: ignore[arg-type]


# --- headers ---------------------------------------------------------------------------


def test_page_answers_html_with_every_required_header() -> None:
    """The five headers of the UI-SPEC, on one function, for every page of the phase."""
    response = sample_page()
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert response.headers["cache-control"] == "no-store"
    policy = response.headers["content-security-policy"]
    for directive in (
        "default-src 'none'",
        "form-action 'self'",
        "frame-ancestors 'none'",
        "base-uri 'none'",
    ):
        assert directive in policy


def test_the_status_code_and_extra_headers_are_passed_through() -> None:
    response = sample_page(status_code=429, headers={"Retry-After": "30"})
    assert response.status_code == 429
    assert response.headers["retry-after"] == "30"
    assert response.headers["cache-control"] == "no-store"


def test_the_page_also_carries_its_headers_through_a_real_route() -> None:
    """The headers survive the ASGI stack, not just the Response object."""

    async def handler(request: object) -> Response:
        return sample_page()

    with TestClient(Starlette(routes=[Route("/consent", handler)])) as http:
        response = http.get("/consent")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert response.headers["cache-control"] == "no-store"
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]


# --- the nonce -------------------------------------------------------------------------


def nonce_of(response: Response) -> str:
    match = re.search(
        r"style-src 'nonce-([A-Za-z0-9_-]+)'", response.headers["content-security-policy"]
    )
    assert match is not None, "the policy must name a nonce for the one style block"
    return match.group(1)


def test_the_csp_nonce_is_the_nonce_of_the_style_tag() -> None:
    response = sample_page()
    nonce = nonce_of(response)
    document = parse(response)
    assert document.tags.count("style") == 1
    assert document.values_of("nonce") == [nonce]


def test_two_pages_carry_two_different_nonces() -> None:
    """A reused nonce is a nonce, and a nonce that is not one allows injected styles."""
    first, second = sample_page(), sample_page()
    assert nonce_of(first) != nonce_of(second)
    assert nonce_of(first) in body(first)
    assert nonce_of(second) in body(second)


# --- no script, no external asset ------------------------------------------------------


def test_the_page_has_no_script_no_event_handler_and_no_style_attribute() -> None:
    document = parse(sample_page(HOSTILE_NAME))
    assert "script" not in document.tags
    offenders = [
        (tag, name)
        for tag, name, _ in document.attributes
        if name.startswith("on") or name == "style"
    ]
    assert offenders == []


def test_no_href_and_no_src_points_at_another_origin() -> None:
    """CSP default-src 'none' already forbids it; the document must not even try."""
    document = parse(sample_page())
    targets = document.values_of("href") + document.values_of("src")
    assert targets, "the sample page has at least one link"
    for target in targets:
        assert "://" not in target
        assert not target.startswith("//")


def test_the_stylesheet_ships_no_external_reference() -> None:
    assert "://" not in layout.STYLESHEET
    assert "@import" not in layout.STYLESHEET
    assert "url(" not in layout.STYLESHEET


# --- escaping --------------------------------------------------------------------------


def test_a_hostile_client_name_does_not_add_a_single_element() -> None:
    """T-03-20: a registration must not be able to write page copy or a second form."""
    benign = parse(sample_page(BENIGN_NAME))
    hostile = parse(sample_page(HOSTILE_NAME))
    assert hostile.tags == benign.tags
    assert "script" not in hostile.tags
    assert "<script" not in body(sample_page(HOSTILE_NAME))


def test_a_hostile_client_name_is_readable_as_text() -> None:
    """Escaped, not swallowed: the user has to see what the app calls itself."""
    document = parse(sample_page(HOSTILE_NAME))
    assert "Bad Client" in document.text
    assert "\x07" not in document.text
    assert "\r" not in document.text


def test_a_long_client_name_is_truncated() -> None:
    long_name = "A" * 200
    rendered = layout.client_name(long_name)
    assert len(rendered) <= layout.CLIENT_NAME_LIMIT
    assert rendered.startswith("AAAA")
    assert long_name not in body(sample_page(long_name))


def test_an_empty_client_name_falls_back_to_a_readable_placeholder() -> None:
    assert layout.client_name("   ") == strings.CLIENT_NAME_FALLBACK
    assert layout.client_name("\x00\x01") == strings.CLIENT_NAME_FALLBACK


def test_a_redirect_uri_is_shown_in_full_and_wraps() -> None:
    """Truncating the return address would hide exactly the part an attacker changed."""
    document = parse(sample_page())
    assert REDIRECT_URI in document.text
    assert ("dd", "class", "mono") in document.attributes
    assert "overflow-wrap: anywhere" in layout.STYLESHEET


# --- structure and accessibility -------------------------------------------------------


def test_the_document_has_one_h1_and_the_three_landmarks() -> None:
    document = parse(sample_page())
    assert document.tags.count("h1") == 1
    for landmark in ("header", "main", "footer"):
        assert document.tags.count(landmark) == 1
    assert ("html", "lang", "en") in document.attributes
    assert body(sample_page()).startswith("<!doctype html>")


def test_buttons_are_buttons_links_are_links_and_no_div_carries_a_role() -> None:
    document = parse(sample_page())
    assert document.tags.count("form") == 1
    assert document.tags.count("button") == 2
    assert document.tags.count("a") == 1
    roles = [tag for tag, name, _ in document.attributes if name == "role"]
    assert "div" not in roles


def test_the_form_is_a_post_with_a_local_action_and_its_hidden_field() -> None:
    document = parse(sample_page())
    assert ("form", "method", "post") in document.attributes
    assert ("form", "action", "/authorize") in document.attributes
    assert ("input", "type", "hidden") in document.attributes
    assert ("input", "name", "state") in document.attributes


def test_a_link_to_another_origin_is_refused() -> None:
    """A link target is never attacker input by accident: it has to be local here."""
    with pytest.raises(ValueError, match="local"):
        layout.link("Start over", "https://evil.example.com/")
    with pytest.raises(ValueError, match="local"):
        layout.link("Start over", "//evil.example.com/")
    with pytest.raises(ValueError, match="local"):
        layout.form("https://evil.example.com/", [])


def test_the_stylesheet_carries_the_focus_ring_and_never_removes_one() -> None:
    assert ":focus-visible" in layout.STYLESHEET
    assert "outline: 3px solid #1F3A5F" in layout.STYLESHEET
    assert "outline-offset: 2px" in layout.STYLESHEET
    assert "outline: none" not in layout.STYLESHEET
    assert "outline:none" not in layout.STYLESHEET


def test_the_stylesheet_keeps_the_touch_target_and_the_light_palette() -> None:
    assert "min-height: 44px" in layout.STYLESHEET
    assert "max-width: 560px" in layout.STYLESHEET
    assert "color-scheme: light" in layout.STYLESHEET
    assert "prefers-color-scheme" not in layout.STYLESHEET
    assert "animation" not in layout.STYLESHEET
    assert "transition" not in layout.STYLESHEET


def test_the_stylesheet_never_borrows_the_nextcloud_palette() -> None:
    """T-03-23: a page that looks like Nextcloud teaches the wrong lesson."""
    assert "0082C9" not in layout.STYLESHEET.upper()


# --- callout ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("kind", "icon"),
    [("warning", icons.WARNING), ("error", icons.CROSS), ("success", icons.CHECK)],
)
def test_every_callout_kind_carries_its_icon_its_title_and_its_body(kind: str, icon: str) -> None:
    rendered = layout.callout(kind, "Unverified client", "Only approve it if you started this.")
    assert icon in rendered
    assert "Unverified client" in rendered
    assert "Only approve it if you started this." in rendered
    assert f"callout-{kind}" in rendered


def test_an_unknown_callout_kind_is_refused() -> None:
    with pytest.raises(ValueError, match="kind"):
        layout.callout("info", "Title", "Body")


def test_a_callout_escapes_its_own_input() -> None:
    rendered = layout.callout("warning", "<b>t</b>", '"x" & <i>y</i>')
    assert "<b>" not in rendered
    assert "<i>" not in rendered
    assert "&lt;b&gt;t&lt;/b&gt;" in rendered


# --- icons -----------------------------------------------------------------------------


def test_there_are_exactly_three_icons() -> None:
    assert sorted(icons.__all__) == ["CHECK", "CROSS", "WARNING"]


@pytest.mark.parametrize("icon", [icons.WARNING, icons.CHECK, icons.CROSS])
def test_every_icon_is_inline_decorative_and_sized(icon: str) -> None:
    assert icon.startswith("<svg")
    assert 'aria-hidden="true"' in icon
    assert 'width="20"' in icon
    assert 'height="20"' in icon
    assert "currentColor" in icon
    assert "<title" not in icon
    assert "://" not in icon


# --- identity of the sender ------------------------------------------------------------


def test_the_wordmark_and_the_host_come_from_the_configuration() -> None:
    document = parse(sample_page())
    assert strings.WORDMARK in document.text
    assert HOST in document.text


def test_the_page_function_never_sees_the_request() -> None:
    """T-03-02 for HTML: a forged Host header must not be able to rename the sender."""
    parameters = inspect.signature(layout.page).parameters
    assert "request" not in parameters
    assert "env" in parameters


def test_the_footer_names_who_may_ask_for_a_password() -> None:
    document = parse(sample_page())
    assert strings.FOOTER_PASSWORD_PROMPT in document.text


def test_a_page_can_carry_its_own_footer() -> None:
    document = parse(sample_page(footer=strings.CONSENT_FOOTER.format(host=HOST)))
    assert "never sees the password you typed" in document.text
