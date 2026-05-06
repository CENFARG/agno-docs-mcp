"""Additional integration tests for navigation error paths."""
import json
from pathlib import Path

import pytest

from mcp_agno_docs.errors import StartupError, ValidationError
from mcp_agno_docs.indexer.navigation import load_navigation, _parse_group, _parse_pages
from mcp_agno_docs.models import NavNode, NavTree


class TestLoadNavigationEdgeCases:
    """Edge cases and error paths for load_navigation."""

    def test_missing_navigation_tabs(self, tmp_path: Path) -> None:
        """When navigation.tabs is not a list, raise ValidationError."""
        p = tmp_path / "docs.json"
        p.write_text(json.dumps({"navigation": {"tabs": "not_a_list"}}))
        with pytest.raises(ValidationError, match="tabs"):
            load_navigation(p)

    def test_invalid_tab_entry_not_dict(self, tmp_path: Path) -> None:
        """Tab entries that are not dicts raise ValidationError."""
        p = tmp_path / "docs.json"
        p.write_text(json.dumps({"navigation": {"tabs": ["string_tab", 42]}}))
        with pytest.raises(ValidationError, match="Invalid tab entry"):
            load_navigation(p)

    def test_tab_missing_name(self, tmp_path: Path) -> None:
        """Tab entry without 'tab' key raises ValidationError."""
        p = tmp_path / "docs.json"
        p.write_text(json.dumps({"navigation": {"tabs": [{"not_tab": "val"}]}}))
        with pytest.raises(ValidationError, match="missing 'tab'"):
            load_navigation(p)

    def test_unreadable_file_raises_startup_error(self, tmp_path: Path) -> None:
        """When docs.json exists but cannot be read, raise StartupError."""
        p = tmp_path / "docs.json"
        p.write_text("{}")
        # Make it unreadable by removing read permission
        import os
        try:
            os.chmod(p, 0o000)
            if os.name == "nt":
                import stat
                os.chmod(p, stat.S_IREAD)  # nope, skip on Windows
                pytest.skip("Cannot reliably test unreadable file on Windows")
            with pytest.raises(StartupError, match="Cannot read"):
                load_navigation(p)
        finally:
            os.chmod(p, 0o644)

    def test_empty_groups_list(self, tmp_path: Path) -> None:
        """Tab with empty groups list returns tab with no children."""
        p = tmp_path / "docs.json"
        p.write_text(json.dumps({"navigation": {"tabs": [
            {"tab": "Solo", "groups": []}
        ]}}))
        result = load_navigation(p)
        assert len(result.root.children) == 1
        assert result.root.children[0].children == []


class TestParseGroupEdgeCases:
    """Error paths for _parse_group."""

    def test_group_entry_not_dict(self) -> None:
        """Non-dict group entry raises ValidationError."""
        with pytest.raises(ValidationError, match="Invalid group entry"):
            _parse_group(["not", "a", "dict"])

    def test_group_missing_name(self) -> None:
        """Group dict without 'group' key raises ValidationError."""
        with pytest.raises(ValidationError, match="missing 'group'"):
            _parse_group({"not_group": "val"})

    def test_invalid_pages_list(self) -> None:
        """Group with pages that is not a list raises ValidationError."""
        with pytest.raises(ValidationError, match="Invalid pages"):
            _parse_group({"group": "Test", "pages": "not_a_list"})


class TestParsePagesEdgeCases:
    """Error paths for _parse_pages."""

    def test_invalid_page_entry_type(self) -> None:
        """A page entry that is neither str nor dict raises ValidationError."""
        with pytest.raises(ValidationError, match="Invalid page entry"):
            _parse_pages(["valid.md", 42, 3.14])

    def test_nested_group_missing_name(self) -> None:
        """Nested group dict without 'group' key raises ValidationError."""
        with pytest.raises(ValidationError, match="nested group"):
            _parse_pages([{"not_group": "x", "pages": []}])

    def test_nested_group_invalid_pages(self) -> None:
        """Nested group with non-list pages raises ValidationError."""
        with pytest.raises(ValidationError, match="Invalid pages"):
            _parse_pages([{"group": "Sub", "pages": "bad"}])


class TestLoadNavigationMissing:
    """Missing file and missing navigation key edge cases."""

    def test_missing_navigation_key(self, tmp_path: Path) -> None:
        """When the JSON has no 'navigation' key, raise ValidationError."""
        p = tmp_path / "docs.json"
        p.write_text('{"other_key": "value"}')
        with pytest.raises(ValidationError, match="missing.*navigation"):
            load_navigation(p)
