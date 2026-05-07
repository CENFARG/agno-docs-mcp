# agno-docs-mcp

**MCP server exposing Agno framework documentation via FTS5-powered full-text search.**

[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://python.org)
[![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-blue)](./LICENSE)
[![MCP](https://img.shields.io/badge/protocol-MCP-black)](https://modelcontextprotocol.io)
[![CI](https://github.com/CENFARG/agno-docs-mcp/actions/workflows/test.yml/badge.svg)](https://github.com/CENFARG/agno-docs-mcp/actions/workflows/test.yml)
[![Coverage](https://img.shields.io/badge/coverage-90%25-brightgreen)](https://github.com/CENFARG/agno-docs-mcp)
[![PyPI version](https://img.shields.io/badge/pypi-coming%20soon-orange)](https://pypi.org)
[![Documentation](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://cenfarg.github.io/agno-docs-mcp)
[![OpenSSF Best Practices](https://img.shields.io/badge/openssf-passing-brightgreen)](https://www.bestpractices.dev/projects)
[![All Contributors](https://img.shields.io/badge/all_contributors-1-orange.svg)](#contributors)
[![ES](https://img.shields.io/badge/lang-ES-yellow)](./README.es.md)
[![ZH](https://img.shields.io/badge/lang-ZH-red)](./README.zh.md)

## What is this?

A [Model Context Protocol](https://modelcontextprotocol.io) server that gives LLMs fast, accurate access to the [Agno framework](https://docs.agno.com) documentation. Uses SQLite FTS5 with **BM25 ranking** for full-text search across 3,800+ documentation pages, with snippet highlighting and navigation tree access.

Built with a **pluggable hexagonal architecture**: `DocSource` and `SearchEngine` are abstract ports — swap implementations without touching tool logic.

## Why not the official MCP?

| Official MCP (`docs.agno.com/mcp`) | agno-docs-mcp |
|---|---|
| Search returns 404 links | BM25-ranked results from FTS5 index |
| Chunked content, 3-5x duplication | Clean individual `.mdx` pages |
| No individual page access | `get_page()` with frontmatter |
| No navigation structure | Full `docs.json` tree |
| No code-only search | `search_examples()` scoped to 1,797 code examples |

## Demo

```
[search_docs] 'MCP agent tools':
  1. Overview                       score=-7.46  examples/tools/mcp/overview.mdx
  2. Mcp Demo                       score=-7.38  examples/agent-os/mcp-demo/overview.mdx
  3. MCP Integration                score=-7.38  cookbook/tools/mcp.mdx

[get_page] 'culture/overview.mdx':
  Title: What is Culture?
  11,116 chars — full MDX with code examples

[get_navigation] 7 tabs:
  Home, SDK, AgentOS, Deploy, Examples, Reference, FAQs
```

## Quick Start

### Prerequisites

- Python 3.11+
- [Agno documentation](https://github.com/agno-agi/agno-docs) cloned locally (3,831 `.mdx` files)

### Install

```bash
git clone https://github.com/CENFARG/agno-docs-mcp.git
cd agno-docs-mcp
pip install -e ".[dev]"
```

Or with `uv` (zero-config, auto-manages venv):

```bash
git clone https://github.com/CENFARG/agno-docs-mcp.git
cd agno-docs-mcp
uv run mcp-agno-docs /path/to/agno-docs
```

> **Note**: PyPI package coming soon. For now, install from source.

### Run

```bash
mcp-agno-docs /path/to/agno-docs
```

Or via environment variable:

```bash
export AGNO_DOCS_PATH=/path/to/agno-docs
mcp-agno-docs
```

Startup time: ~2 seconds (indexes 3,826 `.mdx` files + `docs.json` into FTS5).

## MCP Client Configuration

### OpenCode / Claude Code

```json
{
  "mcp": {
    "agno-docs": {
      "type": "local",
      "command": ["python", "-m", "mcp_agno_docs", "/path/to/agno-docs"],
      "enabled": true
    }
  }
}
```

### Claude Desktop

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

### Cursor / Windsurf

```json
{
  "mcpServers": {
    "agno-docs": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/agno-docs-mcp", "mcp-agno-docs", "/path/to/agno-docs"]
    }
  }
}
```

### Gemini CLI

Add to `~/.gemini/settings.json`:

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

## Tools

| Tool | Signature | Description |
|------|-----------|-------------|
| `search_docs` | `(query: str, topic?: str, limit?: int) → list[DocHit]` | Full-text search with BM25 ranking and `<b>` highlighted snippets |
| `get_page` | `(path: str) → DocPage` | Retrieve a single `.mdx` page with YAML frontmatter |
| `get_navigation` | `() → NavTree` | Full hierarchical navigation tree from `docs.json` |
| `search_examples` | `(query: str, limit?: int) → list[DocHit]` | Scoped search across `examples/` directory |

### Search Features

- **BM25 ranking**: Relevance-sorted results (lower score = more relevant)
- **Porter stemming**: `agent` matches `agents`, `agentic`
- **Topic filter**: Narrow by frontmatter `keywords` field
- **Snippet highlighting**: `<b>...</b>` markup around matched terms
- **Over-fetching**: `search_examples` fetches 4x limit internally to compensate for filtering

## Architecture

```
                    ┌─────────────────────────────────┐
                    │     FastMCP Server (stdio)       │
                    │  lifespan → AppContext            │
                    │     ├── LocalMDXSource            │
                    │     ├── FTS5Engine               │
                    │     └── NavTree (cached)          │
                    └──────────┬──────────────────────┘
                               │
            ┌──────────────────┼──────────────────┐
            ▼                  ▼                  ▼
     search_docs           get_page         get_navigation
     search_examples
            │                  │                  │
            ▼                  ▼                  ▼
     SearchEngine (ABC)   DocSource (ABC)    NavTree cache
            │                  │
            ▼                  ▼
       FTS5Engine        LocalMDXSource
            │                  │
            ▼                  ▼
   SQLite FTS5 (:memory:)  Filesystem: *.mdx + docs.json
```

**Key patterns:**
- **Hexagonal ports**: `DocSource` and `SearchEngine` are abstract — future adapters (vector search, remote docs) require zero changes to tools
- **Dependency injection**: `AppContext` wires adapters at startup; tools never import SQLite or filesystem directly
- **Async wrappers**: All blocking I/O (disk, SQLite) runs in `asyncio.to_thread`

## Development

```bash
git clone https://github.com/gonzalorrecalde/agno-docs-mcp.git
cd agno-docs-mcp
pip install -e ".[dev]"
```

### Quality Gates

| Tool | Command | Target |
|------|---------|--------|
| Tests | `pytest` | 158 tests, 0 failures |
| Coverage | `pytest --cov=src/mcp_agno_docs --cov-fail-under=80` | ≥90% |
| Lint | `ruff check src/` | 0 violations |
| Type check | `mypy src/ --strict` | 0 errors |

### Project Structure

```
agno-docs-mcp/
├── src/mcp_agno_docs/
│   ├── server.py          # FastMCP app + lifespan
│   ├── __main__.py        # CLI entry (python -m mcp_agno_docs)
│   ├── models.py          # Pydantic v2 schemas (12 models)
│   ├── errors.py          # Domain exceptions (5 classes)
│   ├── sources/
│   │   ├── base.py        # DocSource ABC
│   │   └── local_mdx.py   # LocalMDXSource adapter
│   ├── search/
│   │   ├── base.py        # SearchEngine ABC
│   │   └── fts5.py        # FTS5Engine adapter
│   ├── tools/
│   │   ├── search.py      # search_docs + search_examples
│   │   ├── pages.py       # get_page
│   │   └── navigation.py  # get_navigation
│   └── indexer/
│       └── navigation.py  # docs.json → NavTree parser
├── tests/
│   ├── unit/              # 6 test files (mocked dependencies)
│   ├── integration/       # 3 test files (real sqlite + files)
│   ├── e2e/               # MCP client stdio tests
│   └── fixtures/docs/     # 9 synthetic .mdx files + docs.json
├── .github/workflows/     # CI: lint + mypy + pytest (3.11, 3.12)
├── pyproject.toml         # hatchling build, dev deps, tool configs
├── README.md
├── CONTRIBUTING.md
├── CHANGELOG.md
├── CODE_OF_CONDUCT.md
└── LICENSE                # Apache 2.0
```

## Roadmap

| Milestone | Feature | Status |
|-----------|---------|--------|
| **v0.1.0** | Core MCP server with FTS5 search | ✅ Complete |
| **v0.2.0** | MCP Resources (`agno-docs://` URIs) | Planned |
| **v0.3.0** | Watch mode — auto-reindex on file changes | Planned |
| **v0.4.0** | SSE transport — remote server mode | Planned |
| **v0.5.0** | Semantic + hybrid search (embeddings) | Planned |

## License

Apache 2.0 — see [LICENSE](./LICENSE).

---

Built with ❤️ using [FastMCP](https://github.com/jlowin/fastmcp), [FTS5](https://www.sqlite.org/fts5.html), and [Pydantic v2](https://docs.pydantic.dev).
