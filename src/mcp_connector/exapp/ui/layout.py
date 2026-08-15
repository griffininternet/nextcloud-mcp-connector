"""The one function that builds every HTML page of this phase, plus its four blocks.

Why one function: the consent screen is the single place in the whole flow where a human
makes a security decision, and four properties have to hold on every page that leads to it
or away from it. A page must not be framable (T-03-21, clickjacking), must not execute a
script (T-03-22), must not be cached with a foreign client name in it (T-03-25) and must
not leak the flow to a third party through the referrer (T-03-26). Each of those is one
header. Repeating four headers per page means forgetting one on the page that matters, so
:func:`page` sets them and the callers cannot opt out.

The style block is inline with a per response nonce instead of an external stylesheet: a
stylesheet would need its own PUBLIC route in ``appinfo/info.xml``, and D-38 keeps the
route surface as small as it can be. A nonce instead of ``unsafe-inline``, because the
whole point of the policy is that injected markup cannot bring its own styling either.

The palette is deliberately not the Nextcloud palette (T-03-23). A page that looks like
Nextcloud teaches the user that a Nextcloud looking page can come from somewhere else, and
that is the one lesson this flow must never teach: the password prompt is always
Nextcloud's own page, and ours must be visibly ours.

Every value that reaches the document goes through :func:`_escape`, at the single point
where the template writes it. The client name goes through :func:`client_name` first:
it arrives from a dynamic client registration, which is open in the shipped state (D-35),
so it is attacker input. Stripping the control characters and cutting it to
:data:`CLIENT_NAME_LIMIT` is not cosmetics either: without it a registration can name
itself with three lines of fake page copy and a fake button label (T-03-20).
"""

import html
import secrets
from collections.abc import Mapping, Sequence
from urllib.parse import urlsplit

from starlette.responses import HTMLResponse, Response

from ... import config
from ..responses import NO_STORE
from . import icons, strings

__all__ = [
    "CLIENT_NAME_LIMIT",
    "CSP_TEMPLATE",
    "STYLESHEET",
    "action",
    "button_primary",
    "button_secondary",
    "callout",
    "client_name",
    "detail_list",
    "form",
    "link",
    "page",
    "paragraph",
    "section_heading",
    "unordered_list",
]

#: The policy of every HTML answer of this phase. ``default-src 'none'`` is the whole
#: defence: no script source is listed, so there is no script source, and the one style
#: block has to name the nonce of exactly this response.
CSP_TEMPLATE = (
    "default-src 'none'; style-src 'nonce-{nonce}'; form-action 'self'; "
    "frame-ancestors 'none'; base-uri 'none'"
)

#: Bytes of entropy behind the style nonce. 16 bytes is far more than a per response value
#: needs, and it costs nothing.
NONCE_BYTES = 16

#: The rendered client name is cut here (03-UI-SPEC.md, Component Inventory).
CLIENT_NAME_LIMIT = 80

_TRUNCATION_MARK = "..."

_CALLOUT_ICONS = {
    "warning": icons.WARNING,
    "error": icons.CROSS,
    "success": icons.CHECK,
}

_TONES = {"": "", "error": " tone-error", "success": " tone-success"}

