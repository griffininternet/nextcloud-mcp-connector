"""Every user facing sentence of the phase, one constant per sentence (03-UI-SPEC.md).

The separation is not tidiness. A later locale has to be a data change and never a rewrite
of the templates, so no template function in this package carries a literal a user reads.
That is the same rule the ``_HINT`` constants of ``config.py``, ``ocs.py``, ``deps.py`` and
``ids.py`` already follow for the sentences a model reads.

v1 ships English only, consistent with ``docs/client-setup.md``. The German reference
wording lives in the table "German reference wording" of ``03-UI-SPEC.md`` and is
deliberately not mirrored here as a dictionary: an unused mapping would be dead code, the
dead code gate would report it, and a whitelist entry for a translation nobody serves yet
is worse than a table in the document that owns the copy anyway.

The placeholders are ``str.format`` names, and there are exactly six of them across the
whole surface: ``client``, ``host``, ``user``, ``redirect_uri``, ``seconds`` and ``ref``.
Every one of them is filled at render time and escaped by ``layout``, at the single point
where the template writes it.

Copy rules the wording below follows, from the same document: every error names what
happened and what to do next, no OAuth error code, no parameter name, no internal host, no
code or token fragment, no blame, no exclamation mark, no emoji, never "click here".

All names are listed in ``__all__``. That is what a text catalogue is, and it is also what
tells the dead code gate that a sentence which no page uses yet is published on purpose:
the screens that consume the consent and result copy are built in 03-04 to 03-06 against
exactly these names.
"""

__all__ = [
    "ACTION_CANCEL_CONNECTION",
    "ACTION_CANCEL_SIGN_IN",
    "ACTION_CHECK_NOW",
    "ACTION_START_OVER",
    "CLIENT_NAME_FALLBACK",
    "CONNECT_BODY",
    "CONNECT_DETAIL_CREDENTIAL",
    "CONNECT_DETAIL_USER",
    "CONNECT_HANDOFF_BODY",
    "CONNECT_HANDOFF_TITLE",
    "CONNECT_RESULT_BODY",
    "CONNECT_RESULT_HOWTO",
    "CONNECT_RESULT_ONCE",
    "CONNECT_RESULT_ONCE_TITLE",
    "CONNECT_RESULT_REVOKE",
    "CONNECT_TITLE",
    "CONNECT_WAIT_BODY",
    "CONNECT_WAIT_TITLE",
    "CONSENT_APPROVE",
    "CONSENT_DENY",
    "CONSENT_DETAIL_APP_NAME",
    "CONSENT_DETAIL_CLIENT_ID",
    "CONSENT_DETAIL_REDIRECT",
    "CONSENT_FOOTER",
    "CONSENT_GRANT_NO_REMOVAL",
    "CONSENT_GRANT_READ",
    "CONSENT_GRANT_REVOKE",
    "CONSENT_GRANT_TITLE",
    "CONSENT_GRANT_WRITE",
    "CONSENT_IDENTITY",
    "CONSENT_TITLE",
    "CONSENT_WARNING_BODY",
    "CONSENT_WARNING_TITLE",
    "EMPTY_BODY",
    "EMPTY_TITLE",
    "ERROR_ALLOWLIST_BODY",
    "ERROR_ALLOWLIST_TITLE",
    "ERROR_EXPIRED_BODY",
    "ERROR_EXPIRED_TITLE",
    "ERROR_GENERIC_BODY",
    "ERROR_GENERIC_TITLE",
    "ERROR_REDIRECT_BODY",
    "ERROR_REDIRECT_TITLE",
    "ERROR_REGISTRATION_OFF_BODY",
    "ERROR_REGISTRATION_OFF_TITLE",
    "ERROR_THROTTLED_BODY",
    "ERROR_THROTTLED_TITLE",
    "ERROR_TIMEOUT_BODY",
    "ERROR_TIMEOUT_TITLE",
    "FOOTER_PASSWORD_PROMPT",
    "RESULT_CONNECTED_BODY",
    "RESULT_CONNECTED_TITLE",
    "RESULT_DENIED_BODY",
    "RESULT_DENIED_TITLE",
    "RESULT_RETURN_ACTION",
    "RESULT_RETURN_BODY",
    "SIGNIN_BODY",
    "SIGNIN_CTA",
    "SIGNIN_TITLE",
    "WAIT_BODY",
    "WAIT_STATUS",
    "WAIT_TITLE",
    "WORDMARK",
]

