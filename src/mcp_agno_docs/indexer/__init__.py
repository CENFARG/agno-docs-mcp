"""Documentation indexer and navigation builder.

Parses Mintlify ``docs.json`` into a :class:`NavTree` for the
``get_navigation`` tool.
"""

from mcp_agno_docs.indexer.navigation import load_navigation

__all__ = ["load_navigation"]
