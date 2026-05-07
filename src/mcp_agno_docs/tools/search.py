"""Search tool logic — full-text search and examples-scoped search.

Provides ``search_docs`` and ``search_examples`` MCP tools decorated with
``@mcp.tool()``, plus internal async functions (prefixed ``_``) that
contain the business logic and accept explicit engine dependencies.
"""

from __future__ import annotations

from typing import Any

import pydantic as _pydantic

from mcp_agno_docs import errors as domain_err
from mcp_agno_docs.models import DocHit, SearchDocsInput, SearchExamplesInput, SearchHit
from mcp_agno_docs.search.base import SearchEngine
from mcp_agno_docs.utils import _tool_error

from . import mcp


# ---- Internal (testable) functions ----

async def _search_docs(
    engine: SearchEngine,
    query: str,
    topic: str | None = None,
    limit: int = 10,
) -> list[DocHit]:
    """Execute a full-text search across all indexed documentation.

    Args:
        engine: The search engine adapter to query.
        query: Free-text search query (minimum 2 characters).
        topic: Optional keyword filter matched against the ``keywords`` column.
        limit: Maximum number of hits to return (1–50).

    Returns:
        Ranked list of :class:`DocHit` ordered by ascending BM25 score
        (lower = more relevant).

    Raises:
        ValidationError: If *query* is shorter than 2 characters or *limit*
            is out of range.
    """
    try:
        SearchDocsInput(query=query, topic=topic, limit=limit)
    except _pydantic.ValidationError as exc:
        raise domain_err.ValidationError(str(exc)) from exc

    hits: list[SearchHit] = await engine.search(query, topic=topic, limit=limit)
    return [DocHit(**h.model_dump()) for h in hits]


async def _search_examples(
    engine: SearchEngine,
    query: str,
    limit: int = 10,
) -> list[DocHit]:
    """Search only pages whose path starts with ``examples/``.

    Starts with a 4× overfetch, then retries with an 8× overfetch
    (max multiplier = 8) if fewer than *limit* example hits are found
    after client-side filtering.

    Args:
        engine: The search engine adapter to query.
        query: Free-text search query (minimum 2 characters).
        limit: Maximum number of hits to return (1–50).

    Returns:
        Filtered list of :class:`DocHit` for examples-only pages.

    Raises:
        ValidationError: If *query* is shorter than 2 characters or *limit*
            is out of range.
    """
    try:
        SearchExamplesInput(query=query, limit=limit)
    except _pydantic.ValidationError as exc:
        raise domain_err.ValidationError(str(exc)) from exc

    multiplier = 4
    filtered: list[SearchHit] = []
    while True:
        overfetch = limit * multiplier
        hits: list[SearchHit] = await engine.search(query, topic=None, limit=overfetch)
        filtered = [h for h in hits if h.path.startswith("examples/")]
        if len(filtered) >= limit or multiplier >= 8:
            break
        multiplier *= 2

    return [DocHit(**h.model_dump()) for h in filtered[:limit]]


# ---- FastMCP tool wrappers ----

@mcp.tool()
async def search_docs(
    query: str,
    topic: str | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Full-text search across Agno documentation with optional topic filter.

    Searches the entire Agno docs corpus using BM25 relevance ranking.
    Results include the document path, title, a snippet with ``<b>``
    highlighted matches, and a relevance score (lower = more relevant).

    Args:
        query: Search query (minimum 2 characters).
        topic: Optional keyword topic to narrow results.
        limit: Maximum results to return (1–50, default 10).
    """
    ctx = mcp.get_context()
    app_ctx = ctx.request_context.lifespan_context
    engine: SearchEngine = app_ctx.engine
    try:
        hits = await _search_docs(engine, query=query, topic=topic, limit=limit)
    except domain_err.ValidationError as exc:
        raise _tool_error(str(exc)) from exc
    return [h.model_dump() for h in hits]


@mcp.tool()
async def search_examples(
    query: str,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Search only the examples/ section of Agno documentation.

    Like ``search_docs`` but scoped to pages whose path starts with
    ``examples/``. Useful for finding code snippets and usage samples.

    Args:
        query: Search query (minimum 2 characters).
        limit: Maximum results to return (1–50, default 10).
    """
    ctx = mcp.get_context()
    app_ctx = ctx.request_context.lifespan_context
    engine: SearchEngine = app_ctx.engine
    try:
        hits = await _search_examples(engine, query=query, limit=limit)
    except domain_err.ValidationError as exc:
        raise _tool_error(str(exc)) from exc
    return [h.model_dump() for h in hits]
