"""Tests for Pydantic models in mcp_agno_docs.models."""

from pathlib import Path

import pytest
from pydantic import ValidationError as PydanticValidationError

from mcp_agno_docs.models import (
    DocFrontmatter,
    DocPage,
    FTS5Config,
    GetPageInput,
    LocalSourceConfig,
    NavNode,
    NavTree,
    SearchDocsInput,
    SearchExamplesInput,
)


class TestDocFrontmatter:
    """DocFrontmatter defaults and field types."""

    def test_empty_construction_yields_defaults(self) -> None:
        """DocFrontmatter() gives empty title and empty keywords list."""
        fm = DocFrontmatter()
        assert fm.title == ""
        assert fm.description is None
        assert fm.keywords == []

    def test_explicit_title_and_keywords(self) -> None:
        """Providing title and keywords uses them verbatim."""
        fm = DocFrontmatter(
            title="Getting Started", keywords=["install", "setup"]
        )
        assert fm.title == "Getting Started"
        assert fm.description is None
        assert fm.keywords == ["install", "setup"]

    def test_description_stores_when_provided(self) -> None:
        """description accepts string value."""
        fm = DocFrontmatter(description="How to install Agno")
        assert fm.description == "How to install Agno"


class TestSearchDocsInput:
    """SearchDocsInput validation — min_length=2, limit 1-50."""

    def test_query_too_short_raises_validation_error(self) -> None:
        """A single-character query must be rejected."""
        with pytest.raises(PydanticValidationError, match="String should have at least 2 characters"):
            SearchDocsInput(query="a")

    def test_query_exactly_two_chars_passes(self) -> None:
        """A 2-char query is the minimum allowed."""
        inp = SearchDocsInput(query="ab")
        assert inp.query == "ab"
        assert inp.topic is None
        assert inp.limit == 10

    def test_limit_default_is_10(self) -> None:
        """Default limit is 10."""
        inp = SearchDocsInput(query="search term")
        assert inp.limit == 10

    def test_limit_below_1_is_rejected(self) -> None:
        """Limit < 1 must be rejected."""
        with pytest.raises(PydanticValidationError, match="greater than or equal to 1"):
            SearchDocsInput(query="test", limit=0)

    def test_limit_above_50_is_rejected(self) -> None:
        """Limit > 50 must be rejected."""
        with pytest.raises(PydanticValidationError, match="less than or equal to 50"):
            SearchDocsInput(query="test", limit=51)

    def test_topic_optional_default_none(self) -> None:
        """topic is optional and defaults to None."""
        inp = SearchDocsInput(query="install")
        assert inp.topic is None


class TestSearchExamplesInput:
    """SearchExamplesInput — same validation as SearchDocsInput."""

    def test_query_too_short_raises(self) -> None:
        """A single-character query must be rejected."""
        with pytest.raises(PydanticValidationError, match="String should have at least 2 characters"):
            SearchExamplesInput(query="x")

    def test_limit_default(self) -> None:
        """Default limit is 10."""
        inp = SearchExamplesInput(query="example query")
        assert inp.limit == 10

    def test_limit_boundaries(self) -> None:
        """Limit within 1..50 is accepted."""
        inp = SearchExamplesInput(query="test", limit=1)
        assert inp.limit == 1
        inp = SearchExamplesInput(query="test", limit=50)
        assert inp.limit == 50


class TestNavNode:
    """NavNode recursion and defaults."""

    def test_single_node_no_children(self) -> None:
        """A leaf NavNode has no children."""
        node = NavNode(title="Overview", path="index.mdx")
        assert node.title == "Overview"
        assert node.path == "index.mdx"
        assert node.children == []

    def test_node_with_path_none_is_folder(self) -> None:
        """A folder node has path=None."""
        node = NavNode(title="Guides")
        assert node.title == "Guides"
        assert node.path is None
        assert node.children == []

    def test_nested_children_recursion(self) -> None:
        """NavNode children can contain NavNodes recursively."""
        child = NavNode(title="Deep Dive", path="guides/deep.mdx")
        parent = NavNode(title="Guides", children=[child])
        assert len(parent.children) == 1
        assert parent.children[0].title == "Deep Dive"
        assert parent.children[0].path == "guides/deep.mdx"


class TestNavTree:
    """NavTree wraps a root NavNode."""

    def test_tree_with_root_node(self) -> None:
        """NavTree holds a root NavNode."""
        root = NavNode(title="Docs", children=[NavNode(title="Home", path="index.mdx")])
        tree = NavTree(root=root)
        assert tree.root.title == "Docs"
        assert len(tree.root.children) == 1


class TestLocalSourceConfig:
    """LocalSourceConfig validates DirectoryPath."""

    def test_root_path_must_exist(self) -> None:
        """Non-existent directory raises Pydantic validation error."""
        with pytest.raises(PydanticValidationError, match="Path does not point to a directory"):
            LocalSourceConfig(root_path=Path("/this/path/does/not/exist/at/all"))

    def test_valid_directory_path(self, tmp_path: Path) -> None:
        """Existing tmp_path directory is accepted."""
        cfg = LocalSourceConfig(root_path=tmp_path)
        assert cfg.root_path == tmp_path


class TestGetPageInput:
    """GetPageInput accepts a path string."""

    def test_path_stored_as_given(self) -> None:
        """path field is stored as-is."""
        inp = GetPageInput(path="api/agents.mdx")
        assert inp.path == "api/agents.mdx"


class TestFTS5Config:
    """FTS5Config defaults and validation."""

    def test_defaults(self) -> None:
        """Default config: db_path=None, tokenizer='porter'."""
        cfg = FTS5Config()
        assert cfg.db_path is None
        assert cfg.tokenizer == "porter"

    def test_explicit_tokenizer(self) -> None:
        """Setting a custom tokenizer works."""
        cfg = FTS5Config(tokenizer="unicode61")
        assert cfg.tokenizer == "unicode61"

    def test_db_path_can_be_set(self, tmp_path: Path) -> None:
        """A file path for DB can be specified."""
        db = tmp_path / "test.db"
        cfg = FTS5Config(db_path=str(db))
        assert cfg.db_path == str(db)


class TestDocPage:
    """DocPage composite model."""

    def test_doc_page_construction(self) -> None:
        """DocPage holds path, frontmatter, and content."""
        fm = DocFrontmatter(title="Hello", keywords=["world"])
        page = DocPage(path="hello.mdx", frontmatter=fm, content="# Hello\n\nWorld.")
        assert page.path == "hello.mdx"
        assert page.frontmatter.title == "Hello"
        assert "Hello" in page.content
