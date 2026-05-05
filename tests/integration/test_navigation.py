"""Integration tests for Navigation parser.

Parses the fixture docs.json into a NavTree and verifies tree structure,
folder vs. page nodes, and ordering preservation.
"""

from pathlib import Path

import pytest

from mcp_agno_docs.errors import StartupError, ValidationError
from tests.conftest import FIXTURES_DOCS_JSON

from mcp_agno_docs.indexer.navigation import load_navigation


class TestLoadNavigation:
    """Integration tests for load_navigation over the fixture docs.json."""

    def test_parses_docs_json_into_nav_tree(self) -> None:
        """Load the fixture docs.json and return a NavTree."""
        tree = load_navigation(FIXTURES_DOCS_JSON)

        assert tree.root.title == "Docs"
        # Root should be a folder (no path), children are tabs.
        assert tree.root.path is None

    def test_root_children_are_tabs(self) -> None:
        """Each tab becomes a top-level child of the root."""
        tree = load_navigation(FIXTURES_DOCS_JSON)

        tab_titles = [child.title for child in tree.root.children]
        assert "Home" in tab_titles
        assert "API" in tab_titles

    def test_home_tab_contains_welcome_group(self) -> None:
        """Welcome group under Home tab has index and getting-started."""
        tree = load_navigation(FIXTURES_DOCS_JSON)

        home_tab = next(c for c in tree.root.children if c.title == "Home")
        welcome_group = next(c for c in home_tab.children if c.title == "Welcome")

        page_titles = [p.title for p in welcome_group.children]
        assert "index" in page_titles
        assert "getting-started" in page_titles

    def test_leaf_pages_have_path_set(self) -> None:
        """Page nodes (strings in JSON) become NavNodes with path set."""
        tree = load_navigation(FIXTURES_DOCS_JSON)

        home_tab = next(c for c in tree.root.children if c.title == "Home")
        welcome_group = next(c for c in home_tab.children if c.title == "Welcome")
        index_page = next(c for c in welcome_group.children if c.title == "index")

        assert index_page.path is not None
        assert ".mdx" in str(index_page.path)

    def test_folder_nodes_have_path_none(self) -> None:
        """Groups become folder nodes with path=None."""
        tree = load_navigation(FIXTURES_DOCS_JSON)

        home_tab = next(c for c in tree.root.children if c.title == "Home")
        welcome_group = next(c for c in home_tab.children if c.title == "Welcome")

        assert welcome_group.path is None
        assert len(welcome_group.children) > 0

    def test_api_tab_contains_core_group_with_agents(self) -> None:
        """API tab has Core group with api/agents as a child."""
        tree = load_navigation(FIXTURES_DOCS_JSON)

        api_tab = next(c for c in tree.root.children if c.title == "API")
        core_group = next(c for c in api_tab.children if c.title == "Core")

        page_paths = [c.path for c in core_group.children]
        assert any("api/agents" in str(p) for p in page_paths if p)
        assert any("api/models" in str(p) for p in page_paths if p)

    def test_guides_group_contains_installation(self) -> None:
        """Home → Guides contains installation guide."""
        tree = load_navigation(FIXTURES_DOCS_JSON)

        home_tab = next(c for c in tree.root.children if c.title == "Home")
        guides_group = next(c for c in home_tab.children if c.title == "Guides")

        installation = next(c for c in guides_group.children if c.title == "guides/installation")
        assert installation.path is not None


class TestLoadNavigationErrors:
    """Error handling: missing file, malformed JSON."""

    def test_missing_docs_json_raises_startup_error(self, tmp_path: Path) -> None:
        """Calling load_navigation on a non-existent path raises StartupError."""
        bogus = tmp_path / "nope.json"
        with pytest.raises(StartupError, match="docs.json not found"):
            load_navigation(bogus)

    def test_malformed_json_raises_validation_error(self, tmp_path: Path) -> None:
        """Non-JSON content raises ValidationError."""
        bad_json = tmp_path / "docs.json"
        bad_json.write_text("this is not json at all", encoding="utf-8")
        with pytest.raises(ValidationError, match="not valid JSON"):
            load_navigation(bad_json)

    def test_missing_navigation_key_raises_validation_error(self, tmp_path: Path) -> None:
        """JSON without 'navigation' top-level key raises ValidationError."""
        bad = tmp_path / "docs.json"
        bad.write_text('{"theme": "mint"}', encoding="utf-8")
        with pytest.raises(ValidationError, match="missing top-level 'navigation'"):
            load_navigation(bad)

    def test_empty_tabs_list_produces_empty_root(self, tmp_path: Path) -> None:
        """Empty tabs list yields a Docs root with no tab children."""
        empty = tmp_path / "docs.json"
        empty.write_text('{"navigation": {"tabs": []}}', encoding="utf-8")
        tree = load_navigation(empty)
        assert tree.root.title == "Docs"
        assert tree.root.children == []
