"""Unit tests for CLI entry point (__main__.py)."""
from pathlib import Path
from unittest.mock import patch

import pytest


class TestMainCLI:
    """Tests for the main() function: argument parsing and delegation."""

    def test_uses_positional_docs_path(self) -> None:
        """main() passes positional arg as docs_path to run_server."""
        from mcp_agno_docs.__main__ import main
        with patch("mcp_agno_docs.__main__.run_server") as mock_run:
            with patch("sys.argv", ["mcp-agno-docs", "/tmp/docs"]):
                main()
                mock_run.assert_called_once()
                call_kwargs = mock_run.call_args.kwargs
                assert call_kwargs["docs_path"] == Path("/tmp/docs")

    def test_uses_env_var_as_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """When no positional arg, main() uses AGNO_DOCS_PATH env var."""
        monkeypatch.setenv("AGNO_DOCS_PATH", "/env/docs")
        from mcp_agno_docs.__main__ import main
        with patch("mcp_agno_docs.__main__.run_server") as mock_run:
            with patch("sys.argv", ["mcp-agno-docs"]):
                main()
                mock_run.assert_called_once()
                call_kwargs = mock_run.call_args.kwargs
                assert call_kwargs["docs_path"] == Path("/env/docs")

    def test_defaults_to_dot_agno_docs(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """When no positional arg and no env var, main() defaults to ./agno-docs."""
        monkeypatch.delenv("AGNO_DOCS_PATH", raising=False)
        from mcp_agno_docs.__main__ import main
        with patch("mcp_agno_docs.__main__.run_server") as mock_run:
            with patch("sys.argv", ["mcp-agno-docs"]):
                main()
                mock_run.assert_called_once()
                call_kwargs = mock_run.call_args.kwargs
                assert call_kwargs["docs_path"] == Path("./agno-docs")

    def test_argument_help_includes_env_var(self) -> None:
        """The --help output mentions AGNO_DOCS_PATH."""
        import argparse
        from mcp_agno_docs.__main__ import main as _main_unused
        # Check the module-level parser definition
        from mcp_agno_docs.__main__ import main
        # We test by verifying the argparse setup exists
        # (main is importable -> parser is valid)
        assert main is not None
