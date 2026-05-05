"""Integration tests for LocalMDXSource.

Tests the LocalMDXSource adapter over the real fixture file tree in
``tests/fixtures/docs/``. Covers load(), get_page(), list_pages(),
iter_index_documents(), path normalization, frontmatter parsing, and
invalid file handling.
"""

import logging
from pathlib import Path

import pytest

from mcp_agno_docs.errors import PageNotFound
from mcp_agno_docs.models import DocPage, IndexDocument, LocalSourceConfig
from tests.conftest import FIXTURES_DOCS_DIR

# Import will fail until local_mdx.py exists — expected RED.
from mcp_agno_docs.sources.local_mdx import LocalMDXSource


class TestLocalMDXSourceLoad:
    """Tests for LocalMDXSource.load() against the fixture tree."""

    @pytest.mark.asyncio
    async def test_load_discovers_all_valid_mdx_files(self) -> None:
        """load() finds 8 valid .mdx files (1 invalid, 1 no frontmatter acceptable)."""
        cfg = LocalSourceConfig(root_path=FIXTURES_DOCS_DIR)
        source = LocalMDXSource(cfg)
        await source.load()

        pages = source.list_pages()
        assert len(pages) >= 7  # at minimum: all valid mdx minus the invalid one

    @pytest.mark.asyncio
    async def test_load_parses_frontmatter_fields(self) -> None:
        """Frontmatter title, description, and keywords are extracted."""
        cfg = LocalSourceConfig(root_path=FIXTURES_DOCS_DIR)
        source = LocalMDXSource(cfg)
        await source.load()

        page = source.get_page("index.mdx")
        assert page.frontmatter.title == "Agno Documentation"
        assert page.frontmatter.description == "Welcome to the Agno framework documentation"
        assert "agno" in page.frontmatter.keywords

    @pytest.mark.asyncio
    async def test_load_parses_page_body_content(self) -> None:
        """The MDX body after frontmatter is stored as content."""
        cfg = LocalSourceConfig(root_path=FIXTURES_DOCS_DIR)
        source = LocalMDXSource(cfg)
        await source.load()

        page = source.get_page("index.mdx")
        assert "# Welcome to Agno" in page.content
        assert "[Get Started]" in page.content

    @pytest.mark.asyncio
    async def test_file_without_frontmatter_gets_defaults(self) -> None:
        """A .mdx file with no YAML frontmatter is parsed with defaults."""
        cfg = LocalSourceConfig(root_path=FIXTURES_DOCS_DIR)
        source = LocalMDXSource(cfg)
        await source.load()

        page = source.get_page("no-frontmatter.mdx")
        assert page.frontmatter.title == ""
        assert page.frontmatter.description is None
        assert page.frontmatter.keywords == []
        assert "# File Without Frontmatter" in page.content

    @pytest.mark.asyncio
    async def test_paths_are_posix_normalized(self) -> None:
        """All stored paths use forward slashes, regardless of OS."""
        cfg = LocalSourceConfig(root_path=FIXTURES_DOCS_DIR)
        source = LocalMDXSource(cfg)
        await source.load()

        all_paths = source.list_pages()
        for path in all_paths:
            assert "\\" not in path, f"Path {path!r} contains backslashes"

    @pytest.mark.asyncio
    async def test_invalid_yaml_file_is_excluded_from_pages(self) -> None:
        """The invalid.mdx file must NOT appear in list_pages."""
        cfg = LocalSourceConfig(root_path=FIXTURES_DOCS_DIR)
        source = LocalMDXSource(cfg)
        await source.load()

        all_paths = source.list_pages()
        invalid_paths = [p for p in all_paths if "invalid" in p]
        assert len(invalid_paths) == 0, f"Invalid page leaked into pages: {invalid_paths}"


