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
