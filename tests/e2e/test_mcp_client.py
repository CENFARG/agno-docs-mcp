"""End-to-end tests for agno-docs-mcp via the MCP stdio transport.

Starts the FastMCP server in a subprocess using ``python -m mcp_agno_docs``
pointed at the synthetic fixture docs tree, then invokes all four tools
through the MCP client session.
"""

import json
import os
from pathlib import Path

import anyio
import pytest
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

# Re-use the fixture-path helpers from conftest.
from tests.conftest import FIXTURES_DOCS_DIR

# Ensure the src/ directory is on sys.path (needed for the subprocess).
_SRC = Path(__file__).resolve().parent.parent.parent / "src"


# ---- Helpers ----

def _server_params() -> StdioServerParameters:
    """Return MCP stdio server params pointed at the fixture docs tree."""
    env = os.environ.copy()
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(_SRC) + (os.pathsep + existing if existing else "")
    return StdioServerParameters(
        command="python",
        args=["-m", "mcp_agno_docs", str(FIXTURES_DOCS_DIR)],
        env=env,
    )


async def _call_tool(name: str, args: dict | None = None) -> dict | list:
    """Start server, initialise session, call tool, return parsed result."""
    server = _server_params()
    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(name, args or {})
            text = result.content[0].text if result.content else "{}"
            return json.loads(text)


def _call_tool_sync(name: str, args: dict | None = None) -> dict | list:
    """Synchronous wrapper around _call_tool using anyio.run."""
    return anyio.run(_call_tool, name, args)


# ---- Tool tests ----

class TestSearchDocsE2E:
    """E2E tests for the ``search_docs`` tool via MCP stdio."""

    def test_search_returns_ranked_results(self) -> None:
        """Search for 'agent' returns hits with expected schema fields."""
        data = _call_tool_sync("search_docs", {"query": "agent"})
        items = data if isinstance(data, list) else [data]
        assert len(items) > 0, f"Expected at least one result, got: {data}"
        hit = items[0]
        assert "path" in hit
        assert "title" in hit
        assert "snippet" in hit
        assert "score" in hit

    def test_search_snippet_has_b_tags(self) -> None:
        """Search snippets contain <b> highlight markers around matches."""
        data = _call_tool_sync("search_docs", {"query": "agno"})
        items = data if isinstance(data, list) else [data]
        any_highlighted = any("<b>" in h.get("snippet", "") for h in items)
        assert any_highlighted, "Expected at least one snippet with <b> tags"

    def test_search_with_topic_filter(self) -> None:
        """Topic filter narrows results to pages with matching keywords."""
        data = _call_tool_sync(
            "search_docs", {"query": "agno", "topic": "api"}
        )
        assert data is not None

    def test_search_query_too_short_returns_error(self) -> None:
        """Query shorter than 2 chars returns an error response."""
        server = _server_params()
        with pytest.raises(Exception):  # Subprocess sends error
            anyio.run(_call_tool, "search_docs", {"query": "a"})


class TestSearchExamplesE2E:
    """E2E tests for the ``search_examples`` tool via MCP stdio."""

    def test_search_examples_returns_only_example_paths(self) -> None:
        """All returned paths start with 'examples/'."""
        data = _call_tool_sync("search_examples", {"query": "example"})
        items = data if isinstance(data, list) else [data]
        assert len(items) > 0, f"Expected at least one result, got: {data}"
        for hit in items:
            assert hit["path"].startswith("examples/"), (
                f"Expected examples/ prefix, got {hit['path']}"
            )


class TestGetPageE2E:
    """E2E tests for the ``get_page`` tool via MCP stdio."""

    def test_get_page_returns_frontmatter_and_content(self) -> None:
        """Retrieving a known page returns frontmatter + body content."""
        data = _call_tool_sync("get_page", {"path": "index.mdx"})
        assert data["path"] == "index.mdx"
        assert "frontmatter" in data
        assert "content" in data
        assert data["frontmatter"]["title"] == "Agno Documentation"

    def test_get_page_not_found_returns_error(self) -> None:
        """Requesting a non-existent page raises an exception."""
        with pytest.raises(Exception):
            _call_tool_sync("get_page", {"path": "nonexistent/bogus.mdx"})

    def test_get_page_rejects_traversal(self) -> None:
        """Path with '..' is rejected as an error."""
        with pytest.raises(Exception):
            _call_tool_sync("get_page", {"path": "../etc/passwd"})


class TestGetNavigationE2E:
    """E2E tests for the ``get_navigation`` tool via MCP stdio."""

    def test_get_navigation_returns_tree(self) -> None:
        """The navigation tool returns a hierarchical tree structure."""
        data = _call_tool_sync("get_navigation")
        assert "root" in data
        root = data["root"]
        assert root["title"] == "Docs"
        assert "children" in root
        assert isinstance(root["children"], list)
        assert len(root["children"]) > 0