#: One block, one nonce, no external asset. The tokens are the ones of 03-UI-SPEC.md:
#: four type sizes, two weights, spacing in multiples of four, 44px as the smallest
#: interactive height, 560px of content width, and a focus ring that is never removed.
STYLESHEET = """
:root { color-scheme: light; }
*, *::before, *::after { box-sizing: border-box; }
body {
  margin: 0;
  padding: 24px 16px;
  background: #F5F6F7;
  color: #1A1A1A;
  font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  font-size: 16px;
  font-weight: 400;
  line-height: 1.5;
}
header, main, footer { max-width: 560px; margin-left: auto; margin-right: auto; }
header { border-bottom: 2px solid #1F3A5F; padding-bottom: 8px; }
.wordmark { font-size: 14px; font-weight: 600; }
.host { font-size: 14px; font-weight: 400; color: #5A6270; }
main { margin-top: 48px; }
footer { margin-top: 32px; }
.card {
  background: #FFFFFF;
  border: 1px solid #D5D8DD;
  border-radius: 8px;
  padding: 24px;
}
h1 {
  display: flex;
  gap: 8px;
  align-items: flex-start;
  font-size: 28px;
  font-weight: 600;
  line-height: 1.2;
  margin: 0 0 24px;
}
h1.tone-error { color: #B3261E; }
h1.tone-success { color: #1E6B3A; }
h2 { font-size: 20px; font-weight: 600; line-height: 1.2; margin: 32px 0 16px; }
p { margin: 0 0 16px; }
p:last-child { margin-bottom: 0; }
.muted { color: #5A6270; font-size: 14px; }
.mono {
  font-family: ui-monospace, SFMono-Regular, "Cascadia Mono", Consolas, monospace;
  font-size: 14px;
  font-weight: 400;
  overflow-wrap: anywhere;
}
a { color: #1F3A5F; }
ul { margin: 0 0 16px; padding-left: 24px; }
li { margin-bottom: 8px; }
dl { margin: 0; }
dt { font-size: 14px; font-weight: 600; margin-top: 16px; }
dd { margin: 4px 0 0; }
.icon { flex: none; }
.callout {
  display: flex;
  gap: 8px;
  margin: 32px 0;
  padding: 16px;
  border: 1px solid #D5D8DD;
  border-radius: 8px;
}
.callout-title { font-size: 14px; font-weight: 600; margin: 0 0 4px; }
.callout-warning { background: #FFF8E6; border-color: #8A5A00; color: #8A5A00; }
.callout-error { background: #FFFFFF; border-color: #B3261E; color: #B3261E; }
.callout-success { background: #FFFFFF; border-color: #1E6B3A; color: #1E6B3A; }
.actions { display: flex; flex-wrap: wrap; gap: 16px; margin-top: 32px; }
button {
  font-family: inherit;
  font-size: 16px;
  font-weight: 600;
  min-height: 44px;
  min-width: 44px;
  padding: 8px 24px;
  border: 1px solid #1F3A5F;
  border-radius: 8px;
  cursor: pointer;
}
.btn-primary { background: #1F3A5F; color: #FFFFFF; }
.btn-secondary { background: #FFFFFF; color: #1F3A5F; }
.action { margin-top: 32px; margin-bottom: 0; }
.action a { display: inline-block; min-height: 44px; padding: 8px 0; }
:focus-visible { outline: 3px solid #1F3A5F; outline-offset: 2px; }
@media (min-width: 600px) { body { padding: 64px 24px; } }
"""


def page(
    title: str,
    blocks: Sequence[str],
    *,
    env: Mapping[str, str] | None = None,
    status_code: int = 200,
    headers: Mapping[str, str] | None = None,
    footer: str | None = None,
    heading_icon: str = "",
    heading_tone: str = "",
) -> Response:
    """Render one page of this phase, with the headers every page of this phase carries.

    ``blocks`` are fragments built by the component functions below, which escape their own
    input. ``title`` is plain text and is escaped here, which is why a caller formats the
    client name into a string constant and hands the result in without touching HTML.

    The sender identity in the bar comes from :func:`mcp_connector.config.public_url` and
    never from the request, exactly like the discovery documents of 03-01 (T-03-02): a
    forged Host header must not be able to relabel who is asking for access. That is also
    why this function takes an environment and not a request.
    """
    nonce = secrets.token_urlsafe(NONCE_BYTES)
    tone = _TONES.get(heading_tone)
    if tone is None:
        raise ValueError(f"unknown heading tone {heading_tone!r}")
    closing = _escape(footer or strings.FOOTER_PASSWORD_PROMPT)

    document = (
        "<!doctype html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{_escape(title)} - {_escape(strings.WORDMARK)}</title>\n"
        f'<style nonce="{nonce}">{STYLESHEET}</style>\n'
        "</head>\n"
        "<body>\n"
        f"{_bar(env)}\n"
        "<main>\n"
        '<div class="card">\n'
        f'<h1 class="heading{tone}">{heading_icon}<span>{_escape(title)}</span></h1>\n'
        f"{''.join(blocks)}\n"
        "</div>\n"
        "</main>\n"
        f'<footer><p class="muted">{closing}</p></footer>\n'
        "</body>\n"
        "</html>\n"
    )
    return HTMLResponse(
        document,
        status_code=status_code,
        headers=_headers(nonce, headers),
    )


def paragraph(text: str, *, muted: bool = False) -> str:
    """One sentence block. Muted is the 14px grey variant, used for secondary lines."""
    css = ' class="muted"' if muted else ""
    return f"<p{css}>{_escape(text)}</p>"


def section_heading(text: str) -> str:
    """The section headings of a page. ``h1`` belongs to :func:`page` alone."""
    return f"<h2>{_escape(text)}</h2>"


def unordered_list(items: Sequence[str]) -> str:
    """A real list, for the grant list of the consent screen."""
    entries = "".join(f"<li>{_escape(item)}</li>" for item in items)
    return f"<ul>{entries}</ul>"


def detail_list(items: Sequence[tuple[str, str]]) -> str:
    """The definition list of the consent screen: term, then value in monospace.

    The values are shown in full and never shortened. A redirect target that is cut off in
    the middle hides exactly the part an attacker would have changed.
    """
    rows = "".join(
        f'<dt>{_escape(term)}</dt><dd class="mono">{_escape(value)}</dd>' for term, value in items
    )
    return f"<dl>{rows}</dl>"


