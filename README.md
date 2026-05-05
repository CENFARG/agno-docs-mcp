# agno-docs-mcp

**MCP server exposing Agno framework documentation via FTS5-powered full-text search.**

[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://python.org)
[![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-blue)](./LICENSE)
[![MCP](https://img.shields.io/badge/protocol-MCP-black)](https://modelcontextprotocol.io)

## What is this?

A [Model Context Protocol](https://modelcontextprotocol.io) server that gives LLMs fast, accurate access to the [Agno framework](https://docs.agno.com) documentation. Uses SQLite FTS5 with BM25 ranking for full-text search across 3,800+ documentation pages, with snippet highlighting and navigation tree access.

## Why not the official MCP?

The official Agno MCP at `https://docs.agno.com/mcp` has issues:
- Search returns 404 links
- Content is repetitive (chunked, duplicated sections)
- No access to clean individual pages

This server fixes all of that:
- **FTS5 search** with BM25 ranking — accurate, relevance-sorted results
- **Clean page retrieval** — individual `.mdx` pages with frontmatter
- **Navigation tree** — full `docs.json` structure for hierarchical browsing
- **Examples search** — scoped search across 1,797 code examples

## Quick Start

### Install

```bash
pip install agno-docs-mcp
```

### Run

```bash
mcp-agno-docs /path/to/agno-docs
```

Or via environment variable:

```bash
export AGNO_DOCS_PATH=/path/to/agno-docs
mcp-agno-docs
```

## MCP Client Configuration

Add to your MCP client config:

```json
{
  "mcpServers": {
    "agno-docs": {
      "command": "python",
      "args": ["-m", "mcp_agno_docs", "/path/to/agno-docs"]
    }
  }
}
```

### OpenCode Configuration

Add to `opencode.json`:

```json
{
  "mcp": {
    "agno-docs": {
      "type": "local",
      "command": ["python", "-m", "mcp_agno_docs", "C:\\path\\to\\agno-docs"],
      "enabled": true
    }
  }
}
```

## Tools

| Tool | Description |
|------|-------------|
| `search_docs(query, topic?, limit?)` | Full-text search with BM25 ranking and `<b>` highlighted snippets |
| `get_page(path)` | Retrieve a single documentation page with frontmatter |
| `get_navigation()` | Return the full docs.json navigation tree |
| `search_examples(query, limit?)` | Scoped search across examples/ directory |

## Architecture

```
src/mcp_agno_docs/
├── server.py         # FastMCP app + lifespan (DI wiring)
├── __main__.py       # CLI entry point
├── models.py         # Pydantic v2 schemas
├── errors.py         # Domain exceptions
├── sources/          # DocSource ABC + LocalMDXSource
├── search/           # SearchEngine ABC + FTS5Engine
├── tools/            # MCP tool handlers
└── indexer/          # docs.json navigation parser
```

## Development

```bash
pip install -e ".[dev]"
pytest                     # 116 tests
ruff check                 # lint
mypy src/                  # type check
```

## License

MIT — see [LICENSE](./LICENSE).
