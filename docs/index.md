# agno-docs-mcp

**MCP server exposing Agno framework documentation via FTS5-powered full-text search.**

[![CI](https://github.com/CENFARG/agno-docs-mcp/actions/workflows/test.yml/badge.svg)](https://github.com/CENFARG/agno-docs-mcp/actions/workflows/test.yml)
[![Coverage](https://img.shields.io/badge/coverage-90%25-brightgreen)](https://github.com/CENFARG/agno-docs-mcp)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://python.org)
[![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-blue)](https://github.com/CENFARG/agno-docs-mcp/blob/main/LICENSE)

## What is agno-docs-mcp?

A [Model Context Protocol](https://modelcontextprotocol.io) server that gives LLMs fast, accurate access to the [Agno framework](https://docs.agno.com) documentation. Uses SQLite FTS5 with **BM25 ranking** for full-text search across 3,800+ documentation pages.

Choose your path:

- **New here?** → Start with [Getting Started](getting-started.md) — install it in 2 minutes
- **Want to use a specific tool?** → Jump to the [How-To Guides](how-to/search-docs.md)
- **Need the API reference?** → Check the [Tools API](reference/tools-api.md)
- **Curious about design?** → Read [Why FTS5?](explanation/why-fts5.md)

## Quick Start

```bash
pip install agno-docs-mcp
mcp-agno-docs /path/to/agno-docs
```

## Features

- **Full-text search** with BM25 ranking and Porter stemming
- **Snippet highlighting** — `<b>` markup around matched terms
- **Page retrieval** — fetch individual `.mdx` pages with frontmatter
- **Navigation tree** — browse the entire docs hierarchy
- **Code-only search** — scoped to `examples/` directory (1,797 pages)
- **Hexagonal architecture** — swap engines and sources without touching tools
- **Zero config** — in-memory SQLite, no setup required

## Tools

| Tool | What it does |
|------|-------------|
| [`search_docs`](reference/tools-api.md#search_docs) | Full-text search with BM25 ranking and topic filter |
| [`get_page`](reference/tools-api.md#get_page) | Retrieve a single `.mdx` page with metadata |
| [`get_navigation`](reference/tools-api.md#get_navigation) | Full hierarchical navigation tree |
| [`search_examples`](reference/tools-api.md#search_examples) | Scoped search across `examples/` directory |

## Project Links

- [GitHub Repository](https://github.com/CENFARG/agno-docs-mcp)
- [Agno Documentation](https://docs.agno.com)
- [Model Context Protocol](https://modelcontextprotocol.io)
- [SQLite FTS5](https://www.sqlite.org/fts5.html)
