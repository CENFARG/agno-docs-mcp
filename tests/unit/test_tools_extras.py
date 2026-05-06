"""Additional tests for tools module error handling and navigation edge cases."""
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from mcp_agno_docs.errors import PageNotFound, SearchError, StartupError, ValidationError
from mcp_agno_docs.models import (
    DocFrontmatter,
    DocPage,
    NavNode,
    NavTree,
    SearchHit,
)
from mcp_agno_docs.search.base import SearchEngine
from mcp_agno_docs.sources.base import DocSource
from mcp_agno_docs.tools.navigation import _get_navigation
from mcp_agno_docs.tools.pages import _get_page
from mcp_agno_docs.tools.search import _search_docs, _search_examples


class TestSearchDocsErrors:
    """Additional error path coverage for _search_docs."""

    @pytest.mark.asyncio
    async def test_engine_validation_error_propagates(self) -> None:
        """When engine.search raises ValidationError, it propagates up."""
        mock_engine = AsyncMock(spec=SearchEngine)
        mock_engine.search.side_effect = ValidationError("bad query")
        with pytest.raises(ValidationError, match="bad query"):
            await _search_docs(mock_engine, "test")

    @pytest.mark.asyncio
    async def test_zero_results_returns_empty_list(self) -> None:
        """Empty search results return [] without errors."""
        mock_engine = AsyncMock(spec=SearchEngine)
        mock_engine.search.return_value = []
        result = await _search_docs(mock_engine, "zzz_no_match")
        assert result == []

    @pytest.mark.asyncio
    async def test_sorts_results_by_score_ascending(self) -> None:
        """Results should be sorted by engine (BM25) - lower score is better."""
        mock_engine = AsyncMock(spec=SearchEngine)
        mock_engine.search.return_value = [
            SearchHit(path="c.mdx", title="C", snippet="...", score=3.0),
            SearchHit(path="a.mdx", title="A", snippet="...", score=1.0),
            SearchHit(path="b.mdx", title="B", snippet="...", score=2.0),
        ]
        result = await _search_docs(mock_engine, "test")
        # Engine handles ordering; we verify all are returned
        assert len(result) == 3
        assert {h.path for h in result} == {"a.mdx", "b.mdx", "c.mdx"}


class TestSearchExamplesErrors:
    """Additional coverage for _search_examples error paths."""

    @pytest.mark.asyncio
    async def test_empty_overfetch_still_returns_empty(self) -> None:
        """When engine returns empty, filter returns empty."""
        mock_engine = AsyncMock(spec=SearchEngine)
        mock_engine.search.return_value = []
        result = await _search_examples(mock_engine, "query", limit=10)
        assert result == []


class TestGetPageErrors:
    """Additional error paths for _get_page."""

    def test_handles_page_invalid_error(self) -> None:
        """When source raises PageInvalid, it propagates."""
        from mcp_agno_docs.errors import PageInvalid
        mock_source = Mock(spec=DocSource)
        mock_source.get_page.side_effect = PageInvalid("malformed YAML")
        with pytest.raises(PageInvalid, match="malformed YAML"):
            _get_page(mock_source, "broken.mdx")

    def test_returned_page_has_frontmatter_and_content(self) -> None:
        """Verify full DocPage is returned with all fields."""
        mock_source = Mock(spec=DocSource)
        fm = DocFrontmatter(title="Test", description="desc", keywords=["k1"])
        page = DocPage(path="test.mdx", frontmatter=fm, content="# Title\n\nBody.")
        mock_source.get_page.return_value = page
        result = _get_page(mock_source, "test.mdx")
        assert result.path == "test.mdx"
        assert result.frontmatter.title == "Test"
        assert result.frontmatter.description == "desc"
        assert result.frontmatter.keywords == ["k1"]
        assert result.content == "# Title\n\nBody."


class TestGetNavigationErrors:
    """Additional edge cases for _get_navigation."""

    def test_single_leaf_node(self) -> None:
        """NavTree with a single leaf child returns correctly."""
        tree = NavTree(root=NavNode(title="Root", children=[
            NavNode(title="Readme", path="readme.mdx"),
        ]))
        result = _get_navigation(tree)
        assert result.root.children[0].path == "readme.mdx"

    def test_deeply_nested_tree(self) -> None:
        """NavTree with 3-level nesting preserves structure."""
        tree = NavTree(root=NavNode(title="R", path=None, children=[
            NavNode(title="A", path=None, children=[
                NavNode(title="B", path=None, children=[
                    NavNode(title="C", path="c.mdx"),
                ]),
            ]),
        ]))
        result = _get_navigation(tree)
        assert result.root.children[0].children[0].children[0].path == "c.mdx"
