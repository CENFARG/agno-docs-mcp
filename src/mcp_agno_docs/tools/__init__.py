"""MCP tool implementations for agno-docs-mcp.

Each sub-module exposes internal functions (prefixed ``_``) that contain
the pure business logic and accept explicit dependencies
(:class:`~mcp_agno_docs.search.base.SearchEngine`,
:class:`~mcp_agno_docs.sources.base.DocSource`, etc.).

FastMCP-annotated wrappers in the same sub-modules call these internals
after extracting deps from the lifespan context via
:func:`mcp.server.fastmcp.FastMCP.get_context`.

The ``mcp`` instance defined here is the single FastMCP application that
all tool modules decorate with ``@mcp.tool()`` and that
:mod:`mcp_agno_docs.server` configures and runs.
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("agno-docs")
