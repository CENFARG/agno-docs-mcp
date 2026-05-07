# Configuration Reference

How to configure the agno-docs-mcp server.

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AGNO_DOCS_PATH` | See below | `None` | Path to the Agno documentation root (contains `.mdx` files and `docs.json`) |

### Path Specification

The docs path can be set in two ways, with CLI taking precedence:

1. **CLI argument** (recommended):
   ```bash
   mcp-agno-docs /home/user/agno-docs/docs
   ```

2. **Environment variable**:
   ```bash
   export AGNO_DOCS_PATH=/home/user/agno-docs/docs
   mcp-agno-docs
   ```

If both are set, the CLI argument wins:

```
mcp-agno-docs /custom/path  # Uses /custom/path, ignores AGNO_DOCS_PATH
```

If neither is set, the server exits with an error:

```
Error: AGNO_DOCS_PATH is not set.
Usage: mcp-agno-docs [DOCS_PATH]
```

## CLI Reference

```
mcp-agno-docs [OPTIONS] [DOCS_PATH]
```

| Argument | Description |
|----------|-------------|
| `DOCS_PATH` | Path to Agno docs root (optional if `AGNO_DOCS_PATH` is set) |

| Option | Description |
|--------|-------------|
| `--version` | Print version and exit |
| `--help` | Print help message and exit |

## MCP Transport

The server uses **stdio transport** exclusively in v0.1.0:

- Communicates via JSON-RPC over stdin/stdout
- No network ports, no HTTP server
- No authentication required (local process only)
- Compatible with all MCP clients that support stdio

Future versions (v0.4.0 roadmap) will add SSE transport for remote access.

## Resource Limits

| Resource | Limit | Reason |
|----------|-------|--------|
| Search results | 50 max per call | Prevents abuse of MCP context window |
| Page size | No limit | Real pages can be up to ~50KB |
| FTS5 index | In-memory only | Restarts fresh each time; ~2s to rebuild |
| Concurrent clients | 1 | stdio transport is inherently single-client |

## Dependencies

### Runtime

| Package | Version | Purpose |
|---------|---------|---------|
| `mcp` | ≥1.0, <2.0 | MCP protocol implementation |
| `pydantic` | ≥2.0 | Data validation and serialization |
| `pyyaml` | ≥6 | YAML frontmatter parsing |

### Optional (dev)

| Package | Version | Purpose |
|---------|---------|---------|
| `pytest` | ≥8 | Test runner |
| `pytest-asyncio` | — | Async test support |
| `pytest-cov` | — | Coverage reporting |
| `ruff` | — | Linting and formatting |
| `mypy` | — | Static type checking |
| `mkdocs-material` | — | Documentation site generation |
| `types-PyYAML` | — | Type stubs for PyYAML |
