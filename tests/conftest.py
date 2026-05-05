"""Shared test configuration and fixtures for agno-docs-mcp."""

import sys
from pathlib import Path

# Ensure the src/ directory is on sys.path so tests can import mcp_agno_docs.
_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

# ---- Fixture path helpers ----

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
FIXTURES_DOCS_DIR = FIXTURES_DIR / "docs"
FIXTURES_DOCS_JSON = FIXTURES_DOCS_DIR / "docs.json"
