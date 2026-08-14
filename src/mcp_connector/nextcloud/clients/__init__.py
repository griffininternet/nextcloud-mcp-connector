"""One module per Nextcloud API family: WebDAV, CalDAV, CardDAV, Notes, Deck, OCS.

XML building and parsing live here, never in tool code. Shared namespace constants and
the hardened parser are in :mod:`mcp_connector.nextcloud.clients.xml`.
"""
