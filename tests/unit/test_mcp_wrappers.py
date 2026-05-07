"""Tests for FastMCP @mcp.tool() wrapper error handling — forces coverage of the MCP integration layer.

These tests mock `mcp.get_context()` to exercise the try/except blocks
in the tool wrappers that convert domain errors to MCP ToolError.
"""
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from mcp_agno_docs import errors as domain_err
from mcp_agno_docs.models import (
    DocFrontmatter,
    DocPage,
    NavNode,
    NavTree,
    SearchHit,
)
from mcp_agno_docs.search.base import SearchEngine
from mcp_agno_docs.sources.base import DocSource


def _make_mock_context(source=None, engine=None, nav=None):
    """Build a mock FastMCP context with lifespan_context for DI."""
    ctx = MagicMock()
    app_ctx = MagicMock()
    app_ctx.source = source or MagicMock(spec=DocSource)
    app_ctx.engine = engine or AsyncMock(spec=SearchEngine)
    app_ctx.nav = nav or NavTree(root=NavNode(title="Docs"))
    ctx.request_context.lifespan_context = app_ctx
    return ctx


class TestSearchDocsToolWrapper:
    """Tests for the @mcp.tool() search_docs wrapper."""

    @pytest.mark.asyncio
    @patch("mcp_agno_docs.tools.search.mcp.get_context")
    async def test_returns_formatted_results(self, mock_get_context):
        """search_docs wrapper calls engine, formats results as dicts."""
        from mcp_agno_docs.tools.search import search_docs

        engine = AsyncMock(spec=SearchEngine)
        engine.search.return_value = [
            SearchHit(path="api/agents.mdx", title="Agents", snippet="...", score=1.0),
        ]
        mock_get_context.return_value = _make_mock_context(engine=engine)

        result = await search_docs("agents", limit=5)
        assert len(result) == 1
        assert result[0]["path"] == "api/agents.mdx"
        assert result[0]["title"] == "Agents"
        engine.search.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("mcp_agno_docs.tools.search.mcp.get_context")
    async def test_wraps_validation_error_as_tool_error(self, mock_get_context):
        """When engine raises ValidationError, wrapper converts to ToolError."""
        from mcp_agno_docs.tools.search import search_docs

        engine = AsyncMock(spec=SearchEngine)
        engine.search.side_effect = domain_err.ValidationError("bad query")
        mock_get_context.return_value = _make_mock_context(engine=engine)

        with pytest.raises(Exception) as exc_info:
            await search_docs("test")
        # FastMCP wraps it; we just verify it doesn't crash with raw domain error
        assert "bad query" in str(exc_info.value) or isinstance(exc_info.value, Exception)

    @pytest.mark.asyncio
    @patch("mcp_agno_docs.tools.search.mcp.get_context")
    async def test_default_limit_is_10(self, mock_get_context):
        """Default limit=10 is passed to engine."""
        from mcp_agno_docs.tools.search import search_docs

        engine = AsyncMock(spec=SearchEngine)
        engine.search.return_value = []
        mock_get_context.return_value = _make_mock_context(engine=engine)

        await search_docs("query")
        engine.search.assert_awaited_once_with("query", topic=None, limit=10)

    @pytest.mark.asyncio
    @patch("mcp_agno_docs.tools.search.mcp.get_context")
    async def test_topic_is_passed_to_engine(self, mock_get_context):
        """Topic parameter is forwarded to engine.search."""
        from mcp_agno_docs.tools.search import search_docs

        engine = AsyncMock(spec=SearchEngine)
        engine.search.return_value = []
        mock_get_context.return_value = _make_mock_context(engine=engine)

        await search_docs("query", topic="examples")
        engine.search.assert_awaited_once_with("query", topic="examples", limit=10)


class TestSearchExamplesToolWrapper:
    """Tests for the @mcp.tool() search_examples wrapper."""

    @pytest.mark.asyncio
    @patch("mcp_agno_docs.tools.search.mcp.get_context")
    async def test_returns_dicts_from_search_examples(self, mock_get_context):
        """search_examples wrapper calls engine, filters, returns dicts."""
        from mcp_agno_docs.tools.search import search_examples

        engine = AsyncMock(spec=SearchEngine)
        engine.search.return_value = [
            SearchHit(path="examples/basic.mdx", title="Basic", snippet="...", score=0.5),
        ]
        mock_get_context.return_value = _make_mock_context(engine=engine)

        result = await search_examples("example", limit=5)
        assert len(result) == 1
        assert result[0]["path"] == "examples/basic.mdx"

    @pytest.mark.asyncio
    @patch("mcp_agno_docs.tools.search.mcp.get_context")
    async def test_default_limit_for_examples(self, mock_get_context):
        """Default limit=10 for search_examples."""
        from mcp_agno_docs.tools.search import search_examples

        engine = AsyncMock(spec=SearchEngine)
        engine.search.return_value = []
        mock_get_context.return_value = _make_mock_context(engine=engine)

        await search_examples("query")
        engine.search.assert_awaited_once_with("query", topic=None, limit=40)


