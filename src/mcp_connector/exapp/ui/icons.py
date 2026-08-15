"""The three inline icons of the phase, as module constants (03-UI-SPEC.md, Design System).

Inline and not an icon package, for the same reason there is no web font and no stylesheet
route: ``default-src 'none'`` forbids every external asset, and a consent screen is the
last place to grow a supply chain for three shapes. The ``xmlns`` attribute is left out on
purpose as well: inside an HTML document the parser puts ``<svg>`` into the SVG namespace
by itself, and the attribute would be the only absolute URL in the whole surface.

Every icon is 20 by 20, paints in ``currentColor`` so the surrounding text colour is the
only colour decision, and carries ``aria-hidden="true"`` without a ``<title>``: each icon
always stands next to its own text label, so a screen reader that announced the icon too
would read the same thing twice.
"""

__all__ = ["CHECK", "CROSS", "WARNING"]

_OPEN = (
    '<svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" '
    'focusable="false" class="icon">'
)

#: Unverified client, and every other callout that asks the user to slow down.
WARNING = (
    f'{_OPEN}<path d="M10 2.5 1.5 17.5h17L10 2.5Z"/><path d="M10 8v3.5"/>'
    '<path d="M10 14.8h0.01"/></svg>'
)

#: The connection succeeded. Paired with the word "Connected", never used alone.
CHECK = f'{_OPEN}<path d="M3 10.5 8 15.5 17 5"/></svg>'

#: Every error page and the denied result. Paired with a heading that names the problem.
CROSS = f'{_OPEN}<path d="M5 5 15 15"/><path d="M15 5 5 15"/></svg>'