class TestLocalMDXSourceGetPage:
    """Tests for LocalMDXSource.get_page()."""

    @pytest.mark.asyncio
    async def test_get_page_returns_doc_page_for_known_path(self) -> None:
        """get_page retrieves a correctly parsed DocPage."""
        cfg = LocalSourceConfig(root_path=FIXTURES_DOCS_DIR)
        source = LocalMDXSource(cfg)
        await source.load()

        page = source.get_page("api/agents.mdx")
        assert isinstance(page, DocPage)
        assert page.path == "api/agents.mdx"
        assert page.frontmatter.title == "Agents API"

    @pytest.mark.asyncio
    async def test_get_page_raises_page_not_found_for_missing(self) -> None:
        """Requesting a non-existent path raises PageNotFound."""
        cfg = LocalSourceConfig(root_path=FIXTURES_DOCS_DIR)
        source = LocalMDXSource(cfg)
        await source.load()

        with pytest.raises(PageNotFound):
            source.get_page("bogus/nope.mdx")

    @pytest.mark.asyncio
    async def test_get_page_handles_path_without_leading_slash(self) -> None:
        """A path without leading slash is accepted and normalized."""
        cfg = LocalSourceConfig(root_path=FIXTURES_DOCS_DIR)
        source = LocalMDXSource(cfg)
        await source.load()

        page = source.get_page("getting-started.mdx")
        assert page.path == "getting-started.mdx"
        assert "Getting Started" in page.frontmatter.title


class TestLocalMDXSourceListPages:
    """Tests for list_pages()."""

    @pytest.mark.asyncio
    async def test_list_pages_returns_all_loaded_paths(self) -> None:
        """list_pages returns a sorted list of all known page paths."""
        cfg = LocalSourceConfig(root_path=FIXTURES_DOCS_DIR)
        source = LocalMDXSource(cfg)
        await source.load()

        pages = source.list_pages()
        assert "index.mdx" in pages
        assert "api/agents.mdx" in pages
        assert "getting-started.mdx" in pages
        assert "guides/installation.mdx" in pages
        assert "examples/basic.mdx" in pages
        assert "examples/advanced.mdx" in pages

    @pytest.mark.asyncio
    async def test_list_pages_sorted_order(self) -> None:
        """list_pages returns paths in sorted order."""
        cfg = LocalSourceConfig(root_path=FIXTURES_DOCS_DIR)
        source = LocalMDXSource(cfg)
        await source.load()

        pages = source.list_pages()
        assert pages == sorted(pages)


class TestLocalMDXSourceIterIndexDocuments:
    """Tests for iter_index_documents()."""

    @pytest.mark.asyncio
    async def test_iter_index_documents_yields_all_valid_pages(self) -> None:
        """Each valid page becomes an IndexDocument."""
        cfg = LocalSourceConfig(root_path=FIXTURES_DOCS_DIR)
        source = LocalMDXSource(cfg)
        await source.load()

        docs = list(source.iter_index_documents())
        pages = source.list_pages()
        assert len(docs) == len(pages)

    @pytest.mark.asyncio
    async def test_index_documents_have_correct_fields(self) -> None:
        """IndexDocument carries path, title, and content from the page."""
        cfg = LocalSourceConfig(root_path=FIXTURES_DOCS_DIR)
        source = LocalMDXSource(cfg)
        await source.load()

        doc = next(d for d in source.iter_index_documents() if d.path == "api/agents.mdx")
        assert isinstance(doc, IndexDocument)
        assert doc.title == "Agents API"
        assert "create and manage AI agents" in doc.content

    @pytest.mark.asyncio
    async def test_iter_index_documents_excludes_invalid_pages(self) -> None:
        """Invalid pages are NOT yielded by iter_index_documents."""
        cfg = LocalSourceConfig(root_path=FIXTURES_DOCS_DIR)
        source = LocalMDXSource(cfg)
        await source.load()

        all_paths = [d.path for d in source.iter_index_documents()]
        assert not any("invalid" in p for p in all_paths)
