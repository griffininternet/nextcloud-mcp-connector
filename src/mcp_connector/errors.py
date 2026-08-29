"""Error format of the whole connector: one message plus one actionable hint (D-15).

No exception class in this package ever carries credentials or a URL that contains
credentials. The server layer turns these errors into ordinary tool errors so the model
can correct itself; tracebacks are suppressed there on purpose (threat T-01-07).

The ``reason`` of an error is the only part of it that may ever leave for a log
(threat T-18-01). ``message`` and ``hint`` are written for the model and are therefore
concrete: ``dav.py`` says ``f"No permission to write to {path}."`` and names a real path,
``caldav.py`` names a real calendar. That is result content, it belongs in the tool answer
and in no log. A fixed identifier carries the reason without carrying the case.
"""

# The six rejection reasons. Each line says which case sets it.
REASON_UNSPECIFIED = "unspecified"  # not determined; honest instead of guessed
REASON_PERMISSION_DENIED = "permission_denied"  # Nextcloud answered 403
REASON_UNKNOWN_ID = "unknown_id"  # Nextcloud answered 404, 409 or 998
REASON_TIMEOUT = "timeout"  # Nextcloud did not answer in time
REASON_UNREACHABLE = "unreachable"  # Nextcloud could not be reached at all
REASON_GUARD_TRIPPED = "guard_tripped"  # a guard of this server stopped the call

# Frozen on purpose: a seventh reason is a decision and belongs into a review, not into a
# diff. ``tests/unit/test_errors_reason.py`` walks src/ and fails on any ``reason=`` that is
# not one of these names.
REASONS: frozenset[str] = frozenset(
    {
        REASON_UNSPECIFIED,
        REASON_PERMISSION_DENIED,
        REASON_UNKNOWN_ID,
        REASON_TIMEOUT,
        REASON_UNREACHABLE,
        REASON_GUARD_TRIPPED,
    }
)


class ToolError(Exception):
    """A failure a caller can act on: what went wrong plus what to do about it."""

    def __init__(self, message: str, hint: str, *, reason: str = REASON_UNSPECIFIED) -> None:
        # The default is the reason why the roughly 223 other raise sites stay untouched
        # (D-17): this phase puts a module next to the error handling, it does not tidy the
        # error handling up. Everything without a reason reads as "not determined", which is
        # honest, and not as a guessed cause.
        super().__init__(f"{message} Hint: {hint}")
        self.message = message
        self.hint = hint
        self.reason = reason


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
