"""Unit tests for mcp_agno_docs.utils — shared path normalisation.

Verifies the unified normalise_path() correctly handles normalisation,
path traversal rejection, backslash conversion, and edge cases.
"""

import pytest

from mcp_agno_docs.errors import ValidationError
from mcp_agno_docs.utils import normalise_path


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
