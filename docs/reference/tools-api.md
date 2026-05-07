# Tools API Reference

Complete API reference for the four MCP tools exposed by agno-docs-mcp.

---

## `search_docs`

Full-text search across all Agno documentation pages with BM25 ranking.

### Signature

```
search_docs(query: str, topic?: str, limit?: int) → list[DocHit]
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | `str` | Yes | — | Search query. Supports multi-word queries. |
| `topic` | `str` | No | `None` | Filter results by frontmatter keyword. Case-sensitive, exact match. |
| `limit` | `int` | No | `10` | Maximum results to return. Range: 1–50. |

### Returns

`list[DocHit]` — each hit contains:

| Field | Type | Description |
|-------|------|-------------|
| `path` | `str` | Relative page path (e.g., `"cookbook/tools/mcp.mdx"`) |
| `title` | `str` | Page title from YAML frontmatter |
| `score` | `float` | BM25 relevance score. **Lower is better** (negative values). |
| `snippet` | `str` | Text excerpt with `<b>...</b>` around matched terms. Max 64 tokens. |

### Examples

```python
# Basic search
results = search_docs("MCP agent tools")

# With topic filter
results = search_docs("streaming", topic="agents", limit=5)
```

### MCP JSON-RPC

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "search_docs",
    "arguments": {
      "query": "MCP agent tools",
      "limit": 5
    }
  }
}
```

### Errors

| Condition | Error |
|-----------|-------|
| Empty query | `InvalidArgument("query must not be empty")` |
| Limit > 50 | `InvalidArgument("limit must be between 1 and 50")` |

### Implementation Notes

- Uses SQLite FTS5 `MATCH` with `ORDER BY rank`
- BM25 ranking is custom-implemented (SQLite FTS5 defaults to `bm25()`; we use `rank`)
- Porter tokenizer normalizes terms before matching
- Search is **case-insensitive** for content; **case-sensitive** for topic filter

---

## `get_page`

Retrieve the full content and metadata of a single documentation page.

### Signature

```
get_page(path: str) → DocPage
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `path` | `str` | Yes | — | Relative path from docs root (e.g., `"culture/overview.mdx"`) |

### Returns

`DocPage` — full page content:

| Field | Type | Description |
|-------|------|-------------|
| `path` | `str` | Relative page path |
| `title` | `str` | Page title from YAML frontmatter |
| `description` | `str` | Description from frontmatter (empty if missing) |
| `keywords` | `list[str]` | Keywords from frontmatter (empty if missing) |
| `content` | `str` | Full markdown/MDX body content |
| `content_length` | `int` | Character count of content |

### Examples

```python
page = get_page("cookbook/tools/mcp.mdx")
print(page.title)       # "MCP Integration"
print(page.content_length)  # 4523
```

### MCP JSON-RPC

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "get_page",
    "arguments": {
      "path": "culture/overview.mdx"
    }
  }
}
```

### Errors

| Condition | Error |
|-----------|-------|
| Page not found | `PageNotFound("culture/overview.mdx")` |
| Path is absolute | `InvalidArgument("path must be relative")` |

### Implementation Notes

- Content is read from disk on each call (no page-level caching)
- YAML frontmatter parsing uses `pyyaml`
- Paths are resolved against the configured `AGNO_DOCS_PATH` root
- Returns even if frontmatter is missing (fields default to empty)

---

## `get_navigation`

Return the full hierarchical navigation tree from `docs.json`.

### Signature

```
get_navigation() → NavTree
```

### Parameters

None.

### Returns

`NavTree` — hierarchical structure:

| Field | Type | Description |
|-------|------|-------------|
| `tabs` | `list[NavTab]` | Top-level navigation tabs |
| `tabs[].label` | `str` | Tab display name |
| `tabs[].groups` | `list[NavGroup]` | Groups within the tab |
| `groups[].label` | `str` | Group display name |
| `groups[].pages` | `list[NavPage]` | Pages within the group |
| `pages[].path` | `str` | Relative page path |
| `pages[].label` | `str` | Page display title |

### Examples

```python
nav = get_navigation()
for tab in nav.tabs:
    print(f"{tab.label}: {sum(len(g.pages) for g in tab.groups)} pages")
```

### MCP JSON-RPC

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "get_navigation",
    "arguments": {}
  }
}
```

### Errors

| Condition | Error |
|-----------|-------|
| `docs.json` missing | `StartupError("docs.json not found in ...")` |
| Invalid JSON | `StartupError("Failed to parse docs.json")` |

### Implementation Notes

- Tree is parsed at startup and cached in `AppContext.nav_tree`
- Subsequent calls return the cached tree — no disk I/O
- `docs.json` is the Agno documentation's official navigation file
- If structure changes, restart the server to re-parse

---

## `search_examples`

Scoped search across the `examples/` directory only.

### Signature

```
search_examples(query: str, limit?: int) → list[DocHit]
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | `str` | Yes | — | Search query |
| `limit` | `int` | No | `10` | Maximum results. Range: 1–50. |

### Returns

`list[DocHit]` — same structure as `search_docs`, but only from `examples/` pages.

### Implementation Notes

- Internally fetches `limit * 4` results from FTS5
- Post-filters by `path LIKE 'examples/%'` to keep only example pages
- Over-fetching compensates for the scope restriction
- If fewer than `limit` results exist after filtering, returns all found

### MCP JSON-RPC

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "search_examples",
    "arguments": {
      "query": "streaming agent",
      "limit": 5
    }
  }
}
```
