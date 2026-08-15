"""The AppAPI side of the connector: handshake, lifecycle and the progress push.

Two decisions define this package (D-23 and D-24):

* The ExApp is a fourth operating mode of the same code base, not a second project. The
  stdio server and the standalone HTTP server of phase 1 stay exactly as they were, which
  is why nothing in this package registers itself on the shared server object at import
  time. Routes are handed out by a factory and attached by ``entry_exapp`` alone.
* The AppAPI contract is implemented here instead of pulled in with ``nc_py_api``. The
  incoming half is three headers and two comparisons, the outgoing half is four headers.
  The library would add FastAPI and niquests to a project that is Starlette only.

Importing this package has no side effects: no route registration, no environment read,
no client creation.
"""