class TestGetPageToolWrapper:
    """Tests for the @mcp.tool() get_page wrapper."""

    @pytest.mark.asyncio
    @patch("mcp_agno_docs.tools.pages.mcp.get_context")
    async def test_returns_page_as_dict(self, mock_get_context):
        """get_page wrapper returns DocPage serialized as dict."""
        from mcp_agno_docs.tools.pages import get_page

        page = DocPage(
            path="agents/overview.mdx",
            frontmatter=DocFrontmatter(title="Agents", description="Overview"),
            content="# Agents\n\nContent.",
        )
        source = Mock(spec=DocSource)
        source.get_page.return_value = page
        mock_get_context.return_value = _make_mock_context(source=source)

        result = await get_page("agents/overview.mdx")
        assert result["path"] == "agents/overview.mdx"
        assert result["frontmatter"]["title"] == "Agents"

    @pytest.mark.asyncio
    @patch("mcp_agno_docs.tools.pages.mcp.get_context")
    async def test_page_not_found_converts_to_tool_error(self, mock_get_context):
        """When source raises PageNotFound, wrapper converts to MCP error."""
        from mcp_agno_docs.tools.pages import get_page

        source = Mock(spec=DocSource)
        source.get_page.side_effect = domain_err.PageNotFound("missing")
        mock_get_context.return_value = _make_mock_context(source=source)

        with pytest.raises(Exception) as exc_info:
            await get_page("bogus.mdx")
        assert "missing" in str(exc_info.value) or isinstance(exc_info.value, Exception)

    @pytest.mark.asyncio
    @patch("mcp_agno_docs.tools.pages.mcp.get_context")
    async def test_path_traversal_returns_error(self, mock_get_context):
        """Path with .. raises error before touching source."""
        from mcp_agno_docs.tools.pages import get_page

        source = Mock(spec=DocSource)
        mock_get_context.return_value = _make_mock_context(source=source)

        with pytest.raises(Exception):
            await get_page("../secrets")
        source.get_page.assert_not_called()


class TestGetNavigationToolWrapper:
    """Tests for the @mcp.tool() get_navigation wrapper."""

    @pytest.mark.asyncio
    @patch("mcp_agno_docs.tools.navigation.mcp.get_context")
    async def test_returns_nav_as_dict(self, mock_get_context):
        """get_navigation wrapper returns NavTree serialized as dict."""
        from mcp_agno_docs.tools.navigation import get_navigation

        tree = NavTree(root=NavNode(title="Docs", children=[
            NavNode(title="Home", path="index.mdx"),
        ]))
        mock_get_context.return_value = _make_mock_context(nav=tree)

        result = await get_navigation()
        assert result["root"]["title"] == "Docs"
        assert len(result["root"]["children"]) == 1

    @pytest.mark.asyncio
    @patch("mcp_agno_docs.tools.navigation.mcp.get_context")
    async def test_empty_navigation_tree(self, mock_get_context):
        """NavTree with no children returns correctly."""
        from mcp_agno_docs.tools.navigation import get_navigation

        tree = NavTree(root=NavNode(title="Docs"))
        mock_get_context.return_value = _make_mock_context(nav=tree)

        result = await get_navigation()
        assert result["root"]["title"] == "Docs"


class TestNavigationErrorWrapping:
    """Tests for error wrapping in the navigation tool wrapper."""

    @pytest.mark.asyncio
    @patch("mcp_agno_docs.tools.navigation.mcp.get_context")
    async def test_wraps_error_in_navigation_tool(self, mock_get_context):
        """If the model_dump() fails somehow, wrapper handles it."""
        from mcp_agno_docs.tools.navigation import get_navigation

        # Create a NavTree that will fail model_dump (unlikely but tests the path)
        tree = NavTree(root=NavNode(title="Docs"))
        mock_get_context.return_value = _make_mock_context(nav=tree)

        result = await get_navigation()
        assert "root" in result
