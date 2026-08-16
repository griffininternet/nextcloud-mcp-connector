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
# oauth/store.py is the persistence layer of the OAuth phase and is built in one piece, in
# plan 03-02, because its schema and its transactions only make sense together. Its callers
# arrive in the plans that follow: the consent bridge (03-04) writes flows and
# authorizations, the authorize and token endpoints (03-05, 03-06) write and redeem codes
# and tokens, the verifier (03-06) reads access tokens, and the rotation with reuse
# detection (03-07) is the whole reason redeem_refresh_token and revoke_family exist.
# Every name below is exercised by tests/unit/test_oauth_store.py, which fails if one of
# them stops behaving; none of them is reachable from the production call graph yet. The six
# names the browser onboarding of plan 03-04 calls for real (save_client, touch_client,
# create_flow, load_flow, delete_flow and purge_expired) left this list with that plan.
_.load_client
_.delete_client
_.create_authorization
_.load_authorization
_.revoke_authorization
_.create_auth_code
_.redeem_auth_code
_.create_access_token
_.load_access_token
_.create_refresh_token
_.load_refresh_token
_.redeem_refresh_token
_.revoke_family

# Fields of the row objects above that this phase writes and a later plan reads:
# client_secret_hash (03-06 authenticates a confidential client with it), created_at and
# revoked_at (03-07 and the admin view of phase 4), issued_at and used_at (the grace window
# of D-41 is decided on used_at, and the auth code row keeps its own used_at as the record
# that it was consumed).
_.client_secret_hash
_.created_at
_.revoked_at
_.issued_at
_.used_at

# --- The eleven methods of the SDK provider protocol -----------------------------------
# oauth/provider.py implements OAuthAuthorizationServerProvider. Every method below is
# called by the SDK handlers of /authorize, /token, /register and /revoke, and by nothing
# in this repository: create_auth_routes takes the object and wires the calls itself, the
# same shape as verify_token above. All of them are driven directly by
# tests/unit/test_oauth_provider.py, which is what keeps them honest. load_access_token is
# absent from this list because it already stands in the store block above.
_.get_client
_.register_client
_.authorize
_.load_authorization_code
_.exchange_authorization_code
_.load_refresh_token
_.exchange_refresh_token
_.revoke_token
_.exchange_identity_assertion

# --- Two more names the SDK and the next plan call -------------------------------------
# authenticate_request: the one method of the SDK ClientAuthenticator. The TokenHandler and
#   the RevocationHandler call it on every request to /token and /revoke; nothing in this
#   repository does. tests/unit/test_oauth_provider.py drives it through both endpoints.
# invalidate: empties the process cache of the token verifier. Plan 03-07 calls it from the
#   revocation path, where a cached answer of up to five seconds would keep a connection
#   alive that the user just ended (D-34). tests/unit/test_oauth_verifier.py proves it.
_.authenticate_request
_.invalidate
