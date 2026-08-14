"""Tool logic as freestanding async functions.

Nothing in this package imports ``mcp``: every function takes one parameter object
(:class:`mcp_connector.nextcloud.NcClients`) and returns a plain dict. That is what makes
the tools unit testable with respx and what lets the same code run under stdio, Streamable
HTTP and, from phase 2 on, AppAPI impersonation without a change.
"""