def callout(kind: str, title: str, body: str) -> str:
    """An icon, a title and a body. Never colour alone (03-UI-SPEC.md, Color).

    An unknown kind raises instead of falling back to a neutral box: a warning that
    silently loses its warning look is the failure mode this whole screen exists against.
    """
    icon = _CALLOUT_ICONS.get(kind)
    if icon is None:
        raise ValueError(f"unknown callout kind {kind!r}")
    return (
        f'<div class="callout callout-{kind}">{icon}'
        f'<div><p class="callout-title">{_escape(title)}</p>'
        f"<p>{_escape(body)}</p></div></div>"
    )


def button_primary(label: str, *, name: str, value: str) -> str:
    """The one action that carries the risk of the page. Always inside :func:`form`."""
    return _button(label, name=name, value=value, css="btn-primary")


def button_secondary(label: str, *, name: str, value: str) -> str:
    """The safe action. Rendered before the primary one, so it is reachable first."""
    return _button(label, name=name, value=value, css="btn-secondary")


def form(
    action_path: str,
    buttons: Sequence[str],
    *,
    hidden: Mapping[str, str] | None = None,
) -> str:
    """Wrap the buttons in a POST form, because a GET must never grant anything.

    The hidden fields carry the values that bind the decision to one authorization request,
    including the anti forgery token that the plan owning the route puts in.
    """
    target = _local(action_path)
    fields = "".join(
        f'<input type="hidden" name="{_escape(key)}" value="{_escape(value)}">'
        for key, value in (hidden or {}).items()
    )
    return (
        f'<form method="post" action="{_escape(target)}">'
        f'{fields}<div class="actions">{"".join(buttons)}</div></form>'
    )


def link(label: str, href: str) -> str:
    """An inline link to a path of this application. Link text names the destination."""
    return f'<a href="{_escape(_local(href))}">{_escape(label)}</a>'


def action(label: str, href: str) -> str:
    """A link as the standalone next step of a page, for example on the timeout page."""
    return f'<p class="action">{link(label, href)}</p>'


def client_name(raw: str) -> str:
    """Make an attacker supplied client name safe to show, before it is escaped.

    Escaping alone keeps the markup intact but not the page: a name of two hundred
    characters with line breaks in it can imitate a second paragraph of page copy inside
    the card. So control characters go, runs of whitespace collapse into one blank, and
    the result is cut to :data:`CLIENT_NAME_LIMIT` characters. A name that is empty after
    that is not shown as an empty gap but as the fallback wording, because a nameless app
    asking for access is itself information the user should read.
    """
    printable = "".join(character for character in (raw or "") if character.isprintable())
    collapsed = " ".join(printable.split())
    if not collapsed:
        return strings.CLIENT_NAME_FALLBACK
    if len(collapsed) > CLIENT_NAME_LIMIT:
        return collapsed[: CLIENT_NAME_LIMIT - len(_TRUNCATION_MARK)] + _TRUNCATION_MARK
    return collapsed


def _button(label: str, *, name: str, value: str, css: str) -> str:
    return (
        f'<button class="{css}" type="submit" name="{_escape(name)}" '
        f'value="{_escape(value)}">{_escape(label)}</button>'
    )


def _headers(nonce: str, extra: Mapping[str, str] | None) -> dict[str, str]:
    """The four security headers plus ``no-store``, with the caller merged over them.

    The merge order is the one of :func:`mcp_connector.exapp.responses.json_response`
    (IN-06): extra headers are added on top instead of replacing the base, so a page that
    needs ``Retry-After`` cannot lose ``no-store`` on the way.
    """
    base = {
        "Content-Security-Policy": CSP_TEMPLATE.format(nonce=nonce),
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "no-referrer",
        **NO_STORE,
    }
    return {**base, **(extra or {})}


def _bar(env: Mapping[str, str] | None) -> str:
    """Who is asking, on every single page: the wordmark and the configured instance."""
    return (
        "<header>"
        f'<span class="wordmark">{_escape(strings.WORDMARK)}</span> '
        f'<span class="host">{_escape(_host(env))}</span>'
        "</header>"
    )


def _host(env: Mapping[str, str] | None) -> str:
    configured = config.public_url(env)
    return urlsplit(configured).netloc or configured


def _local(target: str) -> str:
    """Refuse anything that leaves this application.

    Every link and every form action of this phase points at one of our own routes. A
    value that starts a scheme or a protocol relative address would either be a bug or an
    open redirect wearing a link label, and both are cheaper to forbid than to review.
    """
    value = (target or "").strip()
    if not value.startswith("/") or value.startswith("//"):
        raise ValueError(f"{target!r} is not a local path of this application")
    return value


def _escape(value: str) -> str:
    """The single escaping point of the package, quotes included (T-03-20)."""
    return html.escape(str(value), quote=True)
