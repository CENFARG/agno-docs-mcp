# Getting Started

This tutorial walks you from zero to running your first MCP query in under 5 minutes.

## Prerequisites

- **Python 3.11** or later
- The [Agno documentation](https://github.com/agno-agi/agno-docs) cloned locally (3,831 `.mdx` files and a `docs.json`)
- An MCP-compatible client (Claude Desktop, OpenCode, Gemini CLI, Cursor, Windsurf)

## Step 1: Install

```bash
pip install agno-docs-mcp
```

Verify the install:

```bash
mcp-agno-docs --version
# 0.1.0
```

## Step 2: Clone the Docs

The server needs a local copy of the Agno documentation:

```bash
git clone https://github.com/agno-agi/agno-docs.git ~/agno-docs
```

The `docs/` directory inside should contain 3,800+ `.mdx` files and a `docs.json` navigation file.

## Step 3: Run the Server

Point it at the docs directory:

```bash
mcp-agno-docs ~/agno-docs/docs
```

Or use an environment variable:

```bash
export AGNO_DOCS_PATH=~/agno-docs/docs
mcp-agno-docs
```

Startup takes ~2 seconds — it indexes all `.mdx` files into an in-memory FTS5 database.

## Step 4: Configure Your MCP Client

### OpenCode / Claude Code

```json
{
  "mcp": {
    "agno-docs": {
      "type": "local",
      "command": ["python", "-m", "mcp_agno_docs", "/path/to/agno-docs/docs"],
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
      "args": ["-m", "mcp_agno_docs", "/path/to/agno-docs/docs"]
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

## Step 5: Run Your First Query

Once connected, try these in your AI coding assistant:

**Search for MCP agents:**
```
Use agno-docs search_docs with query "MCP agent tools"
```

**Fetch a specific page:**
```
Use agno-docs get_page with path "culture/overview.mdx"
```

**Browse the navigation:**
```
Use agno-docs get_navigation
```

## What Happens Under the Hood

```
mcp-agno-docs ~/agno-docs/docs
  │
  ├─ Opens docs.json → builds NavTree (cached in memory)
  ├─ Scans *.mdx files → parses frontmatter + body
  ├─ Feeds content into SQLite FTS5 index (in-memory)
  │     └─ Porter tokenizer: "running" → "run"
  │     └─ BM25 ranking: frequency × inverse document frequency
  │
  └─ Starts MCP stdio server → ready for tool calls
```

## Next Steps

- [Search effectively with topics and limits](how-to/search-docs.md)
- [Read the Tools API reference](reference/tools-api.md)
- [Understand why FTS5 was chosen](explanation/why-fts5.md)

## Troubleshooting

### "AGNO_DOCS_PATH is not set"

You must either pass the path as a CLI argument or set the environment variable. The server does not guess.

### "No .mdx files found in ..."

Verify the path points to the `docs/` directory inside the cloned repo — it should contain `.mdx` files and `docs.json`.

### "Permission denied"

The server reads files, it never writes. Make sure your user has read access to the docs directory.

### MCP Client Can't Connect

- Check the client's MCP config matches Step 4 exactly
- Use absolute paths — the MCP client may have a different working directory
- Restart the client after changing the config
