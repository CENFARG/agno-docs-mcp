"""Unit tests for MCP tool logic with mocked SearchEngine and DocSource.

Tests the internal tool functions that contain the business logic,
independent of FastMCP decorators and request context wiring.
"""

from unittest.mock import AsyncMock, Mock

import pytest

from mcp_agno_docs.errors import PageNotFound, ValidationError
from mcp_agno_docs.models import (
    DocFrontmatter,
    DocHit,
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
from mcp_agno_docs.utils import normalise_path


# ---- Fixtures ----

def _make_search_hit(path: str, title: str, snippet: str = "...", score: float = 1.0) -> SearchHit:
    """Create a SearchHit with minimal required fields."""
    return SearchHit(path=path, title=title, snippet=snippet, score=score)


# ---- search_docs ----

class TestSearchDocs:
    """Unit tests for _search_docs using a mocked SearchEngine."""

    @pytest.mark.asyncio
    async def test_calls_engine_search_and_returns_doc_hits(self) -> None:
        """_search_docs calls engine.search with given params and wraps results as DocHit."""
        mock_engine = AsyncMock(spec=SearchEngine)
        mock_engine.search.return_value = [
            _make_search_hit("api/agents.mdx", "Agents API"),
        ]

        result = await _search_docs(mock_engine, "agents", topic="api", limit=5)

        mock_engine.search.assert_awaited_once_with("agents", topic="api", limit=5)
        assert len(result) == 1
        assert isinstance(result[0], DocHit)
        assert result[0].path == "api/agents.mdx"
        assert result[0].title == "Agents API"

    @pytest.mark.asyncio
    async def test_default_topic_is_none(self) -> None:
        """When topic is not provided, it passes None to engine.search."""
        mock_engine = AsyncMock(spec=SearchEngine)
        mock_engine.search.return_value = []

        await _search_docs(mock_engine, "install")

        mock_engine.search.assert_awaited_once_with("install", topic=None, limit=10)

    @pytest.mark.asyncio
    async def test_validates_input_via_pydantic(self) -> None:
        """Query shorter than 2 characters raises a Pydantic ValidationError."""
        mock_engine = AsyncMock(spec=SearchEngine)

        with pytest.raises(ValidationError):
            await _search_docs(mock_engine, "a")

        mock_engine.search.assert_not_awaited()


# ---- search_examples ----

class TestSearchExamples:
    """Unit tests for _search_examples with mocked SearchEngine."""

    @pytest.mark.asyncio
    async def test_filters_results_to_examples_prefix(self) -> None:
        """Only hits whose path starts with 'examples/' are returned."""
        mock_engine = AsyncMock(spec=SearchEngine)
        mock_engine.search.return_value = [
            _make_search_hit("examples/basic.mdx", "Basic Example", score=0.5),
            _make_search_hit("api/agents.mdx", "Agents API", score=1.0),
            _make_search_hit("examples/advanced.mdx", "Advanced Example", score=0.8),
            _make_search_hit("guides/install.mdx", "Installation", score=2.0),
        ]

        result = await _search_examples(mock_engine, "example", limit=10)

        paths = {h.path for h in result}
        assert paths == {"examples/basic.mdx", "examples/advanced.mdx"}
        # Verify non-examples paths are excluded.
        assert "api/agents.mdx" not in paths
        assert "guides/install.mdx" not in paths

    @pytest.mark.asyncio
    async def test_overfetches_to_compensate_for_filtering(self) -> None:
        """Over-fetches 4x limit to account for non-examples hits being filtered out."""
        mock_engine = AsyncMock(spec=SearchEngine)
        mock_engine.search.return_value = [
            _make_search_hit(f"examples/page_{i}.mdx", f"Page {i}", score=float(i))
            for i in range(100)
        ]

        await _search_examples(mock_engine, "test", limit=5)

        mock_engine.search.assert_awaited_once_with("test", topic=None, limit=20)

    @pytest.mark.asyncio
    async def test_respects_limit_after_filtering(self) -> None:
        """Returned hits are capped at limit even when over-fetching."""
        mock_engine = AsyncMock(spec=SearchEngine)
        mock_engine.search.return_value = [
            _make_search_hit(f"examples/page_{i}.mdx", f"Page {i}", score=float(i))
            for i in range(50)
        ]

        result = await _search_examples(mock_engine, "page", limit=3)

        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_examples_match(self) -> None:
        """Empty list when no hits start with 'examples/'."""
        mock_engine = AsyncMock(spec=SearchEngine)
        mock_engine.search.return_value = [
            _make_search_hit("api/models.mdx", "Models"),
        ]

        result = await _search_examples(mock_engine, "model")

        assert result == []

    @pytest.mark.asyncio
    async def test_validates_query_length(self) -> None:
        """Query < 2 chars raises Pydantic ValidationError (via SearchExamplesInput)."""
        mock_engine = AsyncMock(spec=SearchEngine)

        with pytest.raises(ValidationError):
            await _search_examples(mock_engine, "x")

        mock_engine.search.assert_not_awaited()


# ---- get_page path normalisation ----

class TestNormalisePath:
    """Unit tests for _normalise_path helper used by _get_page."""

    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("api/agents.mdx", "api/agents.mdx"),
            ("/api/agents.mdx", "api/agents.mdx"),  # leading slash stripped
            ("api//agents.mdx", "api/agents.mdx"),  # double slash collapsed
            ("./api/agents.mdx", "api/agents.mdx"),  # leading ./ removed
            ("api/./agents.mdx", "api/agents.mdx"),  # embedded ./ removed
            (r"api\agents.mdx", "api/agents.mdx"),  # backslash → forward slash
            ("getting-started.mdx", "getting-started.mdx"),
            ("", ""),  # empty → empty
            ("/", ""),  # only slash → empty
        ],
    )
    def test_normalises_path(self, raw: str, expected: str) -> None:
        """Paths are normalised: leading slash stripped, backslash converted, . collapsed."""
        assert normalise_path(raw) == expected

    def test_rejects_parent_traversal(self) -> None:
        """Path containing '..' raises ValidationError."""
        with pytest.raises(ValidationError, match="traversal"):
            normalise_path("../etc/passwd")

    def test_rejects_double_dot_anywhere(self) -> None:
        """'..' anywhere in the path is rejected."""
        with pytest.raises(ValidationError, match="traversal"):
            normalise_path("api/../secrets")


