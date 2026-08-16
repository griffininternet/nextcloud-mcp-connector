# Vulture whitelist: names that are reachable, but not through a call vulture can see.
#
# Passing this file to vulture is what lets the dead code gate run at full confidence
# instead of at --min-confidence 80. At 80 the tool reports nothing at all here, which
# makes the CI step decorative in exactly the way the token budget gate used to be.
#
# Every entry below needs a reason. "vulture complained" is not one. A name that cannot be
# justified in one line is dead code and belongs in a delete commit, not in this file.
#
# The bare names are the documented vulture whitelist format: the file is parsed, never
# imported, so undefined names are intentional (ruff and pyright are configured to skip it
# in pyproject.toml).

# --- The fifteen tool functions -------------------------------------------------------
# Registered by the @mcp.tool decorator at import time and called by the MCP runtime, never
# from our own code. Every one of them is covered by tests/contract/test_tool_surface.py,
# which fails if any of them stops being listed.
files_search
files_list
files_read
files_upload
calendar_list_events
calendar_create_event
notes_search
notes_read
notes_create
deck_browse
deck_create_card
contacts_search

# --- Framework entry points -----------------------------------------------------------
# health: registered with @mcp.custom_route and checked by tests/unit/test_transport_
#   security.py and the client matrix, which waits for it before every run.
# verify_token: the one method of the SDK TokenVerifier protocol; the SDK calls it on every
#   authenticated request, tests/unit/test_http_modes.py calls it directly.
# auth_flow: the one method of the httpx.Auth interface; httpx calls it for every request
#   that was given auth=creds.auth(), and tests/unit/test_appapi_credentials.py drives it
#   directly to read the four AppAPI headers off the signed request.
health
_.verify_token
_.auth_flow

# --- Fields of an SDK model that only the serialised document reads --------------------
# scopes_supported, authorization_response_iss_parameter_supported: two of the three fields
#   oauth/metadata.py sets on the OAuthMetadata model of the SDK after build_metadata built
#   it. Nothing in this repository reads them back; they are written, dumped to JSON and
#   answered to the client, which is exactly what tests/unit/test_oauth_metadata.py asserts
#   on. Assigning them on the model instead of on the dumped dict keeps the field names
#   checked by pydantic and pyright, which is why the write looks unused to vulture.
_.scopes_supported
_.authorization_response_iss_parameter_supported

# --- Read from outside the production call graph --------------------------------------
# deck_api_versions: a capabilities field the Deck integration test asserts on; it exists so
#   an instance that only offers API 1.1 is a named finding instead of a mystery 404.
# NSMAP: the complete DAV namespace map, used by tests/unit/test_xml.py and by every future
#   XML body; splitting it up per call site would invite a typo in a namespace URI.
# get_board: the single board read of the Deck client, covered by tests/unit/test_deck_
#   client.py. deck_browse reaches boards through get_boards, so the singular form currently
#   has no production caller. It stays because it is the only place that knows the shape of
#   the single board route, and it costs eight lines.
deck_api_versions
NSMAP
get_board

# --- The store API of phase 3 ----------------------------------------------------------
# oauth/store.py was built in one piece in plan 03-02, because its schema and its
# transactions only make sense together, and its callers arrived plan by plan afterwards.
# Plan 03-07 was the last of them: the rotation calls redeem_refresh_token, load_refresh_
# token and revoke_family, and the revocation calls revoke_authorization, note_cleanup and
# clear_cleanup. What is left below is the one name that is still reachable through the
# store alone. Every entry that gained a production caller left this list with the plan
# that called it.
#
# load_access_token: the store method is called by the verifier on every request, but the
#   name also belongs to the provider method of the same name, which refuses on purpose and
#   therefore has no caller (see the module docstring of oauth/provider.py). One whitelist
#   entry covers both, and dropping it would flag the deliberate refusal as dead code.
_.load_access_token

# Fields of the row objects that this phase writes and a later plan reads:
# created_at and issued_at (the admin view of phase 4 shows when a connection was made),
# cleanup_at (03-07 writes it when a Nextcloud app password could not be handed back; the
# sweep selects on the column in SQL, and the field itself is for the same admin view).
_.created_at
_.issued_at
_.cleanup_at

# --- The methods of the SDK provider protocol ------------------------------------------
# oauth/provider.py implements OAuthAuthorizationServerProvider. Every method below is
# called by the SDK handlers of /authorize, /token and /register, and by nothing in this
# repository: create_auth_routes takes the object and wires the calls itself, the same
# shape as verify_token above. All of them are driven directly by
# tests/unit/test_oauth_provider.py, which is what keeps them honest. load_access_token is
# absent from this list because it already stands in the store block above.
#
# revoke_token stays here although /revoke is served by our own FamilyRevocation now: the
# handler calls revoke_presented_token, which adds the ownership check, and revoke_token is
# the protocol method that any other SDK path would use. Both end in the same revocation.
_.get_client
_.register_client
_.authorize
_.load_authorization_code
_.exchange_authorization_code
_.load_refresh_token
_.exchange_refresh_token
_.revoke_token
_.exchange_identity_assertion

# --- The two methods of the cookie jar that refuses to be one ---------------------------
# nextcloud/http.NoCookieJar overrides both halves of http.cookiejar.CookieJar. They are
# called by urllib through httpx and by nothing in this repository, and their whole job is
# to do nothing: a shared client must not keep or send a Nextcloud session cookie, which is
# the identity mix up plan 03-08 measured. tests/unit/test_credentials_http.py drives both.
_.set_cookie
_.add_cookie_header
_.cookie
