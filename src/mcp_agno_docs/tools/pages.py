"""Page retrieval tool logic.

Provides the ``get_page`` MCP tool decorated with ``@mcp.tool()``, plus
internal functions for path normalisation and page lookup.
"""

from __future__ import annotations

from typing import Any

import pydantic as _pydantic

from mcp_agno_docs import errors as domain_err
from mcp_agno_docs.models import DocPage, GetPageInput
from mcp_agno_docs.sources.base import DocSource
from mcp_agno_docs.utils import normalise_path

from . import mcp


# ---- Internal (testable) functions ----


def _get_page(source: DocSource, path: str) -> DocPage:
    """Retrieve a documentation page by its relative path.

    Args:
        source: The doc source adapter to query.
        path: Raw page path (e.g. ``"api/agents.mdx"`` or
            ``"/api/agents.mdx"``).

    Returns:
        The matching :class:`DocPage` with frontmatter and content.

    Raises:
        ValidationError: If *path* contains ``..`` (traversal attempt) or
            fails Pydantic validation.
        PageNotFound: If the page does not exist in the source.
        PageInvalid: If the page exists but failed frontmatter validation.
    """
    try:
        GetPageInput(path=path)
    except _pydantic.ValidationError as exc:
        raise domain_err.ValidationError(str(exc)) from exc

    normalised = normalise_path(path)
    try:
        return source.get_page(normalised)
    except domain_err.PageNotFound:
        raise
    except domain_err.PageInvalid:
        raise


# ---- FastMCP tool wrapper ----

@mcp.tool()
async def get_page(path: str) -> dict[str, Any]:
    """Retrieve a documentation page by its relative path.

    Returns the full page content including parsed YAML frontmatter
    (title, description, keywords) and raw Markdown/MDX body.

    Args:
        path: Relative page path, e.g. ``"api/agents.mdx"``.
            Accepts leading slashes and backslashes.
    """
    ctx = mcp.get_context()
    app_ctx = ctx.request_context.lifespan_context
    source: DocSource = app_ctx.source
    try:
        page = _get_page(source, path)
    except domain_err.ValidationError as exc:
        raise _tool_error(str(exc)) from exc
    except domain_err.PageNotFound as exc:
        raise _not_found(str(exc)) from exc
    except domain_err.PageInvalid as exc:
        raise _tool_error(str(exc)) from exc
    return page.model_dump()


# ---- Error mapping helpers ----

def _tool_error(message: str) -> Exception:
    """Convert a domain error message into an MCP-level ToolError."""
    from mcp.server.fastmcp.exceptions import ToolError

    return ToolError(message)


def _not_found(message: str) -> Exception:
    """Raise a structured not-found error for missing pages."""
    from mcp.server.fastmcp.exceptions import ResourceError

    return ResourceError(message)