# ---- get_page ----

class TestGetPage:
    """Unit tests for _get_page with mocked DocSource."""

    def test_returns_doc_page_for_valid_path(self) -> None:
        """_get_page calls source.get_page with normalised path and returns the page."""
        mock_source = Mock(spec=DocSource)
        page = DocPage(
            path="api/agents.mdx",
            frontmatter=DocFrontmatter(title="Agents", description="API ref"),
            content="# Agents\n\nContent here.",
        )
        mock_source.get_page.return_value = page

        result = _get_page(mock_source, "/api/agents.mdx")

        mock_source.get_page.assert_called_once_with("api/agents.mdx")
        assert result.path == "api/agents.mdx"
        assert result.frontmatter.title == "Agents"

    def test_rejects_path_traversal_at_tool_level(self) -> None:
        """Path with '..' raises ValidationError before touching the source."""
        mock_source = Mock(spec=DocSource)

        with pytest.raises(ValidationError, match="traversal"):
            _get_page(mock_source, "../secrets")

        mock_source.get_page.assert_not_called()

    def test_propagates_page_not_found(self) -> None:
        """When the source raises PageNotFound, it propagates to the caller."""
        mock_source = Mock(spec=DocSource)
        mock_source.get_page.side_effect = PageNotFound("missing")

        with pytest.raises(PageNotFound, match="missing"):
            _get_page(mock_source, "bogus.mdx")

    def test_validates_input_via_pydantic(self) -> None:
        """GetPageInput validates the path field exists (type-level check)."""
        mock_source = Mock(spec=DocSource)
        # path is a required str field — any string is valid.
        # The main validation is traversal check, tested above.
        result_page = DocPage(
            path="guides/install.mdx",
            frontmatter=DocFrontmatter(title="Install"),
            content="...",
        )
        mock_source.get_page.return_value = result_page

        result = _get_page(mock_source, "guides/install.mdx")

        assert result.path == "guides/install.mdx"


# ---- get_navigation ----

class TestGetNavigation:
    """Unit tests for _get_navigation."""

    def test_returns_cached_nav_tree(self) -> None:
        """_get_navigation returns the NavTree passed as argument (cached)."""
        tree = NavTree(
            root=NavNode(
                title="Docs",
                path=None,
                children=[
                    NavNode(title="Home", path="index.mdx"),
                    NavNode(
                        title="API",
                        path=None,
                        children=[NavNode(title="Agents", path="api/agents.mdx")],
                    ),
                ],
            )
        )

        result = _get_navigation(tree)

        assert result is tree
        assert result.root.title == "Docs"
        assert len(result.root.children) == 2
        assert result.root.children[0].title == "Home"
        assert result.root.children[0].path == "index.mdx"

    def test_returns_empty_nav_when_no_children(self) -> None:
        """NavTree with empty root children is returned as-is."""
        tree = NavTree(root=NavNode(title="Docs", path=None, children=[]))

        result = _get_navigation(tree)

        assert result is tree
        assert result.root.children == []