# --- Sender identity, on every page ------------------------------------------------------

#: The wordmark of the bar above the card, next to the configured host. Together they are
#: the answer to "who is asking", which the user must be able to read on every screen.
WORDMARK = "MCP Connector for Nextcloud"

#: Default footer. The one sentence that makes a phishing copy of this page useless.
FOOTER_PASSWORD_PROMPT = (
    "The password prompt is always Nextcloud itself. If any other page asks you for your "  # noqa: S105 - a sentence about passwords, not a password
    "Nextcloud password, close it."
)

#: What a client is called when its registration carries no usable name at all.
CLIENT_NAME_FALLBACK = "An unnamed app"

# --- S1, sign in handoff -----------------------------------------------------------------

SIGNIN_TITLE = "Sign in to continue"

SIGNIN_BODY = (
    "{client} wants to connect to your Nextcloud. Sign in at {host} first. This page never "
    "asks for your password."
)

SIGNIN_CTA = "Continue to Nextcloud sign in"

# --- S2, waiting for the sign in ---------------------------------------------------------

WAIT_TITLE = "Waiting for your sign in"

WAIT_STATUS = "Waiting for your sign in at {host}."

WAIT_BODY = (
    "Finish the sign in in the other window. This page checks every few seconds and "
    "continues on its own as soon as you are signed in."
)

# --- Secondary actions, shared across the screens ----------------------------------------

ACTION_CANCEL_CONNECTION = "Cancel connection"

ACTION_CANCEL_SIGN_IN = "Cancel sign in"

ACTION_CHECK_NOW = "Check now"

ACTION_START_OVER = "Start over"

# --- The browser onboarding of AUTH-02 (plan 03-04) ---------------------------------------
#
# The same three screens as S1, S2 and the out of band variant of S4, for the user who has no
# OAuth capable client: an invitation, then the handoff with the Nextcloud link, then the
# waiting state, then the one time result. The wording never calls the credential a password
# of the user, because it is not one: it is an app password this connection owns, and the
# user can end it on its own in Nextcloud.

CONNECT_TITLE = "Connect an assistant app"

CONNECT_BODY = (
    "This creates a credential for an assistant app that cannot sign in at {host} by itself. "
    "The sign in happens at {host}, on its own pages, including your second factor. This page "
    "never asks for your password."
)

CONNECT_HANDOFF_TITLE = "Sign in at {host}"

CONNECT_HANDOFF_BODY = (
    "The sign in opens in a new window. Approve the connection there, then come back to this "
    "page. It is waiting for the result and needs nothing else from you."
)

CONNECT_WAIT_TITLE = "Waiting for your sign in"

CONNECT_WAIT_BODY = (
    "Finish the sign in in the other window. This page checks every few seconds and shows the "
    "result as soon as it arrives. If the other window is gone, start over."
)

CONNECT_DETAIL_USER = "Signed in as"

CONNECT_DETAIL_CREDENTIAL = "Credential for your assistant app"

CONNECT_RESULT_BODY = (
    "The connection is ready. Copy the credential below into your assistant app, together with "
    "the user name above."
)

CONNECT_RESULT_ONCE_TITLE = "Shown once"

CONNECT_RESULT_ONCE = (
    "This is the only time the credential is shown. Nothing of it is stored on this server. If "
    "you lose it, start over and create a new one."
)

CONNECT_RESULT_HOWTO = (
    "In your assistant app, use the user name and the credential as Basic credentials for the "
    "connector endpoint, exactly as described in the client setup guide."
)

CONNECT_RESULT_REVOKE = (
    "You can end this connection at any time in Nextcloud under Settings, Security, Devices and "
    "sessions. It is listed there under the name of this connector."
)

# --- S3, consent -------------------------------------------------------------------------

CONSENT_TITLE = "Allow {client} to use your Nextcloud?"

CONSENT_IDENTITY = "You are signed in as {user} at {host}."

CONSENT_WARNING_TITLE = "Unverified client"

CONSENT_WARNING_BODY = (
    "This app registered itself automatically. Nextcloud has not verified it. Only approve "
    "it if you started this connection yourself."
)

