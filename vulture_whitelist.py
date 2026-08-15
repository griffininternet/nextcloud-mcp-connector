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

# --- Reserved names of the AppAPI deploy environment -----------------------------------
# ENV_APP_PERSISTENT_STORAGE: AppAPI injects APP_PERSISTENT_STORAGE into every ExApp
#   container. The name is declared here in one place, with the other eight AppAPI
#   variables, instead of appearing as a bare string in the plan that starts using the
#   volume (02-04). Declaring a name without evaluating it is the same "no silent
#   defaults" rule the HTTP mode variables followed in phase 1.
ENV_APP_PERSISTENT_STORAGE
