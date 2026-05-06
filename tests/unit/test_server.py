"""Unit tests for server module: AppContext, run_server, lifespan."""
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from mcp_agno_docs.models import NavTree, NavNode
from mcp_agno_docs.search.base import SearchEngine
from mcp_agno_docs.sources.base import DocSource


class TestAppContext:
    """AppContext stores the wired dependencies."""

    def test_stores_source_engine_and_nav(self) -> None:
        from mcp_agno_docs.server import AppContext
        source = MagicMock(spec=DocSource)
        engine = MagicMock(spec=SearchEngine)
        nav = NavTree(root=NavNode(title="Docs"))
        ctx = AppContext(source=source, engine=engine, nav=nav)
        assert ctx.source is source
        assert ctx.engine is engine
        assert ctx.nav is nav

    def test_app_context_attributes_are_typed(self) -> None:
        from mcp_agno_docs.server import AppContext
        source = MagicMock(spec=DocSource)
        engine = MagicMock(spec=SearchEngine)
        nav = NavTree(root=NavNode(title="Docs"))
        ctx = AppContext(source=source, engine=engine, nav=nav)
        assert isinstance(ctx.source, DocSource)
        assert isinstance(ctx.engine, SearchEngine)
        assert isinstance(ctx.nav, NavTree)


class TestRunServer:
    """run_server validates the docs path and delegates to mcp.run()."""

    def test_raises_filenotfound_for_missing_directory(self, tmp_path: Path) -> None:
        """When docs_path does not exist, raise FileNotFoundError."""
        from mcp_agno_docs.server import run_server
        bogus = tmp_path / "does_not_exist"
        with pytest.raises(FileNotFoundError, match="not a directory"):
            run_server(bogus)

    def test_raises_filenotfound_for_file_instead_of_dir(self, tmp_path: Path) -> None:
        """When docs_path is a file not a directory, raise FileNotFoundError."""
        from mcp_agno_docs.server import run_server
        f = tmp_path / "some_file.txt"
        f.write_text("not a dir")
        with pytest.raises(FileNotFoundError, match="not a directory"):
            run_server(f)

    def test_accepts_string_path(self, tmp_path: Path) -> None:
        """run_server accepts str in addition to Path."""
        from mcp_agno_docs.server import run_server
        # Patch mcp.run so we don't actually start a server
        with patch("mcp_agno_docs.server.mcp.run") as mock_run:
            with patch("mcp_agno_docs.server._configure_lifespan"):
                run_server(str(tmp_path))
                mock_run.assert_called_once_with(transport="stdio")

    def test_accepts_path_object(self, tmp_path: Path) -> None:
        """run_server accepts pathlib.Path."""
        from mcp_agno_docs.server import run_server
        with patch("mcp_agno_docs.server.mcp.run") as mock_run:
            with patch("mcp_agno_docs.server._configure_lifespan"):
                run_server(tmp_path)
                mock_run.assert_called_once_with(transport="stdio")

    def test_resolves_relative_path(self, tmp_path: Path) -> None:
        """run_server resolves relative paths via Path.resolve()."""
        from mcp_agno_docs.server import run_server
        with patch("mcp_agno_docs.server.mcp.run"):
            with patch("mcp_agno_docs.server._configure_lifespan"):
                import os
                cwd = os.getcwd()
                try:
                    os.chdir(tmp_path)
                    run_server(".")
                finally:
                    os.chdir(cwd)