CONSENT_DETAIL_APP_NAME = "App name"

CONSENT_DETAIL_REDIRECT = "Sends you back to"

CONSENT_DETAIL_CLIENT_ID = "Client ID"

CONSENT_GRANT_TITLE = "What this allows"

CONSENT_GRANT_READ = (
    "Read your files, calendar, notes, contacts and Deck cards, exactly as far as your own "
    "account reaches"
)

CONSENT_GRANT_WRITE = (
    "Create and change notes, calendar entries, Deck cards and files that do not exist yet"
)

# The constant is named after the promise and not after the HTTP verb: the contract gate in
# tests/contract/test_no_destructive_calls.py rejects that verb in upper case anywhere in
# production code, and it guards exactly the promise this sentence makes to the user.
CONSENT_GRANT_NO_REMOVAL = "Nothing is deleted. The connector has no delete tools."

CONSENT_GRANT_REVOKE = "Access ends when you revoke it in Nextcloud settings."

CONSENT_APPROVE = "Approve access"

CONSENT_DENY = "Deny access"

CONSENT_FOOTER = (
    "Approving does not share your password. The connector receives its own credential and "
    "never sees the password you typed at {host}."
)

# --- S4, result pages --------------------------------------------------------------------

RESULT_CONNECTED_TITLE = "Connected"

RESULT_CONNECTED_BODY = "{client} may now use your Nextcloud as {user}. You can close this window."

RESULT_DENIED_TITLE = "Access denied"

RESULT_DENIED_BODY = "{client} did not get access. Nothing was shared. You can close this window."

#: The return page of a decision that has somewhere to go back to (CR-03). The decision is
#: a form submission, and Chromium and WebKit check ``form-action`` against the target of a
#: redirect that follows one, so an answer of "302 to the client" is refused by the browser
#: under the policy of this phase. The answer is this page instead: it continues on its own
#: and names the button that does the same thing, so the return never depends on a redirect
#: the browser may refuse or on a policy that names a foreign origin.
RESULT_RETURN_BODY = "Taking you back to {client}. If nothing happens, use the button below."

RESULT_RETURN_ACTION = "Continue to {client}"

# --- Empty state -------------------------------------------------------------------------

EMPTY_TITLE = "Nothing to approve"

EMPTY_BODY = (
    "This page only appears while an app is asking for access. Start the connection again "
    "in your assistant app."
)

# --- E1 to E7, the seven error pages -----------------------------------------------------
#
# The trigger of each page and its status code live in ``errors.py``. Here is only the copy,
# so that a wording fix never touches a status code and a status code fix never touches the
# wording. Every body ends with the next step, because a user who reads only the last
# sentence of an error page still has to know what to do.

ERROR_ALLOWLIST_TITLE = "This app is not allowed"

ERROR_ALLOWLIST_BODY = (
    "An administrator has not allowed {client} to connect to this Nextcloud. Ask your "
    "administrator to add it, then try again."
)

ERROR_REGISTRATION_OFF_TITLE = "Automatic registration is off"

ERROR_REGISTRATION_OFF_BODY = (
    "An administrator switched off automatic app registration on this Nextcloud. Ask your "
    "administrator to register {client} manually, then try again."
)

ERROR_EXPIRED_TITLE = "This link has expired"

ERROR_EXPIRED_BODY = (
    "Authorization links are valid for a few minutes and can be used once. Start the "
    "connection again in your assistant app."
)

ERROR_TIMEOUT_TITLE = "Sign in timed out"

ERROR_TIMEOUT_BODY = (
    "The sign in was not completed in time. Start the connection again in your assistant app."
)

ERROR_REDIRECT_TITLE = "This app cannot be sent back safely"

ERROR_REDIRECT_BODY = (
    "The address {client} asked us to return to does not match its registration. For your "
    "safety nothing was shared. Start the connection again in your assistant app, and tell "
    "your administrator if it keeps happening."
)

ERROR_THROTTLED_TITLE = "Too many attempts"

ERROR_THROTTLED_BODY = "Wait {seconds} seconds and try again."

ERROR_GENERIC_TITLE = "Something went wrong"

ERROR_GENERIC_BODY = (
    "The connection could not be completed. Try again. If it keeps failing, an administrator "
    "can find the details in the app log under reference {ref}."
)
