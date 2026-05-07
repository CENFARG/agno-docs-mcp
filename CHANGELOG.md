# Changelog

All notable changes to agno-docs-mcp are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] — 2026-05-07

### Added
- Core MCP server with FastMCP stdio transport
- `search_docs` tool: FTS5 full-text search with BM25 ranking and snippet highlighting
- `get_page` tool: individual `.mdx` page retrieval with YAML frontmatter
- `get_navigation` tool: hierarchical navigation tree from `docs.json`
- `search_examples` tool: scoped search across `examples/` directory
- `DocSource` abstract port with `LocalMDXSource` adapter
- `SearchEngine` abstract port with `FTS5Engine` adapter (porter tokenizer, BM25)
- Pydantic v2 schemas for all tool I/O (12 models)
- Domain exception hierarchy (5 classes)
- Hexagonal architecture with dependency injection via `AppContext`
- Async wrappers for all blocking I/O (`asyncio.to_thread`)
- Full test suite: 158 tests (unit + integration + E2E), 90% coverage
- MCP tool wrapper tests with mocked FastMCP context
- GitHub Actions CI pipeline (lint + mypy + pytest on Python 3.11, 3.12)
- Apache 2.0 license
- PEP 8, PEP 257, PEP 484 compliance enforced via Ruff and Mypy strict mode
