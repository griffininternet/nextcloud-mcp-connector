"""The authorization server half of the connector (AUTH-02, AUTH-03, AUTH-04, AUTH-07).

The MCP SDK brings the resource server half and the four OAuth endpoint handlers; what
lives here is the part where the security decisions are made: which client may authorize,
which audience a token is bound to, how a refresh rotates, and how the bridge to the
Nextcloud Login Flow v2 works (D-33, D-34, D-35).

Importing this package has no side effects: no route registration, no environment read, no
client creation. Routes are handed out by a factory and attached by ``entry_exapp`` alone,
exactly like the ``exapp`` package does it (D-23, 03-PATTERNS.md, shared pattern 5).

Module layout of this phase, one module per concern:

* ``metadata`` - the three discovery documents (this plan)
* ``provider``, ``verifier``, ``registry``, ``store``, ``crypto``, ``loginflow``, ``consent``
  follow in the later plans of the phase

Nothing is re-exported here on purpose. A package that re-exports its implementations
forces every plan of this phase to edit this one file, which is the merge conflict a
parallel wave does not need.
"""
