"""Tests for the mcp_agno_docs package exports."""

import mcp_agno_docs


class TestPackageExports:
    """Verify the package exposes expected attributes."""

    def test_version_is_defined(self) -> None:
        """The package MUST expose a __version__ string matching semver."""
        assert hasattr(mcp_agno_docs, "__version__"), "mcp_agno_docs.__version__ is missing"
        assert isinstance(mcp_agno_docs.__version__, str), "__version__ must be a str"
        # Should be a valid version-like string (at minimum contains a dot).
        assert "." in mcp_agno_docs.__version__, f"__version__ looks invalid: {mcp_agno_docs.__version__!r}"

    def test_module_docstring_is_set(self) -> None:
        """The package docstring describes the project."""
        assert mcp_agno_docs.__doc__ is not None, "__doc__ must not be None"
        assert "agno-docs-mcp" in mcp_agno_docs.__doc__, "docstring should mention agno-docs-mcp"
