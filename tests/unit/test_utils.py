"""Unit tests for mcp_agno_docs.utils — shared path normalisation and tool error helpers.

Verifies the unified normalise_path() correctly handles normalisation,
path traversal rejection, backslash conversion, and edge cases.
Also verifies _tool_error and _not_found produce correct MCP exception types.
"""

import pytest

from mcp_agno_docs.errors import ValidationError
from mcp_agno_docs.utils import _not_found, _tool_error, normalise_path


class TestNormalisePath:
    """Unit tests for the unified normalise_path() from utils.py."""

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
            (r"api\sub\page.mdx", "api/sub/page.mdx"),  # multiple backslashes
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

    def test_triple_dot_not_rejected(self) -> None:
        """'...' (three dots) is NOT '..' and should pass through."""
        result = normalise_path("api/.../page.mdx")
        assert result == "api/.../page.mdx"

    def test_leading_dot_slash_removed(self) -> None:
        """Leading './' is collapsed."""
        result = normalise_path("./readme.mdx")
        assert result == "readme.mdx"

    def test_consecutive_slashes_collapsed(self) -> None:
        """Multiple consecutive slashes are collapsed."""
        result = normalise_path("a///b")
        assert result == "a/b"


class TestToolErrorHelpers:
    """ToolError and ResourceError helpers produce correct MCP exception types."""

    def test_tool_error_returns_tool_error(self) -> None:
        """_tool_error returns a ToolError with the given message."""
        exc = _tool_error("bad input")
        from mcp.server.fastmcp.exceptions import ToolError

        assert isinstance(exc, ToolError)
        assert str(exc) == "bad input"

    def test_not_found_returns_resource_error(self) -> None:
        """_not_found returns a ResourceError with the given message."""
        exc = _not_found("page missing")
        from mcp.server.fastmcp.exceptions import ResourceError

        assert isinstance(exc, ResourceError)
        assert str(exc) == "page missing"
