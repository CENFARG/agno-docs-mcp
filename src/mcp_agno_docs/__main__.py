"""Entry-point for ``python -m mcp_agno_docs``.

Parses CLI arguments, resolves the docs path from a positional argument
or the ``AGNO_DOCS_PATH`` environment variable, and starts the server.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from mcp_agno_docs.server import run_server


def main() -> None:
    """Parse CLI args and start the MCP server on stdio."""
    parser = argparse.ArgumentParser(
        prog="mcp-agno-docs",
        description="MCP server for Agno documentation (FastMCP + FTS5).",
    )
    parser.add_argument(
        "docs_path",
        type=Path,
        nargs="?",
        default=Path(os.environ.get("AGNO_DOCS_PATH", "./agno-docs")),
        help="Path to Agno docs directory (default: $AGNO_DOCS_PATH or ./agno-docs)",
    )
    args = parser.parse_args()
    run_server(docs_path=args.docs_path)


if __name__ == "__main__":
    main()
