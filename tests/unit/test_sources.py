"""Tests for the DocSource abstract base class and LocalMDXSource internal helpers.

Verifies that DocSource cannot be instantiated directly and that subclasses
MUST implement all abstract methods. Also tests _split_frontmatter and
_process_file internal helpers.
"""

from pathlib import Path

import pytest
import yaml

from mcp_agno_docs.models import DocFrontmatter
from mcp_agno_docs.sources.base import DocSource
from mcp_agno_docs.sources.local_mdx import _process_file, _split_frontmatter


class TestDocSourceContract:
    """DocSource ABC enforces its interface contract."""

    def test_cannot_instantiate_abc_directly(self) -> None:
        """Instantiating DocSource directly MUST raise TypeError."""
        with pytest.raises(TypeError, match="abstract"):
            DocSource()  # type: ignore[abstract]

    def test_subclass_without_load_fails_instantiation(self) -> None:
        """Missing async load() prevents instantiation."""

        class Incomplete(DocSource):
            def get_page(self, path: str):  # noqa: D102
                pass

            def list_pages(self) -> list[str]:  # noqa: D102
                return []

            def iter_index_documents(self):  # noqa: D102
                return iter([])

        with pytest.raises(TypeError, match="abstract"):
            Incomplete()  # type: ignore[abstract]

    def test_subclass_without_get_page_fails_instantiation(self) -> None:
        """Missing get_page() prevents instantiation."""

        class Incomplete(DocSource):
            async def load(self) -> None:  # noqa: D102
                pass

            def list_pages(self) -> list[str]:  # noqa: D102
                return []

            def iter_index_documents(self):  # noqa: D102
                return iter([])

        with pytest.raises(TypeError, match="abstract"):
            Incomplete()  # type: ignore[abstract]

    def test_fully_implemented_subclass_instantiates(self) -> None:
        """A subclass implementing ALL abstract methods instantiates successfully."""

        class Complete(DocSource):
            async def load(self) -> None:
                pass

            def get_page(self, path: str):
                raise NotImplementedError

            def list_pages(self) -> list[str]:
                return []

            def iter_index_documents(self):
                return iter([])

        source = Complete()
        assert isinstance(source, DocSource)


class TestSplitFrontmatter:
    """Unit tests for _split_frontmatter with the new ValueError-on-error signature."""

    @pytest.fixture
    def valid_frontmatter_raw(self) -> str:
        """MDX raw text with valid YAML frontmatter."""
        return "---\ntitle: Getting Started\ndescription: A guide\nkeywords:\n  - install\n  - setup\n---\n\n# Content\n\nBody text here."

    @pytest.fixture
    def no_frontmatter_raw(self) -> str:
        """MDX raw text with no frontmatter fence."""
        return "# Just a title\n\nSome content."

    @pytest.fixture
    def empty_frontmatter_raw(self) -> str:
        """MDX raw text with empty frontmatter block."""
        return "---\n---\n# Content after empty frontmatter."

    @pytest.fixture
    def invalid_yaml_raw(self) -> str:
        """MDX raw text with broken YAML frontmatter."""
        return "---\ninvalid: [unclosed\n---\n\nContent here."

    def test_returns_none_for_no_frontmatter(self, no_frontmatter_raw: str) -> None:
        """When no --- fence exists, returns (None, raw_text)."""
        fm, content = _split_frontmatter(no_frontmatter_raw)
        assert fm is None
        assert content == no_frontmatter_raw

    def test_parses_valid_frontmatter(self, valid_frontmatter_raw: str) -> None:
        """Valid YAML frontmatter returns DocFrontmatter and body content."""
        fm, content = _split_frontmatter(valid_frontmatter_raw)
        assert isinstance(fm, DocFrontmatter)
        assert fm.title == "Getting Started"
        assert fm.description == "A guide"
        assert fm.keywords == ["install", "setup"]
        assert "Body text here" in content

    def test_empty_frontmatter_returns_defaults(self, empty_frontmatter_raw: str) -> None:
        """Empty frontmatter block returns DocFrontmatter with defaults."""
        fm, content = _split_frontmatter(empty_frontmatter_raw)
        assert isinstance(fm, DocFrontmatter)
        assert fm.title == ""
        assert fm.description is None
        assert fm.keywords == []

    def test_invalid_yaml_raises_value_error(self, invalid_yaml_raw: str) -> None:
        """Malformed YAML raises ValueError instead of returning error string."""
        with pytest.raises(ValueError, match="YAML"):
            _split_frontmatter(invalid_yaml_raw)

    def test_non_dict_frontmatter_raises_value_error(self) -> None:
        """Frontmatter that parses as a list (not dict) raises ValueError."""
        raw = "---\n- item1\n- item2\n---\n\nContent."
        with pytest.raises(ValueError, match="not a YAML mapping"):
            _split_frontmatter(raw)


