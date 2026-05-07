"""Shared test configuration and fixtures for agno-docs-mcp."""

from pathlib import Path

# ---- Fixture path helpers ----

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
FIXTURES_DOCS_DIR = FIXTURES_DIR / "docs"
FIXTURES_DOCS_JSON = FIXTURES_DOCS_DIR / "docs.json"
