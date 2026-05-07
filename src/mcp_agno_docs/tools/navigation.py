"""Navigation tool logic.

Provides the ``get_navigation`` MCP tool decorated with ``@mcp.tool()``,
plus the internal function for returning the pre-loaded navigation tree.
"""

from __future__ import annotations

from typing import Any

from mcp_agno_docs.models import NavTree

from . import mcp


# ---- Internal (testable) function ----

def _get_navigation(nav: NavTree) -> NavTree:
    """Return the pre-loaded navigation tree.

    The navigation tree is parsed from ``docs.json`` once during server
    startup (lifespan) and cached. This function returns the cached copy.

    Args:
        nav: The :class:`NavTree` instance cached in the application context.

    Returns:
        The same :class:`NavTree` instance (no copy — read-only access).
    """
    return nav


# ---- FastMCP tool wrapper ----

@mcp.tool()
def get_navigation() -> dict[str, Any]:
    """Return the Agno documentation navigation tree.

    Returns a hierarchical tree structure with tabs, groups, and pages
    as parsed from the ``docs.json`` navigation file. Folder nodes have
    ``path: null``; leaf nodes have a ``.mdx`` path.
    """
    ctx = mcp.get_context()
    app_ctx = ctx.request_context.lifespan_context
    nav: NavTree = app_ctx.nav
    tree = _get_navigation(nav)
    return tree.model_dump()
