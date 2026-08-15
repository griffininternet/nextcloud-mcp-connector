"""The browser facing surface of the authorization flow: one shell, four blocks, seven errors.

Import has no side effects, like every package of this project: nothing here registers a
route, reads the environment or touches a socket at import time. The pages are built by
functions that a route factory calls, and the factories live in the plans that own the
routes (03-04 for the sign in handoff, 03-05 and 03-06 for consent).

``.planning/phases/03-oauth-2-1/03-UI-SPEC.md`` is the binding source for everything in
this package: the required response headers, the spacing scale, the four type sizes, the
palette, the copy of every screen and the wording of the seven error pages. Where this code
and that document disagree, the document wins. Taste does not enter here, because the
consent page is the one place in the phase where a human makes a security decision, and
the value of that decision comes from the page always looking and reading the same way.

The modules, in the order they depend on each other:

* :mod:`.strings` holds every user facing sentence, one constant per sentence.
* :mod:`.icons` holds the three inline SVG constants, and nothing else.
* :mod:`.layout` holds the one page function, the escaping and the four components.
* :mod:`.errors` turns one table into the seven error pages, through that same function.
"""
