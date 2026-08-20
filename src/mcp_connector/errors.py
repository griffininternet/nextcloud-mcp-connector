"""Error format of the whole connector: one message plus one actionable hint (D-15).

No exception class in this package ever carries credentials or a URL that contains
credentials. The server layer turns these errors into ordinary tool errors so the model
can correct itself; tracebacks are suppressed there on purpose (threat T-01-07).
"""


class ToolError(Exception):
    """A failure a caller can act on: what went wrong plus what to do about it."""

    def __init__(self, message: str, hint: str) -> None:
        super().__init__(f"{message} Hint: {hint}")
        self.message = message
        self.hint = hint


class AppMissingError(ToolError):
    """A Nextcloud app the tool needs (Notes, Deck, ...) is not installed."""


class ConflictError(ToolError):
    """The target already exists. This server never overwrites (TOOL-09)."""


class IssuerRefused(ToolError):
    """The configured public address cannot be the issuer of the authorization server.

    Raised in ``oauth/provider.auth_routes`` when the SDK refuses the issuer, and caught in
    ``entry_exapp.main``, which answers it by dropping the address and building once more
    with the documented default, so the admin form stays reachable (the rescue half of
    CR-01).

    It has a type of its own because that rescue used to catch every :class:`ToolError` of
    the build, which was true about today and an assumption about tomorrow (IN-06): a second
    build time failure would have been logged as an address problem, would have had a
    possibly perfectly good address dropped and would have ended in a second build with a
    confusing double message. Everything else stays what it is and ends the start.
    """
