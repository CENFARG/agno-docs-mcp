"""Parse Mintlify ``docs.json`` into a :class:`NavTree`.

The ``docs.json`` structure is: tabs → groups → pages, where a page
entry can be a plain string (leaf) or a nested ``{group, pages}`` dict
(sub-folder). The parser preserves order and appends ``.mdx`` to page
slugs.
"""

import json
from pathlib import Path
from typing import Any

from mcp_agno_docs.errors import StartupError, ValidationError
from mcp_agno_docs.models import NavNode, NavTree


def load_navigation(docs_json_path: Path) -> NavTree:
    """Load and parse a Mintlify ``docs.json`` into a navigation tree.

    Args:
        docs_json_path: Filesystem path to ``docs.json``.

    Returns:
        Parsed :class:`NavTree` with root node ``"Docs"`` and tab
        children.

    Raises:
        StartupError: If *docs_json_path* does not exist or is not a file.
        ValidationError: If the JSON structure is malformed or missing
            required keys.
    """
    if not docs_json_path.is_file():
        raise StartupError(f"docs.json not found at {docs_json_path}")

    try:
        raw = docs_json_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise StartupError(f"Cannot read docs.json at {docs_json_path}: {exc}") from exc

    try:
        data: dict[str, Any] = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValidationError(f"docs.json is not valid JSON: {exc}") from exc

    navigation = data.get("navigation")
    if not isinstance(navigation, dict):
        raise ValidationError("docs.json missing top-level 'navigation' key")

    tabs_raw = navigation.get("tabs")
    if not isinstance(tabs_raw, list):
        raise ValidationError("docs.json missing 'navigation.tabs' list")

    root_children: list[NavNode] = []
    for tab_entry in tabs_raw:
        if not isinstance(tab_entry, dict):
            raise ValidationError(f"Invalid tab entry in docs.json: {tab_entry}")
        tab_name = tab_entry.get("tab")
        if not isinstance(tab_name, str):
            raise ValidationError(f"Tab entry missing 'tab' name: {tab_entry}")

        tab_node = NavNode(title=tab_name, path=None)
        groups_raw = tab_entry.get("groups", [])

        for group_entry in groups_raw:
            group_node = _parse_group(group_entry)
            tab_node.children.append(group_node)

        root_children.append(tab_node)

    root = NavNode(title="Docs", path=None, children=root_children)
    return NavTree(root=root)


def _parse_pages(raw_pages: list[Any]) -> list[NavNode]:
    """Parse a list of page entries into NavNode children.

    Each entry is either:
    - A ``str`` page slug (e.g. ``"index"``) → leaf node.
    - A ``dict`` with ``"group"`` and ``"pages"`` keys → sub-folder node.
    """
    children: list[NavNode] = []
    for entry in raw_pages:
        if isinstance(entry, str):
            path = f"{entry}.mdx" if not entry.endswith(".mdx") else entry
            children.append(NavNode(title=entry, path=path))
        elif isinstance(entry, dict):
            group_name = entry.get("group")
            if not isinstance(group_name, str):
                raise ValidationError(f"Invalid nested group: {entry}")
            sub_pages = entry.get("pages", [])
            if not isinstance(sub_pages, list):
                raise ValidationError(f"Invalid pages in group '{group_name}': {sub_pages}")
            sub_node = NavNode(title=group_name, path=None)
            sub_node.children = _parse_pages(sub_pages)
            children.append(sub_node)
        else:
            raise ValidationError(f"Invalid page entry in docs.json: {entry!r}")
    return children


def _parse_group(group_entry: Any) -> NavNode:
    """Parse a single group entry into a NavNode.

    A group entry is a dict with ``"group"`` (str) and ``"pages"`` (list).
    """
    if not isinstance(group_entry, dict):
        raise ValidationError(f"Invalid group entry in docs.json: {group_entry!r}")

    group_name = group_entry.get("group")
    if not isinstance(group_name, str):
        raise ValidationError(f"Group entry missing 'group' name: {group_entry}")

    pages_raw = group_entry.get("pages", [])
    if not isinstance(pages_raw, list):
        raise ValidationError(f"Invalid pages in group '{group_name}': {pages_raw}")

    group_node = NavNode(title=group_name, path=None)
    group_node.children = _parse_pages(pages_raw)
    return group_node