class TestProcessFile:
    """Unit tests for _process_file returning FileResult instead of mutating dicts."""

    @pytest.fixture
    def tmp_mdx_dir(self, tmp_path: Path) -> Path:
        """Create a temporary directory with .mdx files for testing."""
        return tmp_path

    def test_valid_file_returns_page(self, tmp_mdx_dir: Path) -> None:
        """A valid .mdx file returns FileResult with page set."""
        mdx = tmp_mdx_dir / "valid.mdx"
        mdx.write_text(
            "---\ntitle: Test Page\n---\n\n# Hello World\n\nSome content.",
            encoding="utf-8",
        )
        result = _process_file(mdx, tmp_mdx_dir)
        assert result.error is None
        assert result.page is not None
        assert result.page.path == "valid.mdx"
        assert result.page.frontmatter.title == "Test Page"
        assert "Hello World" in result.page.content

    def test_no_frontmatter_file_returns_page_with_defaults(self, tmp_mdx_dir: Path) -> None:
        """A .mdx file without frontmatter returns page with default frontmatter."""
        mdx = tmp_mdx_dir / "no-fm.mdx"
        mdx.write_text("# Just Content\n\nNo frontmatter here.", encoding="utf-8")
        result = _process_file(mdx, tmp_mdx_dir)
        assert result.error is None
        assert result.page is not None
        assert result.page.path == "no-fm.mdx"
        assert result.page.frontmatter.title == ""
        assert result.page.frontmatter.keywords == []

    def test_invalid_yaml_returns_error_result(self, tmp_mdx_dir: Path) -> None:
        """Broken YAML frontmatter returns FileResult with error set, page=None."""
        mdx = tmp_mdx_dir / "bad.mdx"
        mdx.write_text(
            "---\nbroken: [unclosed\n---\n\nContent.",
            encoding="utf-8",
        )
        result = _process_file(mdx, tmp_mdx_dir)
        assert result.page is None
        assert result.error is not None
        assert "bad.mdx" in result.path

    def test_dotfile_is_skipped(self, tmp_mdx_dir: Path) -> None:
        """Hidden files (starting with .) return FileResult with page=None, error=None."""
        dotfile = tmp_mdx_dir / ".hidden.mdx"
        dotfile.write_text("# Hidden", encoding="utf-8")
        result = _process_file(dotfile, tmp_mdx_dir)
        assert result.page is None
        assert result.error is None

    def test_unreadable_file_is_skipped(self, tmp_mdx_dir: Path) -> None:
        """A non-existent file returns FileResult with page=None."""
        nonexistent = tmp_mdx_dir / "gone.mdx"
        result = _process_file(nonexistent, tmp_mdx_dir)
        assert result.page is None

    def test_path_is_posix_normalized(self, tmp_mdx_dir: Path) -> None:
        """The returned path uses POSIX forward slashes."""
        subdir = tmp_mdx_dir / "api"
        subdir.mkdir()
        mdx = subdir / "agents.mdx"
        mdx.write_text("---\ntitle: Agents\n---\n\nContent.", encoding="utf-8")
        result = _process_file(mdx, tmp_mdx_dir)
        assert result.page is not None
        assert result.page.path == "api/agents.mdx"
        assert "\\" not in result.page.path
